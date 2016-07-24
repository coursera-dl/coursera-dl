"""
This module contains utility functions that operate on the network, download
some data and so on.
"""

import json
import logging

import requests


def get_reply(session, url, post=False, data=None, headers=None):
    """
    Download an HTML page using the requests session. Low-level function
    that allows for flexible request configuration.
    """

    request_headers = {} if headers is None else headers

    request = requests.Request('POST' if post else 'GET',
                               url,
                               data=data,
                               headers=request_headers)
    prepared_request = session.prepare_request(request)

    reply = session.send(prepared_request)

    try:
        reply.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error("Error %s getting page %s", e, url)
        from ipdb import set_trace; set_trace()
        raise

    return reply

def get_page(session, url, post=False, data=None, headers=None):
    reply = get_reply(session, url, post=post, data=data, headers=headers)
    return reply.text


def get_page_and_url(session, url):
    """
    Download an HTML page using the requests session and return
    the final URL after following redirects.
    """

    reply = session.get(url)

    try:
        reply.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error("Error %s getting page %s", e, url)
        raise

    return reply.text, reply.url


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

def post_page_and_reply(session, url, data=None, headers=None, **kwargs):
    url = url.format(**kwargs)
    reply = get_reply(session, url, post=True, data=data, headers=headers)
    return reply.text, reply

def post_page_json(session, url, data=None, headers=None, **kwargs):
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
    page, _reply = post_page_and_reply(
        session, url, data=data, headers=headers, **kwargs)
    return json.loads(page)
