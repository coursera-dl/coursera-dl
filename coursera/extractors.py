"""
This module contains implementation for extractors. Extractors know how
to parse site of MOOC platform and return a list of modules to download.
Usually they do not download heavy content, except when necessary
to parse course syllabus.
"""

import abc
import json
import logging

from .api import CourseraOnDemand, OnDemandCourseMaterialItems
from .define import OPENCOURSE_CONTENT_URL
from .cookies import login
from .network import get_page
from .utils import is_debug_run


class PlatformExtractor(object):
    __metaclass__ = abc.ABCMeta

    def get_modules(self):
        """
        Get course modules.
        """
        pass


class CourseraExtractor(PlatformExtractor):
    def __init__(self, session, username, password):
        login(session, username, password)

        self._session = session

    def list_courses(self):
        """
        List enrolled courses.

        @return: List of enrolled courses.
        @rtype: [str]
        """
        course = CourseraOnDemand(session=self._session, course_id=None)
        return course.list_courses()

    def get_modules(self, class_name,
                    reverse=False, unrestricted_filenames=False,
                    subtitle_language='en', video_resolution=None):

        page = self._get_on_demand_syllabus(class_name)
        modules = self._parse_on_demand_syllabus(
            page, reverse, unrestricted_filenames,
            subtitle_language, video_resolution)
        return modules

    def _get_on_demand_syllabus(self, class_name):
        """
        Get the on-demand course listing webpage.
        """

        url = OPENCOURSE_CONTENT_URL.format(class_name=class_name)
        page = get_page(self._session, url)
        logging.info('Downloaded %s (%d bytes)', url, len(page))

        return page

    def _parse_on_demand_syllabus(self, page, reverse=False,
                                  unrestricted_filenames=False,
                                  subtitle_language='en',
                                  video_resolution=None):
        """
        Parse a Coursera on-demand course listing/syllabus page.
        """

        dom = json.loads(page)
        course_name = dom['slug']

        logging.info('Parsing syllabus of on-demand course. '
                     'This may take some time, please be patient ...')
        modules = []
        json_modules = dom['courseMaterial']['elements']
        course = CourseraOnDemand(session=self._session, course_id=dom['id'],
                                  course_name=course_name,
                                  unrestricted_filenames=unrestricted_filenames)
        course.obtain_user_id()
        ondemand_material_items = OnDemandCourseMaterialItems.create(
            session=self._session, course_name=course_name)

        if is_debug_run():
            with open('%s-syllabus-raw.json' % course_name, 'w') as file_object:
                json.dump(dom, file_object, indent=4)
            with open('%s-course-material-items.json' % course_name, 'w') as file_object:
                json.dump(ondemand_material_items._items, file_object, indent=4)

        for module in json_modules:
            module_slug = module['slug']
            logging.info('Processing module  %s', module_slug)
            sections = []
            json_sections = module['elements']
            for section in json_sections:
                section_slug = section['slug']
                logging.info('Processing section     %s', section_slug)
                lectures = []
                json_lectures = section['elements']

                # Certain modules may be empty-looking programming assignments
                # e.g. in data-structures, algorithms-on-graphs ondemand courses
                if not json_lectures:
                    lesson_id = section['id']
                    lecture = ondemand_material_items.get(lesson_id)
                    if lecture is not None:
                        json_lectures = [lecture]

                for lecture in json_lectures:
                    lecture_slug = lecture['slug']
                    typename = lecture['content']['typeName']

                    logging.info('Processing lecture         %s (%s)',
                                 lecture_slug, typename)
                    links = None

                    if typename == 'lecture':
                        lecture_video_id = lecture['content']['definition']['videoId']
                        assets = lecture['content']['definition'].get('assets', [])

                        links = course.extract_links_from_lecture(
                            lecture_video_id, subtitle_language,
                            video_resolution, assets)

                    elif typename == 'supplement':
                        links = course.extract_links_from_supplement(
                            lecture['id'])

                    elif typename in ('gradedProgramming', 'ungradedProgramming'):
                        links = course.extract_links_from_programming(lecture['id'])

                    elif typename == 'quiz':
                        links = course.extract_links_from_quiz(lecture['id'])

                    elif typename == 'exam':
                        links = course.extract_links_from_exam(lecture['id'])

                    if links:
                        lectures.append((lecture_slug, links))

                if lectures:
                    sections.append((section_slug, lectures))

            if sections:
                modules.append((module_slug, sections))

        if modules and reverse:
            modules.reverse()

        return modules
