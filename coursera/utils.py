# -*- coding: utf-8 -*-

"""
This module provides utility functions that are used within the script.
"""

import errno
import os
import re
import string
import sys

import six

#  six.moves doesn’t support urlparse
if six.PY3:  # pragma: no cover
    from urllib.parse import urlparse
else:
    from urlparse import urlparse


if six.PY2:
    def decode_input(x):
        stdin_encoding = sys.stdin.encoding
        if stdin_encoding is None: stdin_encoding = "UTF-8"
        return x.decode(stdin_encoding)
else:
    def decode_input(x):
        return x


def clean_filename(s, minimal_change=False):
    """
   Sanitize a string to be used as a filename.

    If minimal_change is set to true, then we only strip the bare minimum of
    characters that are problematic for filesystems (namely, ':', '/' and
    '\x00', '\n').
    """

    # strip paren portions which contain trailing time length (...)
    s = (
        s.replace(':', '-')
        .replace('/', '-')
        .replace('\x00', '-')
        .replace('\n', '')
        )

    if minimal_change:
        return s

    s = s.replace('(', '').replace(')', '')
    s = s.rstrip('.') # Remove excess of trailing dots

    s = s.replace('nbsp', '')
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
    return (fmt.group(1) if fmt else None)


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
