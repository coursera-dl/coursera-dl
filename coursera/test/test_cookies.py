#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test syllabus parsing.
"""

import os.path
import pytest
import requests
from six.moves import http_cookiejar as cookielib

from coursera import cookies
from .test_utils import assertEquals, assertTrue, assertFalse, assertRaises

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


def test_get_cookiejar_from_firefox_cookies():
    cj = cookies.get_cookie_jar(FIREFOX_COOKIES)
    assertTrue(isinstance(cj, cookielib.MozillaCookieJar))

def test_get_cookiejar_from_chrome_cookies():
    cj = cookies.get_cookie_jar(CHROME_COOKIES)
    assertTrue(isinstance(cj, cookielib.MozillaCookieJar))

def test_find_cookies_for_class():
    cj = cookies.find_cookies_for_class(FIREFOX_COOKIES, 'class-001')
    assertTrue(isinstance(cj, requests.cookies.RequestsCookieJar))

    assertEquals(len(cj), 6)

    domains = cj.list_domains()
    assertEquals(len(domains), 2)
    assertTrue('.coursera.org' in domains)
    assertTrue('class.coursera.org' in domains)

    paths = cj.list_paths()
    assertEquals(len(paths), 2)
    assertTrue('/' in paths)
    assertTrue('/class-001' in paths)

def test_did_not_find_cookies_for_class():
    cj = cookies.find_cookies_for_class(
        FIREFOX_COOKIES_WITHOUT_COURSERA, 'class-001')
    assertTrue(isinstance(cj, requests.cookies.RequestsCookieJar))

    assertEquals(len(cj), 0)

def test_did_not_find_expired_cookies_for_class():
    cj = cookies.find_cookies_for_class(
        FIREFOX_COOKIES_EXPIRED, 'class-001')
    assertTrue(isinstance(cj, requests.cookies.RequestsCookieJar))

    assertEquals(len(cj), 2)

def test_we_have_enough_cookies():
    cj = cookies.find_cookies_for_class(FIREFOX_COOKIES, 'class-001')

    enough = cookies.do_we_have_enough_cookies(cj, 'class-001')
    assertTrue(enough)

def test_we_dont_have_enough_cookies():
    cj = cookies.find_cookies_for_class(
        FIREFOX_COOKIES_WITHOUT_COURSERA, 'class-001')

    enough = cookies.do_we_have_enough_cookies(cj, 'class-001')
    assertFalse(enough)

def test_make_cookie_values():
    cj = cookies.find_cookies_for_class(FIREFOX_COOKIES, 'class-001')

    values = 'csrf_token=csrfclass001; session=sessionclass1'
    cookie_values = cookies.make_cookie_values(cj, 'class-001')
    assertEquals(cookie_values, values)
