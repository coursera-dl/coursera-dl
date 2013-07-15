#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test functionality of coursera module.
"""

import os.path
import unittest

from six import iteritems

from coursera import coursera_dl


class TestSyllabusParsing(unittest.TestCase):

    def setUp(self):
        """
        As setup, we mock some methods that would, otherwise, create
        repeateadly many web requests.

        More specifically, we mock:

        * the search for hidden videos
        * the actual download of videos
        """

        # Mock coursera_dl.grab_hidden_video_url
        self.__grab_hidden_video_url = coursera_dl.grab_hidden_video_url

        def new_grab_hidden_video_url(session, href):
            """
            Mock function to prevent network requests.
            """
            return None
        coursera_dl.grab_hidden_video_url = new_grab_hidden_video_url

        # Mock coursera_dl.get_video
        self.__get_video = coursera_dl.get_video

        def new_get_video(session, href):
            """
            Mock function to prevent network requests.
            """
            return None
        coursera_dl.get_video = new_get_video

    def tearDown(self):
        """
        We unmock the methods mocked in set up.
        """
        coursera_dl.grab_hidden_video_url = self.__grab_hidden_video_url
        coursera_dl.get_video = self.__get_video

    def _assert_parse(self, filename, sections, lectures, resources, mp4):
        filename = os.path.join(
            os.path.dirname(__file__), "fixtures", "html",
            filename)

        syllabus_page = open(filename).read()

        sections_ = coursera_dl.parse_syllabus(None, syllabus_page, None)

        # section count
        self.assertEqual(len(sections_), sections)

        # lecture count
        lectures_ = [lec for sec in sections_ for lec in sec[1]]
        self.assertEqual(len(lectures_), lectures)

        # resource count
        resources_ = [(res[0], len(res[1]))
                      for lec in lectures_ for res in iteritems(lec[1])]
        self.assertEqual(sum(r for f, r in resources_), resources)

        # mp4 count
        self.assertEqual(
            sum(r for f, r in resources_ if f == "mp4"),
            mp4)

    def test_parse(self):
        self._assert_parse(
            "regular-syllabus.html",
            sections=23,
            lectures=102,
            resources=502,
            mp4=102)

    def test_links_to_wikipedia(self):
        self._assert_parse(
            "links-to-wikipedia.html",
            sections=5,
            lectures=37,
            resources=158,
            mp4=36)

    def test_parse_preview(self):
        self._assert_parse(
            "preview.html",
            sections=20,
            lectures=106,
            resources=106,
            mp4=106)

    def test_sections_missed(self):
        self._assert_parse(
            "sections-not-to-be-missed.html",
            sections=9,
            lectures=61,
            resources=224,
            mp4=61)

    def test_sections_missed2(self):
        self._assert_parse(
            "sections-not-to-be-missed-2.html",
            sections=20,
            lectures=121,
            resources=397,
            mp4=121)

    def test_parse_classes_with_bs4(self):
        classes = {
            'datasci-001': (10, 97, 358, 97),  # issue 134
            'startup-001': (4, 44, 136, 44),   # issue 137
            'wealthofnations-001': (8, 74, 296, 74),  # issue 131
            'malsoftware-001': (3, 18, 56, 16)  # issue 148
        }

        for class_, counts in iteritems(classes):
            filename = "parsing-{0}-with-bs4.html".format(class_)
            self._assert_parse(
                filename,
                sections=counts[0],
                lectures=counts[1],
                resources=counts[2],
                mp4=counts[3])

    def test_multiple_resources_with_the_same_format(self):
        self._assert_parse(
            "multiple-resources-with-the-same-format.html",
            sections=18,
            lectures=97,
            resources=478,
            mp4=97)


if __name__ == "__main__":
    unittest.main()
