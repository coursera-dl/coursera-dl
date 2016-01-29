"""
This module contains implementations of different APIs that are used by the
downloader.
"""

import os
import json
import logging
from six import iterkeys
from six.moves.urllib_parse import quote_plus

from six import iteritems

from .utils import BeautifulSoup
from .network import get_page
from .define import (OPENCOURSE_SUPPLEMENT_URL,
                     OPENCOURSE_PROGRAMMING_ASSIGNMENTS_URL,
                     OPENCOURSE_ASSET_URL)


class CourseraOnDemand(object):
    """
    This is a class that provides a friendly interface to extract certain
    parts of on-demand courses. On-demand class is a new format that Coursera
    is using, they contain `/learn/' in their URLs. This class does not support
    old-style Coursera classes. This API is by no means complete.
    """

    def __init__(self, session, course_json):
        """
        Initialize Coursera OnDemand API.

        @param session: Current session that holds cookies and so on.
        @type session: requests.Session
        """
        self._session = session
        self._course_json = course_json

        self._course_id = self._course_json['id']

    def extract_files_from_programming(self, element_id):
        """
        Return a dictionary with supplement files (pdf, csv, zip, ipynb, html
        and so on) extracted from graded programming assignment.

        @param element_id: Element ID to extract files from.
        @type element_id: str

        @return: @see CourseraOnDemand._extract_supplement_links
        """
        logging.info('Gathering supplement URLs for element_id <%s>.', element_id)

        # Instructions contain text which in turn contains asset tags
        # which describe supplementary files.
        instructions = ''.join(self._extract_assignment_instructions(element_id))
        if not instructions:
            return {}

        # Extract asset tags from instructions text
        asset_map = self._extract_assets(instructions)
        ids = list(iterkeys(asset_map))
        if not ids:
            return {}

        # asset tags contain asset names and ids. We need to make another
        # HTTP request to get asset URL.
        asset_urls = self._extract_asset_urls(ids)

        supplement_links = {}

        # Build supplement links, providing nice titles along the way
        for asset in asset_urls:
            title = asset_map[asset['id']]['name']
            extension = asset_map[asset['id']]['extension']
            if extension not in supplement_links:
                supplement_links[extension] = []
            supplement_links[extension].append((asset['url'], title))

        return supplement_links

    def _extract_assets(self, text):
        """
        Extract assets from text into a convenient form.

        @param text: Text to extract assets from.
        @type text: str

        @return: Asset map.
        @rtype: {
            '<id>': {
                'name': '<name>',
                'extension': '<extension>'
            }
        }
        """
        soup = BeautifulSoup(text)
        asset_map = {}

        for asset in soup.find_all('asset'):
            asset_map[asset['id']] = {'name': asset['name'],
                                      'extension': asset['extension']}

        return asset_map

    def _extract_asset_urls(self, asset_ids):
        """
        Extract asset URLs along with asset ids.

        @param asset_ids: List of ids to get URLs for.
        @type assertn: [str]

        @return: List of dictionaries with asset URLs and ids.
        @rtype: [{
            'id': '<id>',
            'url': '<url>'
        }]
        """
        ids = quote_plus(','.join(asset_ids))
        url = OPENCOURSE_ASSET_URL.format(ids=ids)
        page = get_page(self._session, url)
        dom = json.loads(page)

        return [{'id': element['id'],
                 'url': element['url']}
                for element in dom['elements']]

    def _extract_assignment_instructions(self, element_id):
        """
        Extract assignment instructions.

        @param element_id: Element id to extract assignment instructions from.
        @type element_id: str

        @return: List of assignment instructions.
        @rtype: [str]
        """
        url = OPENCOURSE_PROGRAMMING_ASSIGNMENTS_URL.format(
            course_id=self._course_id, element_id=element_id)
        page = get_page(self._session, url)

        dom = json.loads(page)
        return [element['submissionLearnerSchema']['definition']
                ['assignmentInstructions']['definition']['value']
                for element in dom['elements']]

    def extract_files_from_supplement(self, element_id):
        """
        Return a dictionary with supplement files (pdf, csv, zip, ipynb, html
        and so on) extracted from supplement page.

        @return: @see CourseraOnDemand._extract_supplement_links
        """
        logging.info('Gathering supplement URLs for element_id <%s>.', element_id)

        url = OPENCOURSE_SUPPLEMENT_URL.format(
            course_id=self._course_id, element_id=element_id)
        page = get_page(self._session, url)

        dom = json.loads(page)
        supplement_content = {}

        # Supplement content has structure as follows:
        # 'linked' {
        #   'openCourseAssets.v1' [ {
        #       'definition' {
        #           'value'

        for asset in dom['linked']['openCourseAssets.v1']:
            value = asset['definition']['value']
            more = self._extract_supplement_links(value)

            for fmt, items in iteritems(more):
                # We need to merge possible several supplement content results
                if fmt in supplement_content:
                    supplement_content[fmt].extend(more[fmt])
                else:
                    supplement_content[fmt] = more[fmt]

        return supplement_content

    def _extract_supplement_links(self, page):
        """
        Extract supplement links from the html page that contains <a> tags
        with href attribute.

        @param page: HTML page.
        @type page: str

        @return: Dictionary with supplement links grouped by extension.
        @rtype: {
            '<extension1>': [
                ('<link1>', '<title1>'),
                ('<link2>', '<title2')
            ],
            'extension2': [
                ('<link3>', '<title3>'),
                ('<link4>', '<title4>')
            ]
        }
        """
        soup = BeautifulSoup(page)
        links = [item['href']
                 for item in soup.find_all('a') if 'href' in item.attrs]
        links = sorted(list(set(links)))
        supplement_links = {}

        for link in links:
            filename, extension = os.path.splitext(link)
            # Some courses put links to sites in supplement section, e.g.:
            # http://pandas.pydata.org/
            if extension is '':
                continue

            # Make lowercase and cut the leading/trailing dot
            extension = extension.lower().strip('.')
            basename = os.path.basename(filename)
            if extension not in supplement_links:
                supplement_links[extension] = []
            # Putting basename into the second slot of the tuple is important
            # because that will allow to download many supplements within a
            # single lecture, e.g.:
            # 01_slides-presented-in-this-module.pdf
            # 01_slides-presented-in-this-module_Dalal-cvpr05.pdf
            # 01_slides-presented-in-this-module_LM-3dtexton.pdf
            supplement_links[extension].append((link, basename))

        return supplement_links
