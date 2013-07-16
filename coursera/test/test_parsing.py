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

    def _assert_parse(self, filename, num_sections, num_lectures,
                      num_resources, num_videos):
        filename = os.path.join(
            os.path.dirname(__file__), "fixtures", "html",
            filename)

        syllabus_page = open(filename).read()

        sections = coursera_dl.parse_syllabus(None, syllabus_page, None)

        # section count
        self.assertEqual(len(sections), num_sections)

        # lecture count
        lectures = [lec for sec in sections for lec in sec[1]]
        self.assertEqual(len(lectures), num_lectures)

        # resource count
        resources = [(res[0], len(res[1]))
                     for lec in lectures for res in iteritems(lec[1])]
        self.assertEqual(sum(r for f, r in resources), num_resources)

        # mp4 count
        self.assertEqual(
            sum(r for f, r in resources if f == "mp4"),
            num_videos)

    def test_parse(self):
        self._assert_parse(
            "regular-syllabus.html",
            num_sections=23,
            num_lectures=102,
            num_resources=502,
            num_videos=102)

    def test_links_to_wikipedia(self):
        self._assert_parse(
            "links-to-wikipedia.html",
            num_sections=5,
            num_lectures=37,
            num_resources=158,
            num_videos=36)

    def test_parse_preview(self):
        self._assert_parse(
            "preview.html",
            num_sections=20,
            num_lectures=106,
            num_resources=106,
            num_videos=106)

    def test_sections_missed(self):
        self._assert_parse(
            "sections-not-to-be-missed.html",
            num_sections=9,
            num_lectures=61,
            num_resources=224,
            num_videos=61)

    def test_sections_missed2(self):
        self._assert_parse(
            "sections-not-to-be-missed-2.html",
            num_sections=20,
            num_lectures=121,
            num_resources=397,
            num_videos=121)

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
                num_sections=counts[0],
                num_lectures=counts[1],
                num_resources=counts[2],
                num_videos=counts[3])

    def test_multiple_resources_with_the_same_format(self):
        self._assert_parse(
            "multiple-resources-with-the-same-format.html",
            num_sections=18,
            num_lectures=97,
            num_resources=478,
            num_videos=97)


if __name__ == "__main__":
    unittest.main()
