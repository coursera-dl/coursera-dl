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
    assert isinstance(cj, cookielib.MozillaCookieJar)


def test_get_cookiejar_from_chrome_cookies():
    cj = cookies.get_cookie_jar(CHROME_COOKIES)
    assert isinstance(cj, cookielib.MozillaCookieJar)


def test_find_cookies_for_class():
    cj = cookies.find_cookies_for_class(FIREFOX_COOKIES, 'class-001')
    assert isinstance(cj, requests.cookies.RequestsCookieJar)

    assert len(cj) == 6

    domains = cj.list_domains()
    assert len(domains) == 2
    assert '.coursera.org' in domains
    assert 'class.coursera.org' in domains

    paths = cj.list_paths()
    assert len(paths) == 2
    assert '/' in paths
    assert '/class-001' in paths


def test_did_not_find_cookies_for_class():
    cj = cookies.find_cookies_for_class(
        FIREFOX_COOKIES_WITHOUT_COURSERA, 'class-001')
    assert isinstance(cj, requests.cookies.RequestsCookieJar)

    assert len(cj) == 0


def test_did_not_find_expired_cookies_for_class():
    cj = cookies.find_cookies_for_class(
        FIREFOX_COOKIES_EXPIRED, 'class-001')
    assert isinstance(cj, requests.cookies.RequestsCookieJar)

    assert len(cj) == 2


def test_we_have_enough_cookies():
    cj = cookies.find_cookies_for_class(FIREFOX_COOKIES, 'class-001')

    enough = cookies.do_we_have_enough_cookies(cj, 'class-001')
    assert enough


def test_we_dont_have_enough_cookies():
    cj = cookies.find_cookies_for_class(
        FIREFOX_COOKIES_WITHOUT_COURSERA, 'class-001')

    enough = cookies.do_we_have_enough_cookies(cj, 'class-001')
    assert not enough


def test_make_cookie_values():
    cj = cookies.find_cookies_for_class(FIREFOX_COOKIES, 'class-001')

    values = 'csrf_token=csrfclass001; session=sessionclass1'
    cookie_values = cookies.make_cookie_values(cj, 'class-001')
    assert cookie_values == values
