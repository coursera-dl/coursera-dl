# -*- coding: utf-8 -*-

"""
This module provides utility functions that are used within the script.
"""

import errno
import os
import re
import string
import urlparse


def clean_filename(s):
    """
    Sanitize a string to be used as a filename.
    """

    # strip paren portions which contain trailing time length (...)
    s = re.sub(r"\([^\(]*$", '', s)
    s = s.strip().replace(':', '-').replace(' ', '_')
    s = s.replace('nbsp', '')
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


def mkdir_p(path):
    """
    Create subdirectory hierarchy given in the paths argument.
    """

    try:
        os.makedirs(path)
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

    if url and not urlparse.urlparse(url).scheme:
        url = "http://" + url

    return url
