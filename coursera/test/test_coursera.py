#!/usr/bin/env python
"""
Test functionality of coursera module.
"""

import os
import os.path
import unittest

from coursera import coursera_dl

TEST_SYLLABUS_FILE = \
    os.path.join(os.path.dirname(__file__), "fixtures", "regular-syllabus.html")

TEST_PREVIEW_FILE = \
    os.path.join(os.path.dirname(__file__), "fixtures","preview.html")

TEST_LINKS_TO_WIKIPEDIA = \
    os.path.join(os.path.dirname(__file__), "fixtures","links-to-wikipedia.html")

TEST_SECTIONS_NOT_TO_MISS = \
    os.path.join(os.path.dirname(__file__), "fixtures","sections-not-to-be-missed.html")


class TestSyllabusParsing(unittest.TestCase):

    def test_parse(self):
        self.syllabus_page = open(TEST_SYLLABUS_FILE).read()

        sections = coursera_dl.parse_syllabus(self.syllabus_page, None)

        # section count
        self.assertEqual(len(sections), 23)

        # lecture count
        lectures = [lec for sec in sections for lec in sec[1]]
        self.assertEqual(len(lectures), 102)

        # resource count
        resources = [res for lec in lectures for res in lec[1].items()]
        self.assertEqual(len(resources), 502)

        # mp4 count
        mp4s = [res for res in resources if res[0] == "mp4"]
        self.assertEqual(len(mp4s), 102)


    def test_links_to_wikipedia(self):
        self.syllabus_page = open(TEST_LINKS_TO_WIKIPEDIA).read()

        sections = coursera_dl.parse_syllabus(self.syllabus_page, None)

        # section count
        self.assertEqual(len(sections), 5)

        # lecture count
        lectures = [lec for sec in sections for lec in sec[1]]
        self.assertEqual(len(lectures), 37)

        # resource count
        resources = [res for lec in lectures for res in lec[1].items()]
        self.assertEqual(len(resources), 158)

        # mp4 count
        mp4s = [res for res in resources if res[0] == "mp4"]
        self.assertEqual(len(mp4s), 36)


    # Python 2.7 accepts @unittest.skip("Too much bandwidth"), but as we are
    # testing this also on Python 2.6, we simply rename the test method to
    # not begin with `test`.
    def xtest_parse_preview(self):
        self.syllabus_page = open(TEST_PREVIEW_FILE).read()

        sections = coursera_dl.parse_syllabus(self.syllabus_page, None)

        # section count
        self.assertEqual(len(sections), 20)

        # lecture count
        lectures = [lec for sec in sections for lec in sec[1]]
        self.assertEqual(len(lectures), 106)

        # resource count
        resources = [res for lec in lectures for res in lec[1].items()]
        self.assertEqual(len(resources), 106)

        # mp4 count
        mp4s = [res for res in resources if res[0] == "mp4"]
        self.assertEqual(len(mp4s), 106)


    def test_sections_missed(self):
        self.syllabus_page = open(TEST_SECTIONS_NOT_TO_MISS).read()

        sections = coursera_dl.parse_syllabus(self.syllabus_page, None)

        # section count
        self.assertEqual(len(sections), 9)

        # lecture count
        lectures = [lec for sec in sections for lec in sec[1]]
        self.assertEqual(len(lectures), 61)

        # resource count
        resources = [res for lec in lectures for res in lec[1].items()]
        self.assertEqual(len(resources), 224)

        # mp4 count
        mp4s = [res for res in resources if res[0] == "mp4"]
        self.assertEqual(len(mp4s), 61)


if __name__ == "__main__":
    unittest.main()
