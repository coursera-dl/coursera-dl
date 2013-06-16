#!/usr/bin/env python
"""
Test syllabus parsing.
"""

import os
import os.path
import unittest

from coursera import coursera_dl

FIREFOX_COOKIES = \
    os.path.join(os.path.dirname(__file__), "fixtures", "firefox_cookies.txt")

CHROME_COOKIES = \
    os.path.join(os.path.dirname(__file__), "fixtures", "chrome_cookies.txt")

FIREFOX_COOKIES_WITHOUT_COURSERA = \
    os.path.join(os.path.dirname(__file__), "fixtures", "firefox_cookies_without_coursera.txt")


class CookiesFileTestCase(unittest.TestCase):

	def test_get_cookiejar_from_firefox_cookies(self):
		from cookielib import MozillaCookieJar
		cj = coursera_dl.get_cookie_jar(FIREFOX_COOKIES)
		self.assertTrue(isinstance(cj, MozillaCookieJar))


	def test_get_cookiejar_from_chrome_cookies(self):
		from cookielib import MozillaCookieJar
		cj = coursera_dl.get_cookie_jar(CHROME_COOKIES)
		self.assertTrue(isinstance(cj, MozillaCookieJar))
