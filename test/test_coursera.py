#!/usr/bin/env python
"""
Test functionality of coursera module.
"""

import unittest
import os
import os.path
from collections import defaultdict
from coursera import coursera_dl 

TEST_SYLLABUS_FILE = os.path.join(os.path.dirname(__file__), "2012-syllabus-format.html")


class TestSyllabusParsing(unittest.TestCase):
  
  def setUp(self):
    self.syllabus_page= open(TEST_SYLLABUS_FILE).read()

  def test_parse(self):
    result = coursera_dl.parse_syllabus(self.syllabus_page, None)
    # test sections
    self.assertEqual(len(result), 5)
    # test lectures
    self.assertEqual(sum([len(x[1]) for x in result]), 23)

  
if __name__ == "__main__":
  unittest.main()


