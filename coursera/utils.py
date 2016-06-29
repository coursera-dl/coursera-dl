# -*- coding: utf-8 -*-

"""
This module provides utility functions that are used within the script.
"""

import errno
import os
import random
import re
import string
import sys

import six
from bs4 import BeautifulSoup as BeautifulSoup_

# Force us of bs4 with html5lib
BeautifulSoup = lambda page: BeautifulSoup_(page, 'html5lib')

from .define import COURSERA_URL

from six.moves import html_parser
from six import iteritems

#  six.moves doesn’t support urlparse
if six.PY3:  # pragma: no cover
    from urllib.parse import urlparse, urljoin, unquote
else:
    from urlparse import urlparse, urljoin, unquote

# Python3 (and six) don't provide string
if six.PY3:
    from string import ascii_letters as string_ascii_letters
    from string import digits as string_digits
else:
    from string import letters as string_ascii_letters
    from string import digits as string_digits


if six.PY2:
    def decode_input(x):
        stdin_encoding = sys.stdin.encoding
        if stdin_encoding is None:
            stdin_encoding = "UTF-8"
        return x.decode(stdin_encoding)
else:
    def decode_input(x):
        return x


def random_string(length):
    """
    Return a pseudo-random string of specified length.
    """
    valid_chars = string_ascii_letters + string_digits

    return ''.join(random.choice(valid_chars) for i in range(length))


def clean_filename(s, minimal_change=False, keep_slashes=False):
    """
    Sanitize a string to be used as a filename.

    If minimal_change is set to True, then we only strip the bare minimum of
    characters that are problematic for filesystems (namely, ':', '/' and
    '\x00', '\n').

    If keep_slashes is set to True, we don't remove the '/' characters, as
    we may be receiving a full filename.
    """

    # First, deal with URL encoded strings
    # h = html_parser.HTMLParser()
    s = unquote(s)

    # Strip forbidden characters
    s = (
        s.replace(':', '-')
        .replace('\x00', '-')
        .replace('\n', '')
    )

    # FIXME (rbrito): As a very special case, we keep, for the moment,
    # slashes in the names (this should really be Python's directory
    # separator character)
    #
    # Furthermore, we should (perhaps?) only be operating on the basename of
    # the files, not on the entire filenames. This should be discussed
    # further with other people reviewing the proposed changes.
    if not keep_slashes:
        s = s.replace('/', '-')

    if minimal_change:
        return s

    s = s.replace('(', '').replace(')', '')
    s = s.rstrip('.')  # Remove excess of trailing dots

    s = s.strip().replace(' ', '_')
    valid_chars = '-_.()%s%s' % (string.ascii_letters, string.digits)
    return ''.join(c for c in s if c in valid_chars)


def get_anchor_format(a):
    """
    Extract the resource file-type format from the anchor.
    """

    # (. or format=) then (file_extension) then (? or $)
    # e.g. "...format=txt" or "...download.mp4?..."
    fmt = re.search(r"(?:\.|format=)(\w+)(?:\?.*)?$", a)
    return fmt.group(1) if fmt else None


def mkdir_p(path, mode=0o777):
    """
    Create subdirectory hierarchy given in the paths argument.
    """

    try:
        os.makedirs(path, mode)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def fix_url(url):
    """
    Strip whitespace characters from the beginning and the end of the url
    and add a default scheme.
    """
    if url is None:
        return None

    url = url.strip()

    if url and not urlparse(url).scheme:
        url = "http://" + url

    return url


def make_coursera_absolute_url(url):
    """
    If given url is relative adds coursera netloc,
    otherwise returns it without any changes.
    """

    if not bool(urlparse(url).netloc):
        return urljoin(COURSERA_URL, url)

    return url


def extend_supplement_links(destination, source):
    """
    Extends (merges) destination dictionary with supplement_links
    from source dictionary. Values are expected to be lists, or any
    data structure that has `extend` method.

    @param destination: Destination dictionary that will be extended.
    @type destination: @see CourseraOnDemand._extract_links_from_text

    @param source: Source dictionary that will be used to extend
        destination dictionary.
    @type source: @see CourseraOnDemand._extract_links_from_text
    """
    for key, value in iteritems(source):
        if key not in destination:
            destination[key] = value
        else:
            destination[key].extend(value)
