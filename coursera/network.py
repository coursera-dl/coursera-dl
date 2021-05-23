"""
This module contains utility functions that operate on the network, download
some data and so on.
"""

import json
import logging

import requests


def get_reply(session, url, post=False, data=None, headers=None, quiet=False):
    """
    Download an HTML page using the requests session. Low-level function
    that allows for flexible request configuration.

    @param session: Requests session.
    @type session: requests.Session

    @param url: URL pattern with optional keywords to format.
    @type url: str

    @param post: Flag that indicates whether POST request should be sent.
    @type post: bool

    @param data: Payload data that is sent with request (in request body).
    @type data: object

    @param headers: Additional headers to send with request.
    @type headers: dict

    @param quiet: Flag that tells whether to print error message when status
        code != 200.
    @type quiet: bool

    @return: Requests response.
    @rtype: requests.Response
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
        if not quiet:
            logging.error("Error %s getting page %s", e, url)
            logging.error("The server replied: %s", reply.text)
        raise

    return reply


def get_page(session,
             url,
             json=False,
             post=False,
             data=None,
             headers=None,
             quiet=False,
             **kwargs):
    """
    Download an HTML page using the requests session.

    @param session: Requests session.
    @type session: requests.Session

    @param url: URL pattern with optional keywords to format.
    @type url: str

    @param post: Flag that indicates whether POST request should be sent.
    @type post: bool

    @param data: Payload data that is sent with request (in request body).
    @type data: object

    @param headers: Additional headers to send with request.
    @type headers: dict

    @return: Response body.
    @rtype: str
    """
    url = url.format(**kwargs)

    if headers == None:
        headers = dict()

    headers.setdefault('User-Agent',  'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36') # Shame on Coursera
    logging.debug("user-agent set")

    reply = get_reply(session, url, post=post, data=data, headers=headers,
                      quiet=quiet)
    return reply.json() if json else reply.text


def get_page_and_url(session, url):
    """
    Download an HTML page using the requests session and return
    the final URL after following redirects.
    """
    reply = get_reply(session, url)
    return reply.text, reply.url


def post_page_and_reply(session, url, data=None, headers=None, **kwargs):
    url = url.format(**kwargs)
    reply = get_reply(session, url, post=True, data=data, headers=headers)
    return reply.text, reply
