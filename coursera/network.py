"""
This module contains utility functions that operate on the network, download
some data and so on.
"""

import json
import logging

import requests


def get_page(session, url, post=False, data=None):
    """
    Download an HTML page using the requests session.
    """

    r = session.post(url, data=data) if post else session.get(url)

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error("Error %s getting page %s", e, url)
        raise

    return r.text


def get_page_and_url(session, url):
    """
    Download an HTML page using the requests session and return
    the final URL after following redirects.
    """

    r = session.get(url)

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error("Error %s getting page %s", e, url)
        raise

    return r.text, r.url


def get_page_json(session, url, **kwargs):
    """
    Download page and parse it as JSON. This is a shorthand for common
    operation.

    @param session: Requests session.
    @type session: requests.Session

    @param url: URL pattern with optional keywords to format.
    @type url: str

    @param kwargs: Arguments to `url` pattern.

    @return: Parsed JSON of the request page.
    @rtype: dict
    """
    url = url.format(**kwargs)
    page = get_page(session, url)
    return json.loads(page)

def post_page_json(session, url, data=None, **kwargs):
    """
    Download page and parse it as JSON. This is a shorthand for common
    operation. Same as `get_page_json` but uses POST.

    @param session: Requests session.
    @type session: requests.Session

    @param url: URL pattern with optional keywords to format.
    @type url: str

    @param kwargs: Arguments to `url` pattern.

    @return: Parsed JSON of the request page.
    @rtype: dict
    """
    url = url.format(**kwargs)
    page = get_page(session, url, post=True, data=data)
    return json.loads(page)
