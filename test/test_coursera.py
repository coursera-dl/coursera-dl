#!/usr/bin/env python
"""
Test functionality of coursera module.
"""

import os
import os.path
import unittest

from coursera import coursera_dl

TEST_SYLLABUS_FILE = \
    os.path.join(os.path.dirname(__file__), "2013-nlp-syllabus.html")


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


if __name__ == "__main__":
    unittest.main()
