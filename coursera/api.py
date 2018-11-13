# vim: set fileencoding=utf8 :
"""
This module contains implementations of different APIs that are used by the
downloader.
"""

import os
import re
import json
import base64
import logging
import time
import requests
import urllib

from collections import namedtuple, OrderedDict
from six import iterkeys, iteritems
from six.moves.urllib_parse import quote_plus
import attr

from .utils import (BeautifulSoup, make_coursera_absolute_url,
                    extend_supplement_links, clean_url, clean_filename,
                    is_debug_run, unescape_html)
from .network import get_reply, get_page, post_page_and_reply
from .define import (OPENCOURSE_SUPPLEMENT_URL,
                     OPENCOURSE_PROGRAMMING_ASSIGNMENTS_URL,
                     OPENCOURSE_ASSET_URL,
                     OPENCOURSE_ASSETS_URL,
                     OPENCOURSE_API_ASSETS_V1_URL,
                     OPENCOURSE_ONDEMAND_COURSE_MATERIALS,
                     OPENCOURSE_ONDEMAND_COURSE_MATERIALS_V2,
                     OPENCOURSE_ONDEMAND_COURSES_V1,
                     OPENCOURSE_ONDEMAND_LECTURE_VIDEOS_URL,
                     OPENCOURSE_ONDEMAND_LECTURE_ASSETS_URL,
                     OPENCOURSE_ONDEMAND_SPECIALIZATIONS_V1,
                     OPENCOURSE_MEMBERSHIPS,
                     OPENCOURSE_REFERENCES_POLL_URL,
                     OPENCOURSE_REFERENCE_ITEM_URL,
                     OPENCOURSE_PROGRAMMING_IMMEDIATE_INSTRUCTIOINS_URL,
                     OPENCOURSE_PEER_ASSIGNMENT_INSTRUCTIONS,

                     # New feature, Notebook (Python Jupyter)
                     OPENCOURSE_NOTEBOOK_DESCRIPTIONS,
                     OPENCOURSE_NOTEBOOK_LAUNCHES,
                     OPENCOURSE_NOTEBOOK_TREE,
                     OPENCOURSE_NOTEBOOK_DOWNLOAD,

                     POST_OPENCOURSE_API_QUIZ_SESSION,
                     POST_OPENCOURSE_API_QUIZ_SESSION_GET_STATE,
                     POST_OPENCOURSE_ONDEMAND_EXAM_SESSIONS,
                     POST_OPENCOURSE_ONDEMAND_EXAM_SESSIONS_GET_STATE,

                     INSTRUCTIONS_HTML_INJECTION_PRE,
                     INSTRUCTIONS_HTML_MATHJAX_URL,
                     INSTRUCTIONS_HTML_INJECTION_AFTER,

                     IN_MEMORY_EXTENSION,
                     IN_MEMORY_MARKER)


from .cookies import prepare_auth_headers


class QuizExamToMarkupConverter(object):
    """
    Converts quiz/exam JSON into semi HTML (Coursera Markup) for local viewing.
    The output needs to be further processed by MarkupToHTMLConverter.
    """
    KNOWN_QUESTION_TYPES = ('mcq',
                            'mcqReflect',
                            'checkbox',
                            'singleNumeric',
                            'textExactMatch',
                            'mathExpression',
                            'regex',
                            'reflect')

    # TODO: support live MathJAX preview rendering for mathExpression
    # and regex question types
    KNOWN_INPUT_TYPES = ('textExactMatch',
                         'singleNumeric',
                         'mathExpression',
                         'regex',
                         'reflect')

    def __init__(self, session):
        self._session = session

    def __call__(self, quiz_or_exam_json):
        result = []

        for question_index, question_json in enumerate(quiz_or_exam_json['questions']):
            question_type = question_json['question']['type']
            if question_type not in self.KNOWN_QUESTION_TYPES:
                logging.info('Unknown question type: %s', question_type)
                logging.info('Question json: %s', question_json)
                logging.info('Please report class name, quiz name and the data'
                             ' above to coursera-dl authors')

            prompt = question_json['variant']['definition']['prompt']
            options = question_json['variant']['definition'].get('options', [])

            # Question number
            result.append('<h3>Question %d</h3>' % (question_index + 1))

            # Question text
            question_text = unescape_html(prompt['definition']['value'])
            result.append(question_text)

            # Input for answer
            if question_type in self.KNOWN_INPUT_TYPES:
                result.extend(self._generate_input_field())

            # Convert input_type from JSON reply to HTML input type
            input_type = {
                'mcq': 'radio',
                'mcqReflect': 'radio',
                'checkbox': 'checkbox'
            }.get(question_type, '')

            # Convert options, they are either checkboxes or radio buttons
            result.extend(self._convert_options(
                question_index, options, input_type))

            result.append('<hr>')

        return '\n'.join(result)

    def _convert_options(self, question_index, options, input_type):
        if not options:
            return []

        result = ['<form>']

        for option in options:
            option_text = unescape_html(
                option['display']['definition']['value'])

            # We need to replace <text> with <span> so that answer text
            # stays on the same line with checkbox/radio button
            option_text = self._replace_tag(option_text, 'text', 'span')
            result.append('<label><input type="%s" name="%s">'
                          '%s<br></label>' % (
                              input_type, question_index, option_text))

        result.append('</form>')
        return result

    def _replace_tag(self, text, initial_tag, target_tag):
        soup = BeautifulSoup(text)
        while soup.find(initial_tag):
            soup.find(initial_tag).name = target_tag
        return soup.prettify()

    def _generate_input_field(self):
        return ['<form><label>Enter answer here:<input type="text" '
                'name=""><br></label></form>']


class MarkupToHTMLConverter(object):
    def __init__(self, session, mathjax_cdn_url=None):
        self._session = session
        self._asset_retriever = AssetRetriever(session)
        if not mathjax_cdn_url:
            mathjax_cdn_url = INSTRUCTIONS_HTML_MATHJAX_URL
        self._mathjax_cdn_url = mathjax_cdn_url

    def __call__(self, markup):
        """
        Convert instructions markup to make it more suitable for
        offline reading.

        @param markup: HTML (kinda) markup to prettify.
        @type markup: str

        @return: Prettified HTML with several markup tags replaced with HTML
            equivalents.
        @rtype: str
        """
        soup = BeautifulSoup(markup)
        self._convert_markup_basic(soup)
        self._convert_markup_images(soup)
        self._convert_markup_audios(soup)
        return soup.prettify()

    def _convert_markup_basic(self, soup):
        """
        Perform basic conversion of instructions markup. This includes
        replacement of several textual markup tags with their HTML equivalents.

        @param soup: BeautifulSoup instance.
        @type soup: BeautifulSoup
        """
        # Inject meta charset tag
        meta = soup.new_tag('meta', charset='UTF-8')
        soup.insert(0, meta)

        # 1. Inject basic CSS style
        css = "".join([
            INSTRUCTIONS_HTML_INJECTION_PRE,
            self._mathjax_cdn_url,
            INSTRUCTIONS_HTML_INJECTION_AFTER])
        css_soup = BeautifulSoup(css)
        soup.append(css_soup)

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

    def _convert_markup_images(self, soup):
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

        # Get assetid attribute from all images
        asset_ids = [image.attrs.get('assetid') for image in images]
        self._asset_retriever(asset_ids)

        for image in images:
            # Encode each image using base64
            asset = self._asset_retriever[image['assetid']]
            if asset.data is not None:
                encoded64 = base64.b64encode(asset.data).decode()
                image['src'] = 'data:%s;base64,%s' % (
                    asset.content_type, encoded64)

    def _convert_markup_audios(self, soup):
        """
        Convert audios of instructions markup. Audios are downloaded,
        base64-encoded and inserted as <audio controls> <source> tag.

        @param soup: BeautifulSoup instance.
        @type soup: BeautifulSoup
        """
        # 7. Replace <asset> audio assets with actual audio contents
        audios = [audio for audio in soup.find_all('asset')
                  if audio.attrs.get('id') is not None
                  and audio.attrs.get('assettype') == 'audio']
        if not audios:
            return

        # Get assetid attribute from all audios
        asset_ids = [audio.attrs.get('id') for audio in audios]
        self._asset_retriever(asset_ids)

        for audio in audios:
            # Encode each audio using base64
            asset = self._asset_retriever[audio['id']]
            if asset.data is not None:
                encoded64 = base64.b64encode(asset.data).decode()
                data_string = 'data:%s;base64,%s' % (
                    asset.content_type, encoded64)

                source_tag = soup.new_tag(
                    'source', src=data_string, type=asset.content_type)
                controls_tag = soup.new_tag('audio', controls="")
                controls_tag.string = 'Your browser does not support the audio element.'

                controls_tag.append(source_tag)
                audio.insert_after(controls_tag)


class OnDemandCourseMaterialItemsV1(object):
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

        dom = get_page(session, OPENCOURSE_ONDEMAND_COURSE_MATERIALS,
                       json=True,
                       class_name=course_name)
        return OnDemandCourseMaterialItemsV1(
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


class Asset(namedtuple('Asset', 'id name type_name url content_type data')):
    """
    This class contains information about an asset.
    """
    __slots__ = ()

    def __repr__(self):
        return 'Asset(id="%s", name="%s", type_name="%s", url="%s", content_type="%s", data="<...>")' % (
            self.id, self.name, self.type_name, self.url, self.content_type)


class AssetRetriever(object):
    """
    This class helps download assets by their ID.
    """

    def __init__(self, session):
        self._session = session
        self._asset_mapping = {}

    def __getitem__(self, asset_id):
        return self._asset_mapping[asset_id]

    def __call__(self, asset_ids, download=True):
        result = []

        # Download information about assets (by IDs)
        asset_list = get_page(self._session, OPENCOURSE_API_ASSETS_V1_URL,
                              json=True,
                              id=','.join(asset_ids))

        # Create a map "asset_id => asset" for easier access
        asset_map = dict((asset['id'], asset)
                         for asset in asset_list['elements'])

        for asset_id in asset_ids:
            # Download each asset
            asset_dict = asset_map[asset_id]

            url = asset_dict['url']['url'].strip()
            data, content_type = None, None

            if download:
                reply = get_reply(self._session, url)
                if reply.status_code == 200:
                    data = reply.content
                    content_type = reply.headers.get('Content-Type')

            asset = Asset(id=asset_dict['id'].strip(),
                          name=asset_dict['name'].strip(),
                          type_name=asset_dict['typeName'].strip(),
                          url=url,
                          content_type=content_type,
                          data=data)

            self._asset_mapping[asset.id] = asset
            result.append(asset)

        return result


@attr.s
class ModuleV1(object):
    name = attr.ib()
    id = attr.ib()
    slug = attr.ib()
    child_ids = attr.ib()

    def children(self, all_children):
        return [all_children[child] for child in self.child_ids]


@attr.s
class ModulesV1(object):
    children = attr.ib()

    @staticmethod
    def from_json(data):
        return ModulesV1(OrderedDict(
            (item['id'],
             ModuleV1(item['name'],
                      item['id'],
                      item['slug'],
                      item['lessonIds']))
            for item in data
        ))

    def __getitem__(self, key):
        return self.children[key]

    def __iter__(self):
        return iter(self.children.values())


@attr.s
class LessonV1(object):
    name = attr.ib()
    id = attr.ib()
    slug = attr.ib()
    child_ids = attr.ib()

    def children(self, all_children):
        return [all_children[child] for child in self.child_ids]


@attr.s
class LessonsV1(object):
    children = attr.ib()

    @staticmethod
    def from_json(data):
        return LessonsV1(OrderedDict(
            (item['id'],
             LessonV1(item['name'],
                      item['id'],
                      item['slug'],
                      item['itemIds']))
            for item in data
        ))

    def __getitem__(self, key):
        return self.children[key]


@attr.s
class ItemV2(object):
    name = attr.ib()
    id = attr.ib()
    slug = attr.ib()
    type_name = attr.ib()
    lesson_id = attr.ib()
    module_id = attr.ib()


@attr.s
class ItemsV2(object):
    children = attr.ib()

    @staticmethod
    def from_json(data):
        return ItemsV2(OrderedDict(
            (item['id'],
             ItemV2(item['name'],
                    item['id'],
                    item['slug'],
                    item['contentSummary']['typeName'],
                    item['lessonId'],
                    item['moduleId']))
            for item in data
        ))

    def __getitem__(self, key):
        return self.children[key]


@attr.s
class VideoV1(object):
    resolution = attr.ib()
    mp4_video_url = attr.ib()


@attr.s
class VideosV1(object):
    children = attr.ib()

    @staticmethod
    def from_json(data):

        videos = [VideoV1(resolution, links['mp4VideoUrl'])
                  for resolution, links
                  in data['sources']['byResolution'].items()]
        videos.sort(key=lambda video: video.resolution, reverse=True)

        videos = OrderedDict(
            (video.resolution, video)
            for video in videos
        )
        return VideosV1(videos)

    def __contains__(self, key):
        return key in self.children

    def __getitem__(self, key):
        return self.children[key]

    def get_best(self):
        return next(iter(self.children.values()))


def expand_specializations(session, class_names):
    """
    Checks whether any given name is not a class but a specialization.

    If it's a specialization, expand the list of class names with the child
    class names.
    """
    result = []
    for class_name in class_names:
        specialization = SpecializationV1.create(session, class_name)
        if specialization is None:
            result.append(class_name)
        else:
            result.extend(specialization.children)
            logging.info('Expanded specialization "%s" into the following'
                         ' classes: %s',
                         class_name, ' '.join(specialization.children))

    return result


@attr.s
class SpecializationV1(object):
    children = attr.ib()

    @staticmethod
    def create(session, class_name):
        try:
            dom = get_page(session, OPENCOURSE_ONDEMAND_SPECIALIZATIONS_V1,
                           json=True, quiet=True,
                           class_name=class_name)
        except requests.exceptions.HTTPError as e:
            logging.debug('Could not expand %s: %s', class_name, e)
            return None

        return SpecializationV1(
            [course['slug'] for course in dom['linked']['courses.v1']])


class CourseraOnDemand(object):
    """
    This is a class that provides a friendly interface to extract certain
    parts of on-demand courses. On-demand class is a new format that Coursera
    is using, they contain `/learn/' in their URLs. This class does not support
    old-style Coursera classes. This API is by no means complete.
    """

    def __init__(self, session, course_id, course_name,
                 unrestricted_filenames=False,
                 mathjax_cdn_url=None):
        """
        Initialize Coursera OnDemand API.

        @param session: Current session that holds cookies and so on.
        @type session: requests.Session

        @param course_id: Course ID from course json.
        @type course_id: str

        @param unrestricted_filenames: Flag that indicates whether grabbed
            file names should endure stricter character filtering. @see
            `clean_filename` for the details.
        @type unrestricted_filenames: bool
        """
        self._session = session
        self._notebook_cookies = None
        self._course_id = course_id
        self._course_name = course_name

        self._unrestricted_filenames = unrestricted_filenames
        self._user_id = None

        self._quiz_to_markup = QuizExamToMarkupConverter(session)
        self._markup_to_html = MarkupToHTMLConverter(
            session, mathjax_cdn_url=mathjax_cdn_url)
        self._asset_retriever = AssetRetriever(session)

    def obtain_user_id(self):
        reply = get_page(self._session, OPENCOURSE_MEMBERSHIPS, json=True)
        elements = reply['elements']
        user_id = elements[0]['userId'] if elements else None
        self._user_id = user_id

    def list_courses(self):
        """
        List enrolled courses.

        @return: List of enrolled courses.
        @rtype: [str]
        """
        reply = get_page(self._session, OPENCOURSE_MEMBERSHIPS, json=True)
        course_list = reply['linked']['courses.v1']
        slugs = [element['slug'] for element in course_list]
        return slugs

    def extract_links_from_exam(self, exam_id):
        try:
            session_id = self._get_exam_session_id(exam_id)
            exam_json = self._get_exam_json(exam_id, session_id)
            return self._convert_quiz_json_to_links(exam_json, 'exam')
        except requests.exceptions.HTTPError as exception:
            logging.error('Could not download exam %s: %s', exam_id, exception)
            if is_debug_run():
                logging.exception(
                    'Could not download exam %s: %s', exam_id, exception)
            return None

    def _get_notebook_folder(self, url, jupyterId, **kwargs):

        supplement_links = {}

        url = url.format(**kwargs)
        reply = get_page(self._session, url, json=True)

        for content in reply['content']:

            if content['type'] == 'directory':
                a = self._get_notebook_folder(
                    OPENCOURSE_NOTEBOOK_TREE, jupyterId, jupId=jupyterId,
                    path=content['path'], timestamp=int(time.time()))
                supplement_links.update(a)

            elif content['type'] == 'file':
                tmp_url = OPENCOURSE_NOTEBOOK_DOWNLOAD.format(
                    path=content['path'], jupId=jupyterId,
                    timestamp=int(time.time()))
                filename, extension = os.path.splitext(clean_url(tmp_url))

                head, tail = os.path.split(content['path'])
                # '/' in the following line is for a reason:
                # @noureddin says: "I split head using split('/') not
                # os.path.split() because it's seems to me that it comes from a
                # web page, so the separator will always be /, so using the
                # native path splitting function is not the most portable
                # way to do it."
                # Original pull request:
                # https://github.com/coursera-dl/coursera-dl/pull/654
                head = '/'.join([clean_filename(dir, minimal_change=True)
                                 for dir in head.split('/')])
                tail = clean_filename(tail, minimal_change=True)

                if not os.path.isdir(self._course_name + "/notebook/" + head + "/"):
                    logging.info('Creating [%s] directories...', head)
                    os.makedirs(self._course_name + "/notebook/" + head + "/")

                r = requests.get(tmp_url.replace(" ", "%20"),
                                 cookies=self._session.cookies)
                if not os.path.exists(self._course_name + "/notebook/" + head + "/" + tail):
                    logging.info('Downloading %s into %s', tail, head)
                    with open(self._course_name + "/notebook/" + head + "/" + tail, 'wb+') as f:
                        f.write(r.content)
                else:
                    logging.info('Skipping %s... (file exists)', tail)

                if str(extension[1:]) not in supplement_links:
                    supplement_links[str(extension[1:])] = []

                supplement_links[str(extension[1:])].append(
                    (tmp_url.replace(" ", "%20"), filename))

            elif content['type'] == 'notebook':
                tmp_url = OPENCOURSE_NOTEBOOK_DOWNLOAD.format(
                    path=content['path'], jupId=jupyterId, timestamp=int(time.time()))
                filename, extension = os.path.splitext(clean_url(tmp_url))

                head, tail = os.path.split(content['path'])

                if not os.path.isdir(self._course_name + "/notebook/" + head + "/"):
                    logging.info('Creating [%s] directories...', head)
                    os.makedirs(self._course_name + "/notebook/" + head + "/")

                r = requests.get(tmp_url.replace(" ", "%20"),
                                 cookies=self._session.cookies)
                if not os.path.exists(self._course_name + "/notebook/" + head + "/" + tail):
                    logging.info(
                        'Downloading Jupyter %s into %s', tail, head)
                    with open(self._course_name + "/notebook/" + head + "/" + tail, 'wb+') as f:
                        f.write(r.content)
                else:
                    logging.info('Skipping %s... (file exists)', tail)

                if "ipynb" not in supplement_links:
                    supplement_links["ipynb"] = []

                supplement_links["ipynb"].append(
                    (tmp_url.replace(" ", "%20"), filename))

            else:
                logging.info(
                    'Unsupported typename %s in notebook', content['type'])

        return supplement_links

    def _get_notebook_json(self, notebook_id, authorizationId):

        headers = self._auth_headers_with_json()
        reply = get_page(
            self._session,
            OPENCOURSE_NOTEBOOK_DESCRIPTIONS,
            json=False,
            authId=authorizationId,
            headers=headers
        )

        jupyted_id = re.findall(r"\"\/user\/(.*)\/tree\"", reply)
        if len(jupyted_id) == 0:
            logging.error('Could not download notebook %s', notebook_id)
            return None

        jupyted_id = jupyted_id[0]

        newReq = requests.Session()
        req = newReq.get(OPENCOURSE_NOTEBOOK_TREE.format(
            jupId=jupyted_id, path="/", timestamp=int(time.time())),
            headers=headers)

        return self._get_notebook_folder(
            OPENCOURSE_NOTEBOOK_TREE, jupyted_id, jupId=jupyted_id,
            path="/", timestamp=int(time.time()))

    def extract_links_from_notebook(self, notebook_id):

        try:
            authorizationId = self._extract_notebook_text(notebook_id)
            ret = self._get_notebook_json(notebook_id, authorizationId)
            return ret
        except requests.exceptions.HTTPError as exception:
            logging.error('Could not download notebook %s: %s',
                          notebook_id, exception)
            if is_debug_run():
                logging.exception(
                    'Could not download notebook %s: %s', notebook_id, exception)
            return None

    def extract_links_from_quiz(self, quiz_id):
        try:
            session_id = self._get_quiz_session_id(quiz_id)
            quiz_json = self._get_quiz_json(quiz_id, session_id)
            return self._convert_quiz_json_to_links(quiz_json, 'quiz')
        except requests.exceptions.HTTPError as exception:
            logging.error('Could not download quiz %s: %s', quiz_id, exception)
            if is_debug_run():
                logging.exception(
                    'Could not download quiz %s: %s', quiz_id, exception)
            return None

    def _convert_quiz_json_to_links(self, quiz_json, filename_suffix):
        markup = self._quiz_to_markup(quiz_json)
        html = self._markup_to_html(markup)

        supplement_links = {}
        instructions = (IN_MEMORY_MARKER + html, filename_suffix)
        extend_supplement_links(
            supplement_links, {IN_MEMORY_EXTENSION: [instructions]})
        return supplement_links

    def _get_exam_json(self, exam_id, session_id):
        headers = self._auth_headers_with_json()
        data = {"name": "getState", "argument": []}

        reply = get_page(self._session,
                         POST_OPENCOURSE_ONDEMAND_EXAM_SESSIONS_GET_STATE,
                         json=True,
                         post=True,
                         data=json.dumps(data),
                         headers=headers,
                         session_id=session_id)

        return reply['elements'][0]['result']

    def _get_exam_session_id(self, exam_id):
        headers = self._auth_headers_with_json()
        data = {'courseId': self._course_id, 'itemId': exam_id}

        _body, reply = post_page_and_reply(self._session,
                                           POST_OPENCOURSE_ONDEMAND_EXAM_SESSIONS,
                                           data=json.dumps(data),
                                           headers=headers)
        return reply.headers.get('X-Coursera-Id')

    def _get_quiz_json(self, quiz_id, session_id):
        headers = self._auth_headers_with_json()
        data = {"contentRequestBody": {"argument": []}}

        reply = get_page(self._session,
                         POST_OPENCOURSE_API_QUIZ_SESSION_GET_STATE,
                         json=True,
                         post=True,
                         data=json.dumps(data),
                         headers=headers,
                         user_id=self._user_id,
                         class_name=self._course_name,
                         quiz_id=quiz_id,
                         session_id=session_id)
        return reply['contentResponseBody']['return']

    def _get_quiz_session_id(self, quiz_id):
        headers = self._auth_headers_with_json()
        data = {"contentRequestBody": []}
        reply = get_page(self._session,
                         POST_OPENCOURSE_API_QUIZ_SESSION,
                         json=True,
                         post=True,
                         data=json.dumps(data),
                         headers=headers,
                         user_id=self._user_id,
                         class_name=self._course_name,
                         quiz_id=quiz_id)

        return reply['contentResponseBody']['session']['id']

    def _auth_headers_with_json(self):
        headers = prepare_auth_headers(self._session, include_cauth=True)
        headers.update({
            'Content-Type': 'application/json; charset=UTF-8'
        })
        return headers

    def extract_links_from_lecture(self, course_id,
                                   video_id, subtitle_language='en',
                                   resolution='540p'):
        """
        Return the download URLs of on-demand course video.

        @param video_id: Video ID.
        @type video_id: str

        @param subtitle_language: Subtitle language.
        @type subtitle_language: str

        @param resolution: Preferred video resolution.
        @type resolution: str

        @return: @see CourseraOnDemand._extract_links_from_text
        """
        try:
            links = self._extract_videos_and_subtitles_from_lecture(
                course_id, video_id, subtitle_language, resolution)

            assets = self._get_lecture_asset_ids(course_id, video_id)
            assets = self._normalize_assets(assets)
            extend_supplement_links(
                links, self._extract_links_from_lecture_assets(assets))

            return links
        except requests.exceptions.HTTPError as exception:
            logging.error('Could not download lecture %s: %s',
                          video_id, exception)
            if is_debug_run():
                logging.exception(
                    'Could not download lecture %s: %s', video_id, exception)
            return None

    def _get_lecture_asset_ids(self, course_id, video_id):
        """
        Obtain a list of asset ids from a lecture.
        """
        dom = get_page(self._session, OPENCOURSE_ONDEMAND_LECTURE_ASSETS_URL,
                       json=True, course_id=course_id, video_id=video_id)
        # Note that we extract here "id", not definition -> assetId, as it
        # be extracted later.
        return [asset['id']
                for asset in dom['linked']['openCourseAssets.v1']]

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
            filename, extension = os.path.splitext(clean_url(name))
            if extension is '':
                return

            extension = clean_filename(
                extension.lower().strip('.').strip(),
                self._unrestricted_filenames)
            basename = clean_filename(
                os.path.basename(filename),
                self._unrestricted_filenames)
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
        use AssetRetriever to extract `asset` element types.

        @param asset_id: Asset ID.
        @type asset_id: str

        @return List of dictionaries with asset file names and urls.
        @rtype [{
            'name': '<filename.ext>'
            'url': '<url>'
        }]
        """
        dom = get_page(self._session, OPENCOURSE_ASSETS_URL,
                       json=True, id=asset_id)
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
                for asset in self._asset_retriever([open_course_asset_id],
                                                   download=False):
                    urls.append({'name': asset.name, 'url': asset.url})

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

    def _extract_videos_and_subtitles_from_lecture(self,
                                                   course_id,
                                                   video_id,
                                                   subtitle_language='en',
                                                   resolution='540p'):

        logging.debug('Parsing JSON for video_id <%s>.', video_id)

        dom = get_page(self._session, OPENCOURSE_ONDEMAND_LECTURE_VIDEOS_URL,
                       json=True,
                       course_id=course_id,
                       video_id=video_id)
        dom = dom['linked']['onDemandVideos.v1'][0]

        videos = VideosV1.from_json(dom)
        video_content = {}

        if resolution in videos:
            source = videos[resolution]
            logging.debug('Proceeding with download of resolution %s of <%s>.',
                          resolution, video_id)
        else:
            source = videos.get_best()
            logging.warning(
                'Requested resolution %s not available for <%s>. '
                'Downloading highest resolution (%s) available instead.',
                resolution, video_id, source.resolution)

        video_content['mp4'] = source.mp4_video_url

        subtitle_link = self._extract_subtitles_from_video_dom(
            dom, subtitle_language, video_id)

        for key, value in iteritems(subtitle_link):
            video_content[key] = value

        lecture_video_content = {}
        for key, value in iteritems(video_content):
            lecture_video_content[key] = [(value, '')]

        return lecture_video_content

    def _extract_subtitles_from_video_dom(self, video_dom,
                                          subtitle_language, video_id):
        # subtitles and transcripts
        subtitle_nodes = [
            ('subtitles', 'srt', 'subtitle'),
            ('subtitlesTxt', 'txt', 'transcript'),
        ]
        subtitle_set_download = set()
        subtitle_set_nonexist = set()
        subtitle_links = {}
        for (subtitle_node, subtitle_extension, subtitle_description) \
                in subtitle_nodes:
            logging.debug('Gathering %s URLs for video_id <%s>.',
                          subtitle_description, video_id)
            subtitles = video_dom.get(subtitle_node)
            download_all_subtitle = False
            if subtitles is not None:
                subtitles_set = set(subtitles)
                requested_subtitle_list = [s.strip() for s in
                                           subtitle_language.split(",")]
                for language_with_alts in requested_subtitle_list:
                    if download_all_subtitle:
                        break
                    grouped_language_list = [l.strip() for l in
                                             language_with_alts.split("|")]
                    for language in grouped_language_list:
                        if language == "all":
                            download_all_subtitle = True
                            break
                        elif language in subtitles_set:
                            subtitle_set_download.update([language])
                            break
                        else:
                            subtitle_set_nonexist.update([language])

            if download_all_subtitle and subtitles is not None:
                subtitle_set_download = set(subtitles)

            if not download_all_subtitle and subtitle_set_nonexist:
                logging.warning("%s unavailable in '%s' language for video "
                                "with video id: [%s],"
                                "%s", subtitle_description.capitalize(),
                                ", ".join(subtitle_set_nonexist), video_id,
                                subtitle_description)
            if not subtitle_set_download:
                logging.warning("%s all requested subtitles are unavailable,"
                                "with video id: [%s], falling back to 'en' "
                                "%s", subtitle_description.capitalize(),
                                video_id,
                                subtitle_description)
                subtitle_set_download = set(['en'])

            for current_subtitle_language in subtitle_set_download:
                subtitle_url = subtitles.get(current_subtitle_language)
                if subtitle_url is not None:
                    # some subtitle urls are relative!
                    subtitle_links[
                        "%s.%s" % (current_subtitle_language,
                                   subtitle_extension)
                    ] = make_coursera_absolute_url(subtitle_url)
        return subtitle_links

    def extract_links_from_programming_immediate_instructions(self, element_id):
        """
        Return a dictionary with links to supplement files (pdf, csv, zip,
        ipynb, html and so on) extracted from graded programming assignment.

        @param element_id: Element ID to extract files from.
        @type element_id: str

        @return: @see CourseraOnDemand._extract_links_from_text
        """
        logging.debug('Extracting links from programming immediate '
                      'instructions for element_id <%s>.', element_id)

        try:
            # Assignment text (instructions) contains asset tags which describe
            # supplementary files.
            text = ''.join(
                self._extract_programming_immediate_instructions_text(element_id))
            if not text:
                return {}

            supplement_links = self._extract_links_from_text(text)
            instructions = (IN_MEMORY_MARKER + self._markup_to_html(text),
                            'instructions')
            extend_supplement_links(
                supplement_links, {IN_MEMORY_EXTENSION: [instructions]})
            return supplement_links
        except requests.exceptions.HTTPError as exception:
            logging.error('Could not download programming assignment %s: %s',
                          element_id, exception)
            if is_debug_run():
                logging.exception('Could not download programming assignment %s: %s',
                                  element_id, exception)
            return None

    def extract_links_from_programming(self, element_id):
        """
        Return a dictionary with links to supplement files (pdf, csv, zip,
        ipynb, html and so on) extracted from graded programming assignment.

        @param element_id: Element ID to extract files from.
        @type element_id: str

        @return: @see CourseraOnDemand._extract_links_from_text
        """
        logging.debug(
            'Gathering supplement URLs for element_id <%s>.', element_id)

        try:
            # Assignment text (instructions) contains asset tags which describe
            # supplementary files.
            text = ''.join(self._extract_assignment_text(element_id))
            if not text:
                return {}

            supplement_links = self._extract_links_from_text(text)
            instructions = (IN_MEMORY_MARKER + self._markup_to_html(text),
                            'instructions')
            extend_supplement_links(
                supplement_links, {IN_MEMORY_EXTENSION: [instructions]})
            return supplement_links
        except requests.exceptions.HTTPError as exception:
            logging.error('Could not download programming assignment %s: %s',
                          element_id, exception)
            if is_debug_run():
                logging.exception('Could not download programming assignment %s: %s',
                                  element_id, exception)
            return None

    def extract_links_from_peer_assignment(self, element_id):
        """
        Return a dictionary with links to supplement files (pdf, csv, zip,
        ipynb, html and so on) extracted from peer assignment.

        @param element_id: Element ID to extract files from.
        @type element_id: str

        @return: @see CourseraOnDemand._extract_links_from_text
        """
        logging.debug(
            'Gathering supplement URLs for element_id <%s>.', element_id)

        try:
            # Assignment text (instructions) contains asset tags which describe
            # supplementary files.
            text = ''.join(self._extract_peer_assignment_text(element_id))
            if not text:
                return {}

            supplement_links = self._extract_links_from_text(text)
            instructions = (IN_MEMORY_MARKER + self._markup_to_html(text),
                            'peer_assignment_instructions')
            extend_supplement_links(
                supplement_links, {IN_MEMORY_EXTENSION: [instructions]})
            return supplement_links
        except requests.exceptions.HTTPError as exception:
            logging.error('Could not download peer assignment %s: %s',
                          element_id, exception)
            if is_debug_run():
                logging.exception('Could not download peer assignment %s: %s',
                                  element_id, exception)
            return None

    def extract_links_from_supplement(self, element_id):
        """
        Return a dictionary with supplement files (pdf, csv, zip, ipynb, html
        and so on) extracted from supplement page.

        @return: @see CourseraOnDemand._extract_links_from_text
        """
        logging.debug(
            'Gathering supplement URLs for element_id <%s>.', element_id)

        try:
            dom = get_page(self._session, OPENCOURSE_SUPPLEMENT_URL,
                           json=True,
                           course_id=self._course_id,
                           element_id=element_id)

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

                instructions = (IN_MEMORY_MARKER + self._markup_to_html(value),
                                'instructions')
                extend_supplement_links(
                    supplement_content, {IN_MEMORY_EXTENSION: [instructions]})

            return supplement_content
        except requests.exceptions.HTTPError as exception:
            logging.error('Could not download supplement %s: %s',
                          element_id, exception)
            if is_debug_run():
                logging.exception('Could not download supplement %s: %s',
                                  element_id, exception)
            return None

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
        dom = get_page(self._session, OPENCOURSE_ASSET_URL,
                       json=True,
                       ids=quote_plus(','.join(asset_ids)))

        return [{'id': element['id'],
                 'url': element['url'].strip()}
                for element in dom['elements']]

    def extract_references_poll(self):
        try:
            dom = get_page(self._session,
                           OPENCOURSE_REFERENCES_POLL_URL.format(
                               course_id=self._course_id),
                           json=True
                           )
            logging.info('Downloaded resource poll (%d bytes)', len(dom))
            return dom['elements']

        except requests.exceptions.HTTPError as exception:
            logging.error('Could not download resource section: %s',
                          exception)
            if is_debug_run():
                logging.exception('Could not download resource section: %s',
                                  exception)
            return None

    def extract_links_from_reference(self, short_id):
        """
        Return a dictionary with supplement files (pdf, csv, zip, ipynb, html
        and so on) extracted from supplement page.

        @return: @see CourseraOnDemand._extract_links_from_text
        """
        logging.debug('Gathering resource URLs for short_id <%s>.', short_id)

        try:
            dom = get_page(self._session, OPENCOURSE_REFERENCE_ITEM_URL,
                           json=True,
                           course_id=self._course_id,
                           short_id=short_id)

            resource_content = {}

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
                    resource_content, self._extract_links_from_text(value))

                instructions = (IN_MEMORY_MARKER + self._markup_to_html(value),
                                'resources')
                extend_supplement_links(
                    resource_content, {IN_MEMORY_EXTENSION: [instructions]})

            return resource_content
        except requests.exceptions.HTTPError as exception:
            logging.error('Could not download supplement %s: %s',
                          short_id, exception)
            if is_debug_run():
                logging.exception('Could not download supplement %s: %s',
                                  short_id, exception)
            return None

    def _extract_programming_immediate_instructions_text(self, element_id):
        """
        Extract assignment text (instructions).

        @param element_id: Element id to extract assignment instructions from.
        @type element_id: str

        @return: List of assignment text (instructions).
        @rtype: [str]
        """
        dom = get_page(self._session, OPENCOURSE_PROGRAMMING_IMMEDIATE_INSTRUCTIOINS_URL,
                       json=True,
                       course_id=self._course_id,
                       element_id=element_id)

        return [element['assignmentInstructions']['definition']['value']
                for element in dom['elements']]

    def _extract_notebook_text(self, element_id):
        """
        Extract notebook text (instructions).

        @param element_id: Element id to extract notebook links.
        @type element_id: str

        @return: Notebook URL.
        @rtype: [str]
        """
        headers = self._auth_headers_with_json()
        data = {'courseId': self._course_id,
                'learnerId': self._user_id, 'itemId': element_id}
        dom = get_page(self._session, OPENCOURSE_NOTEBOOK_LAUNCHES,
                       post=True,
                       json=True,
                       user_id=self._user_id,
                       course_id=self._course_id,
                       headers=headers,
                       element_id=element_id,
                       data=json.dumps(data)
                       )

        # Return authorization id. This id changes on each request
        return dom['elements'][0]['authorizationId']

    def _extract_assignment_text(self, element_id):
        """
        Extract assignment text (instructions).

        @param element_id: Element id to extract assignment instructions from.
        @type element_id: str

        @return: List of assignment text (instructions).
        @rtype: [str]
        """
        dom = get_page(self._session, OPENCOURSE_PROGRAMMING_ASSIGNMENTS_URL,
                       json=True,
                       course_id=self._course_id,
                       element_id=element_id)

        return [element['submissionLearnerSchema']['definition']
                ['assignmentInstructions']['definition']['value']
                for element in dom['elements']]

    def _extract_peer_assignment_text(self, element_id):
        """
        Extract peer assignment text (instructions).

        @param element_id: Element id to extract peer assignment instructions from.
        @type element_id: str

        @return: List of peer assignment text (instructions).
        @rtype: [str]
        """
        dom = get_page(self._session, OPENCOURSE_PEER_ASSIGNMENT_INSTRUCTIONS,
                       json=True,
                       user_id=self._user_id,
                       course_id=self._course_id,
                       element_id=element_id)

        result = []

        for element in dom['elements']:
            # There is only one section with Instructions
            if 'introduction' in element['instructions']:
                try:
                    result.append(element['instructions']
                                  ['introduction']['definition']['value'])
                except Exception as e:
                    result.append(element['instructions']
                                  ['introduction']['definition'])

            # But there may be multiple sections in Sections
            for section in element['instructions'].get('sections', []):
                try:
                    section_value = section['content']['definition']['value']
                except Exception as e:
                    section_value = section['content']['definition']
                section_title = section.get('title')
                if section_title is not None:
                    # If section title is present, put it in the beginning of
                    # section value as if it was there.
                    section_value = ('<heading level="3">%s</heading>' %
                                     section_title) + section_value
                result.append(section_value)

        return result

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
            title = clean_filename(
                asset_tags_map[asset['id']]['name'],
                self._unrestricted_filenames)
            extension = clean_filename(
                asset_tags_map[asset['id']]['extension'].strip(),
                self._unrestricted_filenames)
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
            extension = clean_filename(
                extension.lower().strip('.').strip(),
                self._unrestricted_filenames)
            basename = clean_filename(
                os.path.basename(filename),
                self._unrestricted_filenames)
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
