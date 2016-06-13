# vim: set fileencoding=utf8 :
"""
This module contains implementations of different APIs that are used by the
downloader.
"""

import os
import json
import base64
import logging
from six import iterkeys, iteritems
from six.moves.urllib_parse import quote_plus

from .utils import (BeautifulSoup, make_coursera_absolute_url,
                    extend_supplement_links, clean_url)
from .network import get_page, get_page_json
from .define import (OPENCOURSE_SUPPLEMENT_URL,
                     OPENCOURSE_PROGRAMMING_ASSIGNMENTS_URL,
                     OPENCOURSE_ASSET_URL,
                     OPENCOURSE_ASSETS_URL,
                     OPENCOURSE_API_ASSETS_V1_URL,
                     OPENCOURSE_ONDEMAND_COURSE_MATERIALS,
                     OPENCOURSE_VIDEO_URL,

                     INSTRUCTIONS_HTML_INJECTION,

                     IN_MEMORY_EXTENSION,
                     IN_MEMORY_MARKER)


class OnDemandCourseMaterialItems(object):
    """
    Helper class that allows accessing lecture JSONs by lesson IDs.
    """
    def __init__(self, items):
        """
        Initialization. Build a map from lessonId to Lecture (item)

        @param items: linked.OnDemandCourseMaterialItems key of
            OPENCOURSE_ONDEMAND_COURSE_MATERIALS response.
        @type items: dict
        """
        # Build a map of lessonId => Item
        self._items = dict((item['lessonId'], item) for item in items)

    @staticmethod
    def create(session, course_name):
        """
        Create an instance using a session and a course_name.

        @param session: Requests session.
        @type session: requests.Session

        @param course_name: Course name (slug) from course json.
        @type course_name: str

        @return: Instance of OnDemandCourseMaterialItems
        @rtype: OnDemandCourseMaterialItems
        """

        dom = get_page_json(session, OPENCOURSE_ONDEMAND_COURSE_MATERIALS,
                            class_name=course_name)
        return OnDemandCourseMaterialItems(
            dom['linked']['onDemandCourseMaterialItems.v1'])

    def get(self, lesson_id):
        """
        Return lecture by lesson ID.

        @param lesson_id: Lesson ID.
        @type lesson_id: str

        @return: Lesson JSON.
        @rtype: dict
        Example:
        {
          "id": "AUd0k",
          "moduleId": "0MGvs",
          "lessonId": "QgCuM",
          "name": "Programming Assignment 1: Decomposition of Graphs",
          "slug": "programming-assignment-1-decomposition-of-graphs",
          "timeCommitment": 10800000,
          "content": {
            "typeName": "gradedProgramming",
            "definition": {
              "programmingAssignmentId": "zHzR5yhHEeaE0BKOcl4zJQ@2",
              "gradingWeight": 20
            }
          },
          "isLocked": true,
          "itemLockedReasonCode": "PREMIUM",
          "trackId": "core"
        },
        """
        return self._items.get(lesson_id)


class CourseraOnDemand(object):
    """
    This is a class that provides a friendly interface to extract certain
    parts of on-demand courses. On-demand class is a new format that Coursera
    is using, they contain `/learn/' in their URLs. This class does not support
    old-style Coursera classes. This API is by no means complete.
    """

    def __init__(self, session, course_id):
        """
        Initialize Coursera OnDemand API.

        @param session: Current session that holds cookies and so on.
        @type session: requests.Session

        @param course_id: Course ID from course json.
        @type course_id: str
        """
        self._session = session
        self._course_id = course_id

    def extract_links_from_lecture(self,
                                   video_id, subtitle_language='en',
                                   resolution='540p', assets=None):
        """
        Return the download URLs of on-demand course video.

        @param video_id: Video ID.
        @type video_id: str

        @param subtitle_language: Subtitle language.
        @type subtitle_language: str

        @param resolution: Preferred video resolution.
        @type resolution: str

        @param assets: List of assets that may present in the video.
        @type assets: [str]

        @return: @see CourseraOnDemand._extract_links_from_text
        """
        if assets is None:
            assets = []

        links = self._extract_videos_and_subtitles_from_lecture(
            video_id, subtitle_language, resolution)

        assets = self._normalize_assets(assets)
        extend_supplement_links(
            links, self._extract_links_from_lecture_assets(assets))

        return links

    def _prettify_instructions(self, text):
        """
        Prettify instructions text to make it more suitable for offline reading.

        @param text: HTML (kinda) text to prettify.
        @type text: str

        @return: Prettified HTML with several markup tags replaced with HTML
            equivalents.
        @rtype: str
        """
        soup = BeautifulSoup(text)
        self._convert_instructions_basic(soup)
        self._convert_instructions_images(soup)
        return soup.prettify()

    def _convert_instructions_basic(self, soup):
        """
        Perform basic conversion of instructions markup. This includes
        replacement of several textual markup tags with their HTML equivalents.

        @param soup: BeautifulSoup instance.
        @type soup: BeautifulSoup
        """
        # 1. Inject basic CSS style
        css_soup = BeautifulSoup(INSTRUCTIONS_HTML_INJECTION)
        soup.head.append(css_soup)

        # 2. Replace <text> with <p>
        while soup.find('text'):
            soup.find('text').name = 'p'

        # 3. Replace <heading level="1"> with <h1>
        while soup.find('heading'):
            heading = soup.find('heading')
            heading.name = 'h%s' % heading.attrs.get('level', '1')

        # 4. Replace <code> with <pre>
        while soup.find('code'):
            soup.find('code').name = 'pre'

        # 5. Replace <list> with <ol> or <ul>
        while soup.find('list'):
            list_ = soup.find('list')
            type_ = list_.attrs.get('bullettype', 'numbers')
            list_.name = 'ol' if type_ == 'numbers' else 'ul'

    def _convert_instructions_images(self, soup):
        """
        Convert images of instructions markup. Images are downloaded,
        base64-encoded and inserted into <img> tags.

        @param soup: BeautifulSoup instance.
        @type soup: BeautifulSoup
        """
        # 6. Replace <img> assets with actual image contents
        images = [image for image in soup.find_all('img')
                  if image.attrs.get('assetid') is not None]
        if not images:
            return

        asset_ids = [image.attrs.get('assetid') for image in images]
        asset_list = get_page_json(self._session, OPENCOURSE_API_ASSETS_V1_URL,
                                   id=','.join(asset_ids))
        asset_map = dict((asset['id'], asset) for asset in asset_list['elements'])

        for image in images:
            url = asset_map[image['assetid']]['url']['url'].strip()
            request = self._session.get(url)
            if request.status_code == 200:
                content_type = request.headers.get('Content-Type', 'image/png')
                encoded64 = base64.b64encode(request.content).decode()
                image['src'] = 'data:%s;base64,%s' % (content_type, encoded64)

    def _normalize_assets(self, assets):
        """
        Perform asset normalization. For some reason, assets that are sometimes
        present in lectures, have "@1" at the end of their id. Such "uncut"
        asset id when fed to OPENCOURSE_ASSETS_URL results in error that says:
        "Routing error: 'get-all' not implemented". To avoid that, the last
        two characters from asset id are cut off and after that that method
        works fine. It looks like, Web UI is doing the same.

        @param assets: List of asset ids.
        @type assets: [str]

        @return: Normalized list of asset ids (without trailing "@1")
        @rtype: [str]
        """
        new_assets = []

        for asset in assets:
            # For example: giAxucdaEeWJTQ5WTi8YJQ@1
            if len(asset) == 24:
                # Turn it into: giAxucdaEeWJTQ5WTi8YJQ
                asset = asset[:-2]
            new_assets.append(asset)

        return new_assets

    def _extract_links_from_lecture_assets(self, asset_ids):
        """
        Extract links to files of the asset ids.

        @param asset_ids: List of asset ids.
        @type asset_ids: [str]

        @return: @see CourseraOnDemand._extract_links_from_text
        """
        links = {}

        def _add_asset(name, url, destination):
            filename, extension = os.path.splitext(name)
            if extension is '':
                return

            extension = extension.lower().strip('.').strip()
            basename = os.path.basename(filename)
            url = url.strip()

            if extension not in destination:
                destination[extension] = []
            destination[extension].append((url, basename))

        for asset_id in asset_ids:
            for asset in self._get_asset_urls(asset_id):
                _add_asset(asset['name'], asset['url'], links)

        return links

    def _get_asset_urls(self, asset_id):
        """
        Get list of asset urls and file names. This method may internally
        use _get_open_course_asset_urls to extract `asset` element types.

        @param asset_id: Asset ID.
        @type asset_id: str

        @return List of dictionaries with asset file names and urls.
        @rtype [{
            'name': '<filename.ext>'
            'url': '<url>'
        }]
        """
        dom = get_page_json(self._session, OPENCOURSE_ASSETS_URL, id=asset_id)
        logging.debug('Parsing JSON for asset_id <%s>.', asset_id)

        urls = []

        for element in dom['elements']:
            typeName = element['typeName']
            definition = element['definition']

            # Elements of `asset` types look as follows:
            #
            # {'elements': [{'definition': {'assetId': 'gtSfvscoEeW7RxKvROGwrw',
            #                               'name': 'Презентация к лекции'},
            #                'id': 'phxNlMcoEeWXCQ4nGuQJXw',
            #                'typeName': 'asset'}],
            #  'linked': None,
            #  'paging': None}
            #
            if typeName == 'asset':
                open_course_asset_id = definition['assetId']
                for asset in self._get_open_course_asset_urls(open_course_asset_id):
                    urls.append({'name': asset['name'].strip(),
                                 'url': asset['url'].strip()})

            # Elements of `url` types look as follows:
            #
            # {'elements': [{'definition': {'name': 'What motivates you.pptx',
            #                               'url': 'https://d396qusza40orc.cloudfront.net/learning/Powerpoints/2-4A_What_motivates_you.pptx'},
            #                'id': '0hixqpWJEeWQkg5xdHApow',
            #                'typeName': 'url'}],
            #  'linked': None,
            #  'paging': None}
            #
            elif typeName == 'url':
                urls.append({'name': definition['name'].strip(),
                             'url': definition['url'].strip()})

            else:
                logging.warning(
                    'Unknown asset typeName: %s\ndom: %s\n'
                    'If you think the downloader missed some '
                    'files, please report the issue here:\n'
                    'https://github.com/coursera-dl/coursera-dl/issues/new',
                    typeName, json.dumps(dom, indent=4))

        return urls

    def _get_open_course_asset_urls(self, asset_id):
        """
        Get list of asset urls and file names. This method only works
        with asset_ids extracted internally by _get_asset_urls method.

        @param asset_id: Asset ID.
        @type asset_id: str

        @return List of dictionaries with asset file names and urls.
        @rtype [{
            'name': '<filename.ext>'
            'url': '<url>'
        }]
        """
        dom = get_page_json(self._session, OPENCOURSE_API_ASSETS_V1_URL, id=asset_id)

        # Structure is as follows:
        # elements [ {
        #   name
        #   url {
        #       url
        return [{'name': element['name'].strip(),
                 'url': element['url']['url'].strip()}
                for element in dom['elements']]

    def _extract_videos_and_subtitles_from_lecture(self,
                                                   video_id,
                                                   subtitle_language='en',
                                                   resolution='540p'):

        dom = get_page_json(self._session, OPENCOURSE_VIDEO_URL, video_id=video_id)

        logging.debug('Parsing JSON for video_id <%s>.', video_id)
        video_content = {}

        # videos
        logging.info('Gathering video URLs for video_id <%s>.', video_id)
        sources = dom['sources']
        sources.sort(key=lambda src: src['resolution'])
        sources.reverse()

        # Try to select resolution requested by the user.
        filtered_sources = [source
                            for source in sources
                            if source['resolution'] == resolution]

        if len(filtered_sources) == 0:
            # We will just use the 'vanilla' version of sources here, instead of
            # filtered_sources.
            logging.warn('Requested resolution %s not available for <%s>. '
                         'Downloading highest resolution available instead.',
                         resolution, video_id)
        else:
            logging.info('Proceeding with download of resolution %s of <%s>.',
                         resolution, video_id)
            sources = filtered_sources

        video_url = sources[0]['formatSources']['video/mp4']
        video_content['mp4'] = video_url

        # subtitles and transcripts
        subtitle_nodes = [
            ('subtitles',    'srt', 'subtitle'),
            ('subtitlesTxt', 'txt', 'transcript'),
        ]
        for (subtitle_node, subtitle_extension, subtitle_description) in subtitle_nodes:
            logging.info('Gathering %s URLs for video_id <%s>.', subtitle_description, video_id)
            subtitles = dom.get(subtitle_node)
            if subtitles is not None:
                if subtitle_language == 'all':
                    for current_subtitle_language in subtitles:
                        video_content[current_subtitle_language + '.' + subtitle_extension] = make_coursera_absolute_url(subtitles.get(current_subtitle_language))
                else:
                    if subtitle_language != 'en' and subtitle_language not in subtitles:
                        logging.warning("%s unavailable in '%s' language for video "
                                        "with video id: [%s], falling back to 'en' "
                                        "%s", subtitle_description.capitalize(), subtitle_language, video_id, subtitle_description)
                        subtitle_language = 'en'

                    subtitle_url = subtitles.get(subtitle_language)
                    if subtitle_url is not None:
                        # some subtitle urls are relative!
                        video_content[subtitle_language + '.' + subtitle_extension] = make_coursera_absolute_url(subtitle_url)

        lecture_video_content = {}
        for key, value in iteritems(video_content):
            lecture_video_content[key] = [(value, '')]

        return lecture_video_content

    def extract_links_from_programming(self, element_id):
        """
        Return a dictionary with links to supplement files (pdf, csv, zip,
        ipynb, html and so on) extracted from graded programming assignment.

        @param element_id: Element ID to extract files from.
        @type element_id: str

        @return: @see CourseraOnDemand._extract_links_from_text
        """
        logging.info('Gathering supplement URLs for element_id <%s>.', element_id)

        # Assignment text (instructions) contains asset tags which describe
        # supplementary files.
        text = ''.join(self._extract_assignment_text(element_id))
        if not text:
            return {}

        supplement_links = self._extract_links_from_text(text)

        instructions = (IN_MEMORY_MARKER + self._prettify_instructions(text),
                       'instructions')
        extend_supplement_links(
            supplement_links, {IN_MEMORY_EXTENSION: [instructions]})

        return supplement_links

    def extract_links_from_supplement(self, element_id):
        """
        Return a dictionary with supplement files (pdf, csv, zip, ipynb, html
        and so on) extracted from supplement page.

        @return: @see CourseraOnDemand._extract_links_from_text
        """
        logging.info('Gathering supplement URLs for element_id <%s>.', element_id)

        dom = get_page_json(self._session, OPENCOURSE_SUPPLEMENT_URL,
                            course_id=self._course_id, element_id=element_id)

        supplement_content = {}

        # Supplement content has structure as follows:
        # 'linked' {
        #   'openCourseAssets.v1' [ {
        #       'definition' {
        #           'value'

        for asset in dom['linked']['openCourseAssets.v1']:
            value = asset['definition']['value']
            # Supplement lecture types are known to contain both <asset> tags
            # and <a href> tags (depending on the course), so we extract
            # both of them.
            extend_supplement_links(
                supplement_content, self._extract_links_from_text(value))

            instructions = (IN_MEMORY_MARKER + self._prettify_instructions(value),
                           'instructions')
            extend_supplement_links(
                supplement_content, {IN_MEMORY_EXTENSION: [instructions]})

        return supplement_content

    def _extract_asset_tags(self, text):
        """
        Extract asset tags from text into a convenient form.

        @param text: Text to extract asset tags from. This text contains HTML
            code that is parsed by BeautifulSoup.
        @type text: str

        @return: Asset map.
        @rtype: {
            '<id>': {
                'name': '<name>',
                'extension': '<extension>'
            },
            ...
        }
        """
        soup = BeautifulSoup(text)
        asset_tags_map = {}

        for asset in soup.find_all('asset'):
            asset_tags_map[asset['id']] = {'name': asset['name'],
                                           'extension': asset['extension']}

        return asset_tags_map

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
        dom = get_page_json(self._session, OPENCOURSE_ASSET_URL,
                            ids=quote_plus(','.join(asset_ids)))

        return [{'id': element['id'],
                 'url': element['url'].strip()}
                for element in dom['elements']]

    def _extract_assignment_text(self, element_id):
        """
        Extract assignment text (instructions).

        @param element_id: Element id to extract assignment instructions from.
        @type element_id: str

        @return: List of assignment text (instructions).
        @rtype: [str]
        """
        dom = get_page_json(self._session, OPENCOURSE_PROGRAMMING_ASSIGNMENTS_URL,
                            course_id=self._course_id, element_id=element_id)


        return [element['submissionLearnerSchema']['definition']
                ['assignmentInstructions']['definition']['value']
                for element in dom['elements']]

    def _extract_links_from_text(self, text):
        """
        Extract supplement links from the html text. Links may be provided
        in two ways:
            1. <a> tags with href attribute
            2. <asset> tags with id attribute (requires additional request
               to get the direct URL to the asset file)

        @param text: HTML text.
        @type text: str

        @return: Dictionary with supplement links grouped by extension.
        @rtype: {
            '<extension1>': [
                ('<link1>', '<title1>'),
                ('<link2>', '<title2')
            ],
            'extension2': [
                ('<link3>', '<title3>'),
                ('<link4>', '<title4>')
            ],
            ...
        }
        """
        supplement_links = self._extract_links_from_a_tags_in_text(text)

        extend_supplement_links(
            supplement_links,
            self._extract_links_from_asset_tags_in_text(text))

        return supplement_links

    def _extract_links_from_asset_tags_in_text(self, text):
        """
        Scan the text and extract asset tags and links to corresponding
        files.

        @param text: Page text.
        @type text: str

        @return: @see CourseraOnDemand._extract_links_from_text
        """
        # Extract asset tags from instructions text
        asset_tags_map = self._extract_asset_tags(text)
        ids = list(iterkeys(asset_tags_map))
        if not ids:
            return {}

        # asset tags contain asset names and ids. We need to make another
        # HTTP request to get asset URL.
        asset_urls = self._extract_asset_urls(ids)

        supplement_links = {}

        # Build supplement links, providing nice titles along the way
        for asset in asset_urls:
            title = asset_tags_map[asset['id']]['name']
            extension = asset_tags_map[asset['id']]['extension'].strip()
            url = asset['url'].strip()
            if extension not in supplement_links:
                supplement_links[extension] = []
            supplement_links[extension].append((url, title))

        return supplement_links

    def _extract_links_from_a_tags_in_text(self, text):
        """
        Extract supplement links from the html text that contains <a> tags
        with href attribute.

        @param text: HTML text.
        @type text: str

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
        soup = BeautifulSoup(text)
        links = [item['href'].strip()
                 for item in soup.find_all('a') if 'href' in item.attrs]
        links = sorted(list(set(links)))
        supplement_links = {}

        for link in links:
            filename, extension = os.path.splitext(clean_url(link))
            # Some courses put links to sites in supplement section, e.g.:
            # http://pandas.pydata.org/
            if extension is '':
                continue

            # Make lowercase and cut the leading/trailing dot
            extension = extension.lower().strip('.').strip()
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
