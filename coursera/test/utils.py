"""
Helper functions that are only used in tests.
"""
import os
import re
from io import open

from six import iteritems

from coursera.define import IN_MEMORY_MARKER
from coursera.utils import BeautifulSoup


def slurp_fixture(path):
    return open(os.path.join(os.path.dirname(__file__),
                             "fixtures", path), encoding='utf8').read()


def links_to_plain_text(links):
    """
    Converts extracted links into text and cleans up extra whitespace. Only HTML
    sections are converted. This is a helper to be used in tests.

    @param links: Links obtained from such methods as extract_links_from_peer_assignment.
    @type links: @see CourseraOnDemand._extract_links_from_text

    @return: HTML converted to plain text with extra space removed.
    @rtype: str
    """
    result = []
    for filetype, contents in iteritems(links):
        if filetype != 'html':
            continue

        for content, _prefix in contents:
            if content.startswith(IN_MEMORY_MARKER):
                content = content[len(IN_MEMORY_MARKER):]

            soup = BeautifulSoup(content)
            [script.extract() for script in soup(["script", "style"])]
            text = re.sub(r'[ \t\r\n]+', ' ', soup.get_text()).strip()
            result.append(text)

    return ''.join(result)
