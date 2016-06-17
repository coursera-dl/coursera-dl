"""
This module contains filtering functions.
"""

import re

from six.moves.urllib_parse import urlparse


# These formats are trusted and are not skipped
VALID_FORMATS = r"""^mp4$|
                    ^pdf$|
                    ^.?.?\.?txt$|
                    ^.?.?\.?srt$|
                    .*txt$|
                    .*srt$|
                    ^html?$|
                    ^zip$|
                    ^rar$|
                    ^[ct]sv$|
                    ^xlsx$|
                    ^ipynb$|
                    ^json$|
                    ^pptx?$|
                    ^docx?$|
                    ^xls$|
                    ^py$|
                    ^Rmd$|
                    ^Rdata$|
                    ^wf1$"""

# Non simple format contains characters besides letters, numbers, "_" and "-"
NON_SIMPLE_FORMAT = r".*[^a-zA-Z0-9_-]"

RE_VALID_FORMATS = re.compile(VALID_FORMATS, re.VERBOSE)
RE_NON_SIMPLE_FORMAT = re.compile(NON_SIMPLE_FORMAT)


def skip_format_url(format_, url):
    """
    Checks whether a give format/url should be skipped and not downloaded.

    @param format_: Filename format (extension).
    @type format_: str (e.g. html, txt, zip, pdf)

    @param url: URL.
    @type url: str

    @return: True if format/url should be skipped, False otherwise.
    @rtype bool
    """
    # Do not download empty formats
    if format_ == '':
        return True

    # Do not download email addresses
    if ('mailto:' in url) and ('@' in url):
        return True

    # These are trusted manually added formats, do not skip them
    if RE_VALID_FORMATS.match(format_):
        return False

    # Simple formats only contain letters, numbers, "_" and "-"
    # If this a non simple format?
    if RE_NON_SIMPLE_FORMAT.match(format_):
        return True

    # Is this a link to the site root?
    parsed = urlparse(url)
    if parsed.path in ('', '/'):
        return True

    # Do not skip
    return False
