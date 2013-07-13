#!/usr/bin/env python
"""
Test syllabus parsing.
"""

import os.path
import unittest

import six

from coursera import cookies

FIREFOX_COOKIES = \
    os.path.join(os.path.dirname(__file__),
                 "fixtures", "cookies", "firefox_cookies.txt")

CHROME_COOKIES = \
    os.path.join(os.path.dirname(__file__),
                 "fixtures", "cookies", "chrome_cookies.txt")

FIREFOX_COOKIES_WITHOUT_COURSERA = \
    os.path.join(os.path.dirname(__file__),
                 "fixtures", "cookies", "firefox_cookies_without_coursera.txt")

FIREFOX_COOKIES_EXPIRED = \
    os.path.join(os.path.dirname(__file__),
                 "fixtures", "cookies", "firefox_cookies_expired.txt")


class MockResponse:
    def raise_for_status(self):
        pass


class MockSession:
    def __init__(self):
        self.called = False

    def get(self, url):
        self.called = True
        return MockResponse()


class CookiesFileTestCase(unittest.TestCase):

    def test_get_cookiejar_from_firefox_cookies(self):
        from six.moves import http_cookiejar as cookielib
        cj = cookies.get_cookie_jar(FIREFOX_COOKIES)
        self.assertTrue(isinstance(cj, cookielib.MozillaCookieJar))

    def test_get_cookiejar_from_chrome_cookies(self):
        from six.moves import http_cookiejar as cookielib
        cj = cookies.get_cookie_jar(CHROME_COOKIES)
        self.assertTrue(isinstance(cj, cookielib.MozillaCookieJar))

    def test_find_cookies_for_class(self):
        import requests
        cj = cookies.find_cookies_for_class(FIREFOX_COOKIES, 'class-001')
        self.assertTrue(isinstance(cj, requests.cookies.RequestsCookieJar))

        self.assertEquals(len(cj), 7)

        domains = cj.list_domains()
        self.assertEquals(len(domains), 2)
        self.assertTrue('www.coursera.org' in domains)
        self.assertTrue('class.coursera.org' in domains)

        paths = cj.list_paths()
        self.assertEquals(len(paths), 2)
        self.assertTrue('/' in paths)
        self.assertTrue('/class-001' in paths)

    def test_did_not_find_cookies_for_class(self):
        import requests
        cj = cookies.find_cookies_for_class(
            FIREFOX_COOKIES_WITHOUT_COURSERA, 'class-001')
        self.assertTrue(isinstance(cj, requests.cookies.RequestsCookieJar))

        self.assertEquals(len(cj), 0)

    def test_did_not_find_expired_cookies_for_class(self):
        import requests
        cj = cookies.find_cookies_for_class(
            FIREFOX_COOKIES_EXPIRED, 'class-001')
        self.assertTrue(isinstance(cj, requests.cookies.RequestsCookieJar))

        self.assertEquals(len(cj), 5)

    def test_we_have_enough_cookies(self):
        cj = cookies.find_cookies_for_class(FIREFOX_COOKIES, 'class-001')

        enough = cookies.do_we_have_enough_cookies(cj, 'class-001')
        self.assertTrue(enough)

    def test_we_dont_have_enough_cookies(self):
        cj = cookies.find_cookies_for_class(
            FIREFOX_COOKIES_WITHOUT_COURSERA, 'class-001')

        enough = cookies.do_we_have_enough_cookies(cj, 'class-001')
        self.assertFalse(enough)

    def test_make_cookie_values(self):
        cj = cookies.find_cookies_for_class(FIREFOX_COOKIES, 'class-001')

        values = 'csrf_token=csrfclass001; session=sessionclass1'
        cookie_values = cookies.make_cookie_values(cj, 'class-001')
        self.assertEquals(cookie_values, values)
