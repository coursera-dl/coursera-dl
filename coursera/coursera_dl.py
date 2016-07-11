#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Authors and copyright:
#     © 2012-2013, John Lehmann (first last at geemail dotcom or @jplehmann)
#     © 2012-2015, Rogério Brito (r lastname at ime usp br)
#     © 2013, Jonas De Taeye (first dt at fastmail fm)
#
# Contributions are welcome, but please add new unit tests to test your changes
# and/or features.  Also, please try to make changes platform independent and
# backward compatible.
#
# Legalese:
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your
#  option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Module for downloading lecture resources such as videos for Coursera classes.

Given a class name, username and password, it scrapes the course listing
page to get the section (week) and lecture names, and then downloads the
related materials into appropriately named files and directories.

Examples:
  coursera-dl -u <user> -p <passwd> saas
  coursera-dl -u <user> -p <passwd> -l listing.html -o saas --skip-download

For further documentation and examples, visit the project's home at:
  https://github.com/coursera-dl/coursera
"""


import json
import logging
import os
import re
import shutil

from distutils.version import LooseVersion as V


# Test versions of some critical modules.
# We may, perhaps, want to move these elsewhere.
import bs4
import six
import requests

from .cookies import (
    AuthenticationFailed, ClassNotFound,
    get_cookies_for_class, make_cookie_values, TLSAdapter)
from .define import (CLASS_URL, ABOUT_URL, PATH_CACHE)
from .downloaders import get_downloader
from .workflow import CourseraDownloader
from .utils import (clean_filename, get_anchor_format, mkdir_p, fix_url,
                    print_ssl_error_message,
                    decode_input, BeautifulSoup, is_debug_run)

from .network import get_page, get_page_and_url
from .commandline import parse_args
from .extractors import CourseraExtractor

from coursera import __version__


# URL containing information about outdated modules
_SEE_URL = " See https://github.com/coursera-dl/coursera/issues/139"

assert V(requests.__version__) >= V('2.4'), "Upgrade requests!" + _SEE_URL
assert V(six.__version__) >= V('1.5'), "Upgrade six!" + _SEE_URL
assert V(bs4.__version__) >= V('4.1'), "Upgrade bs4!" + _SEE_URL


def get_syllabus_url(class_name, preview):
    """
    Return the Coursera index/syllabus URL.

    The returned result depends on if we want to only use a preview page or
    if we are enrolled in the course.
    """
    class_type = 'preview' if preview else 'index'
    page = CLASS_URL.format(class_name=class_name) + '/lecture/' + class_type
    logging.debug('Using %s mode with page: %s', class_type, page)

    return page


def get_session():
    """
    Create a session with TLS v1.2 certificate.
    """

    session = requests.Session()
    session.mount('https://', TLSAdapter())

    return session


def grab_hidden_video_url(session, href):
    """
    Follow some extra redirects to grab hidden video URLs.

    The first of these "hidden" videos were seen in courses from the
    University of Washington, but others appeared after that (like in the
    course Social Psychology).
    """
    try:
        page = get_page(session, href)
    except requests.exceptions.HTTPError:
        return None

    soup = BeautifulSoup(page)
    l = soup.find('source', attrs={'type': 'video/mp4'})
    if l is not None:
        return l['src']
    else:
        return None


def get_old_style_syllabus(session, class_name, local_page=False, preview=False):
    """
    Get the old style course listing webpage.

    If we are instructed to use a local page and it already exists, then
    that page is used instead of performing a download.  If we are
    instructed to use a local page and it does not exist, then we download
    the page and save a copy of it for future use.
    """

    if not (local_page and os.path.exists(local_page)):
        url = get_syllabus_url(class_name, preview)
        page, final_url = get_page_and_url(session, url)
        logging.info('Downloaded %s (%d bytes)', url, len(page))

        if "/learn/" in final_url:
            # got redirected to a on-demand course page,
            # abort and let on_demand download run
            raise ClassNotFound

        # cache the page if we're in 'local' mode
        if local_page:
            with open(local_page, 'w') as f:
                f.write(page.encode("utf-8"))
    else:
        with open(local_page) as f:
            page = decode_input(f.read())
        logging.info('Read (%d bytes) from local file', len(page))

    return page


def transform_preview_url(a):
    """
    Given a preview lecture URL, transform it into a regular video URL.

    If the given URL is not a preview URL, we simply return None.
    """

    # Example URLs
    # "https://class.coursera.org/modelthinking/lecture/preview_view/8"
    # "https://class.coursera.org/nlp/lecture/preview_view?lecture_id=124"
    mobj = re.search(r'preview_view/(\d+)$', a)
    if mobj:
        return re.sub(r'preview_view/(\d+)$', r'preview_view?lecture_id=\1', a)
    else:
        return None


def get_old_style_video(session, url):
    """
    Parse a old style Coursera video page.
    """

    page = get_page(session, url)
    soup = BeautifulSoup(page)
    return soup.find(attrs={'type': re.compile('^video/mp4')})['src']


def parse_old_style_syllabus(session, page, reverse=False, unrestricted_filenames=False,
                             subtitle_language='en'):
    """
    Parse an old style Coursera course listing/syllabus page.

    Each section is a week of classes.
    """

    sections = []
    soup = BeautifulSoup(page)

    # traverse sections
    stags = soup.findAll(attrs={'class': re.compile('^course-item-list-header')})
    for stag in stags:
        assert stag.contents[0] is not None, "couldn't find section"
        untouched_fname = stag.contents[0].contents[1]
        section_name = clean_filename(untouched_fname, unrestricted_filenames)
        logging.info(section_name)
        lectures = []  # resources for 1 lecture

        # traverse resources (e.g., video, ppt, ..)
        for vtag in stag.nextSibling.findAll('li'):
            assert vtag.a.contents[0], "couldn't get lecture name"
            untouched_fname = vtag.a.contents[0]
            vname = clean_filename(untouched_fname, unrestricted_filenames)
            logging.info('  %s', vname)
            lecture = {}
            lecture_page = None

            for a in vtag.findAll('a'):
                href = fix_url(a['href'])
                untouched_fname = a.get('title', '')
                title = clean_filename(untouched_fname, unrestricted_filenames)
                fmt = get_anchor_format(href)
                if fmt in ('srt', 'txt') and subtitle_language != 'en':
                    title = title.replace('_en&format', '_' + subtitle_language + '&format')
                    href = href.replace('_en&format', '_' + subtitle_language + '&format')

                logging.debug('    %s %s', fmt, href)
                if fmt:
                    lecture[fmt] = lecture.get(fmt, [])
                    lecture[fmt].append((href, title))
                    continue

                # Special case: find preview URLs
                lecture_page = transform_preview_url(href)
                if lecture_page:
                    try:
                        href = get_old_style_video(session, lecture_page)
                        lecture['mp4'] = lecture.get('mp4', [])
                        lecture['mp4'].append((fix_url(href), ''))
                    except TypeError:
                        logging.warning(
                            'Could not get resource: %s', lecture_page)

            # Special case: we possibly have hidden video links---thanks to
            # the University of Washington for that.
            if 'mp4' not in lecture:
                for a in vtag.findAll('a'):
                    if a.get('data-modal-iframe'):
                        href = grab_hidden_video_url(
                            session, a['data-modal-iframe'])
                        href = fix_url(href)
                        fmt = 'mp4'
                        logging.debug('    %s %s', fmt, href)
                        if href is not None:
                            lecture[fmt] = lecture.get(fmt, [])
                            lecture[fmt].append((href, ''))

            for fmt in lecture:
                count = len(lecture[fmt])
                for i, r in enumerate(lecture[fmt]):
                    if count == i + 1:
                        # for backward compatibility, we do not add the title
                        # to the filename (format_combine_number_resource and
                        # format_resource)
                        lecture[fmt][i] = (r[0], '')
                    else:
                        # make sure the title is unique
                        lecture[fmt][i] = (r[0], '{0:d}_{1}'.format(i, r[1]))

            lectures.append((vname, lecture))

        sections.append((section_name, lectures))

    logging.info('Found %d sections and %d lectures on this page',
                 len(sections), sum(len(s[1]) for s in sections))

    if sections and reverse:
        sections.reverse()

    if not len(sections):
        logging.error('The cookies file may be invalid, '
                      'please re-run with the `--clear-cache` option.')

    return sections


def download_about(session, class_name, path='', overwrite=False,
                   subtitle_language='en'):
    """
    Download the 'about' metadata which is in JSON format and pretty-print it.
    """
    about_fn = os.path.join(path, class_name + '-about.json')
    logging.debug('About file to be written to: %s', about_fn)
    if os.path.exists(about_fn) and not overwrite and subtitle_language == 'en':
        return

    # strip off course number on end e.g. ml-001 -> ml
    base_class_name = class_name.split('-')[0]

    about_url = ABOUT_URL.format(class_name=base_class_name)
    logging.debug('About url: %s', about_url)

    # NOTE: should we create a directory with metadata?
    logging.info('Downloading about page from: %s', about_url)
    about_json = get_page(session, about_url)
    data = json.loads(about_json)["elements"]

    for element in data:
        if element["shortName"] == base_class_name:
            with open(about_fn, 'w') as about_file:
                json_data = json.dumps(element, indent=4,
                                       separators=(',', ':'))
                about_file.write(json_data)
                return element

def download_old_style_class(args, class_name):
    """
    Download all requested resources from the class given in class_name.
    Old style classes are classes located at class.coursera.org.
    Read more about course types here:
    https://learner.coursera.help/hc/en-us/articles/203879739-Course-Types

    Returns True if the class appears completed.
    """
    session = get_session()

    if args.preview:
        # Todo, remove this.
        session.cookie_values = 'dummy=dummy'
    else:
        get_cookies_for_class(session,
                              class_name,
                              cookies_file=args.cookies_file,
                              username=args.username, password=args.password)
        session.cookie_values = make_cookie_values(session.cookies, class_name)

    subtitle_language = args.subtitle_language
    if args.about or args.subtitle_language != 'en':
        try:
            about = download_about(session,
                                   class_name,
                                   args.path,
                                   args.overwrite,
                                   args.subtitle_language)
            # Check if subtitle is available
            if not about or not about["subtitleLanguagesCsv"].split(',').count(args.subtitle_language):
                logging.warning("Subtitle unavailable in specified language")
                subtitle_language = "en"
        except requests.exceptions.HTTPError as e:
            logging.info('Could not download about page, falling back to English subtitles')
            subtitle_language = "en"

    # get the syllabus listing
    page = get_old_style_syllabus(session, class_name,
                                  args.local_page, args.preview)

    # parse it
    sections = parse_old_style_syllabus(session, page, args.reverse,
                                        args.unrestricted_filenames, subtitle_language)

    downloader = get_downloader(session, class_name, args)

    ignored_formats = []
    if args.ignore_formats:
        ignored_formats = args.ignore_formats.split(",")

    skipped_urls = []
    failed_urls = []

    # obtain the resources
    completed = download_lectures(downloader,
                                  class_name,
                                  sections,
                                  args.file_formats,
                                  args.overwrite,
                                  args.skip_download,
                                  args.section_filter,
                                  args.lecture_filter,
                                  args.resource_filter,
                                  args.path,
                                  args.verbose_dirs,
                                  args.preview,
                                  args.combined_section_lectures_nums,
                                  args.hooks,
                                  args.playlist,
                                  args.unrestricted_filenames,
                                  ignored_formats,
                                  args.resume,
                                  None if args.disable_url_skipping else skipped_urls,
                                  failed_urls,
                                  args.video_resolution)

    if skipped_urls:
        print_skipped_urls(skipped_urls)
    if failed_urls:
        print_failed_urls(failed_urls)

    return completed


def list_courses(args):
    """
    List enrolled courses.

    @param args: Command-line arguments.
    @type args: namedtuple
    """
    session = get_session()
    extractor = CourseraExtractor(session, args.username, args.password)
    courses = extractor.list_courses()
    logging.info('Found %d courses', len(courses))
    for course in courses:
        logging.info(course)


def download_on_demand_class(args, class_name):
    """
    Download all requested resources from the on-demand class given in class_name.

    Returns True if the class appears completed.
    """

    session = get_session()
    extractor = CourseraExtractor(session, args.username, args.password)

    modules = extractor.get_modules(class_name,
                                    args.reverse,
                                    args.unrestricted_filenames,
                                    args.subtitle_language,
                                    args.video_resolution)

    if is_debug_run():
        with open('%s-syllabus-parsed.json' % class_name, 'w') as file_object:
            json.dump(modules, file_object, indent=4)

    downloader = get_downloader(session, class_name, args)

    # obtain the resources

    ignored_formats = []
    if args.ignore_formats:
        ignored_formats = args.ignore_formats.split(",")

    course_downloader = CourseraDownloader(
        downloader,
        commandline_args=args,
        class_name=class_name,
        path=args.path,
        ignored_formats=ignored_formats,
        disable_url_skipping=args.disable_url_skipping
    )

    completed = course_downloader.download_modules(modules)

    # Print skipped URLs if any
    if course_downloader.skipped_urls:
        print_skipped_urls(course_downloader.skipped_urls)

    # Print failed URLs if any
    # FIXME: should we set non-zero exit code if we have failed URLs?
    if course_downloader.failed_urls:
        print_failed_urls(course_downloader.failed_urls)

    return completed


def print_skipped_urls(skipped_urls):
    logging.info('The following URLs (%d) have been skipped and not '
                 'downloaded:', len(skipped_urls))
    logging.info('(if you want to download these URLs anyway, please '
                 'add "--disable-url-skipping" option)')
    logging.info('-' * 80)
    for url in skipped_urls:
        logging.info(url)
    logging.info('-' * 80)


def print_failed_urls(failed_urls):
    logging.info('The following URLs (%d) could not be downloaded:',
                 len(failed_urls))
    logging.info('-' * 80)
    for url in failed_urls:
        logging.info(url)
    logging.info('-' * 80)


def download_class(args, class_name):
    """
    Try to download on-demand class.

    Returns True if the class appears completed.
    """
    logging.debug('Downloading new style (on demand) class %s', class_name)
    return download_on_demand_class(args, class_name)


def main():
    """
    Main entry point for execution as a program (instead of as a module).
    """

    args = parse_args()
    logging.info('coursera_dl version %s', __version__)
    completed_classes = []

    mkdir_p(PATH_CACHE, 0o700)
    if args.clear_cache:
        shutil.rmtree(PATH_CACHE)
    if args.on_demand:
        logging.warning('--on-demand option is deprecated and is not required'
                        ' anymore. Do not use this option. It will be removed'
                        ' in the future.')
    if args.list_courses:
        logging.info('Listing enrolled courses')
        list_courses(args)
        return

    for class_name in args.class_names:
        try:
            logging.info('Downloading class: %s', class_name)
            if download_class(args, class_name):
                completed_classes.append(class_name)
        except requests.exceptions.HTTPError as e:
            logging.error('HTTPError %s', e)
        except requests.exceptions.SSLError as e:
            logging.error('SSLError %s', e)
            print_ssl_error_message(e)
            if is_debug_run():
                raise
        except ClassNotFound as cnf:
            logging.error('Could not find class: %s', cnf)
        except AuthenticationFailed as af:
            logging.error('Could not authenticate: %s', af)

    if completed_classes:
        logging.info(
            "Classes which appear completed: " + " ".join(completed_classes))


if __name__ == '__main__':
    main()
