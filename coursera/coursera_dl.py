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


import argparse
import datetime
import glob
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import codecs

from distutils.version import LooseVersion as V


# Test versions of some critical modules.
# We may, perhaps, want to move these elsewhere.
import bs4
import six
from six import iteritems
import requests

from .cookies import (
    AuthenticationFailed, ClassNotFound,
    get_cookies_for_class, make_cookie_values, login, TLSAdapter)
from .credentials import get_credentials, CredentialsError, keyring
from .define import (CLASS_URL, ABOUT_URL, PATH_CACHE,
                     OPENCOURSE_CONTENT_URL, IN_MEMORY_MARKER)
from .downloaders import get_downloader
from .utils import (clean_filename, get_anchor_format, mkdir_p, fix_url,
                    print_ssl_error_message, normalize_path,
                    decode_input, BeautifulSoup, is_debug_run)

from .network import get_page, get_page_and_url
from .api import CourseraOnDemand, OnDemandCourseMaterialItems
from .filter import skip_format_url

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


def get_on_demand_syllabus(session, class_name):
    """
    Get the on-demand course listing webpage.
    """

    url = OPENCOURSE_CONTENT_URL.format(class_name=class_name)
    page = get_page(session, url)
    logging.info('Downloaded %s (%d bytes)', url, len(page))

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


def parse_on_demand_syllabus(session, page, reverse=False, unrestricted_filenames=False,
                             subtitle_language='en', video_resolution=None):
    """
    Parse a Coursera on-demand course listing/syllabus page.
    """

    dom = json.loads(page)
    course_name = dom['slug']

    logging.info('Parsing syllabus of on-demand course. '
                 'This may take some time, please be patient ...')
    modules = []
    json_modules = dom['courseMaterial']['elements']
    course = CourseraOnDemand(session=session, course_id=dom['id'],
                              unrestricted_filenames=unrestricted_filenames)
    ondemand_material_items = OnDemandCourseMaterialItems.create(
        session=session, course_name=course_name)

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

                logging.info('Processing lecture         %s', lecture_slug)

                if typename == 'lecture':
                    lecture_video_id = lecture['content']['definition']['videoId']
                    assets = lecture['content']['definition'].get('assets', [])

                    links = course.extract_links_from_lecture(
                        lecture_video_id, subtitle_language,
                        video_resolution, assets)

                    if links:
                        lectures.append((lecture_slug, links))

                elif typename == 'supplement':
                    supplement_content = course.extract_links_from_supplement(
                        lecture['id'])
                    if supplement_content:
                        lectures.append((lecture_slug, supplement_content))

                elif typename in ('gradedProgramming', 'ungradedProgramming'):
                    supplement_content = course.extract_links_from_programming(
                        lecture['id'])
                    if supplement_content:
                        lectures.append((lecture_slug, supplement_content))

            if lectures:
                sections.append((section_slug, lectures))

        if sections:
            modules.append((module_slug, sections))

    if modules and reverse:
        modules.reverse()

    return modules


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


def is_course_complete(last_update):
    """
    Determine is the course is likely to have been terminated or not.

    We return True if the timestamp given by last_update is 30 days or older
    than today's date.  Otherwise, we return True.

    The intended use case for this is to detect if a given courses has not
    seen any update in the last 30 days or more.  Otherwise, we return True,
    since it is probably too soon to declare the course complete.
    """
    rv = False
    if last_update >= 0:
        delta = time.time() - last_update
        max_delta = total_seconds(datetime.timedelta(days=30))
        if delta > max_delta:
            rv = True
    return rv


def format_section(num, section, class_name, verbose_dirs):
    sec = '%02d_%s' % (num, section)
    if verbose_dirs:
        sec = class_name.upper() + '_' + sec
    return sec


def format_resource(num, name, title, fmt):
    if title:
        title = '_' + title
    return '%02d_%s%s.%s' % (num, name, title, fmt)


def format_combine_number_resource(secnum, lecnum, lecname, title, fmt):
    if title:
        title = '_' + title
    return '%02d_%02d_%s%s.%s' % (secnum, lecnum, lecname, title, fmt)


def find_resources_to_get(lecture, file_formats, resource_filter, ignored_formats=None):
    """
    Select formats to download.
    """
    resources_to_get = []

    if ignored_formats is None:
        ignored_formats = []

    if len(ignored_formats):
        logging.info("The following file formats will be ignored: " + ",".join(ignored_formats))

    for fmt, resources in iteritems(lecture):

        fmt0 = fmt
        if '.' in fmt:
            fmt = fmt.split('.')[1]

        if fmt in ignored_formats:
            continue

        if fmt in file_formats or 'all' in file_formats:
            for r in resources:
                if resource_filter and r[1] and not re.search(resource_filter, r[1]):
                    logging.debug('Skipping b/c of rf: %s %s',
                                  resource_filter, r[1])
                    continue
                resources_to_get.append((fmt0, r[0], r[1]))
        else:
            logging.debug(
                'Skipping b/c format %s not in %s', fmt, file_formats)

    return resources_to_get


def create_m3u_playlist(section_dir):
    """
    Create M3U playlist with contents of `section_dir`/*.mp4. The playlist
    will be created in that directory.

    @param section_dir: Path where to scan for *.mp4 files.
    @type section_dir: str
    """
    path_to_return = os.getcwd()

    for (_path, subdirs, files) in os.walk(section_dir):
        os.chdir(_path)
        globbed_videos = sorted(glob.glob("*.mp4"))
        m3u_name = os.path.split(_path)[1] + ".m3u"

        if len(globbed_videos):
            with open(m3u_name, "w") as m3u:
                for video in globbed_videos:
                    m3u.write(video + "\n")
            os.chdir(path_to_return)
    os.chdir(path_to_return)


def handle_resource(downloader,
                    lecture_filename,
                    fmt,
                    url,
                    overwrite,
                    resume,
                    skip_download,
                    section_dir,
                    skipped_urls,
                    last_update):
    """
    Handle resource. This function builds up resource file name and
    downloads it if necessary.

    @param downloader: Resource downloader instance.
    @type downloader: downloaders.Downloader

    @param fmt: Format of the resource (pdf, csv, etc)
    @type fmt: str

    @param url: URL of the resource.
    @type url: str

    @param overwrite: Flag that indicates whether files should be overwritten.
    @type overwrite: bool

    @param resume: Flag that indicates whether download should be resumed.
    @type resume: bool

    @param skip_download: Flag that indicates whether download should be skipped.
    @type skip_download: bool

    @param section_dir: Path to current section directory.
    @type section_dir: str

    @param skipped_urls: List of skipped urls to update.
    @type skipped_urls: None or list

    @param last_update: Latest mtime across files.
    @type last_update: timestamp

    @return: Updated latest mtime.
    @rtype: timestamp
    """
    # Decide whether we need to download it
    if overwrite or not os.path.exists(lecture_filename) or resume:
        if not skip_download:
            if url.startswith(IN_MEMORY_MARKER):
                page_content = url[len(IN_MEMORY_MARKER):]
                logging.info('Saving page contents to: %s', lecture_filename)
                with codecs.open(lecture_filename, 'w', 'utf-8') as file_object:
                    file_object.write(page_content)
            else:
                if skipped_urls is not None and skip_format_url(fmt, url):
                    skipped_urls.append(url)
                else:
                    logging.info('Downloading: %s', lecture_filename)
                    downloader.download(url, lecture_filename, resume=resume)
        else:
            open(lecture_filename, 'w').close()  # touch
        last_update = time.time()
    else:
        logging.info('%s already downloaded', lecture_filename)
        # if this file hasn't been modified in a long time,
        # record that time
        last_update = max(last_update, os.path.getmtime(lecture_filename))

    return last_update


def get_lecture_filename(combined_section_lectures_nums,
                         section_dir,
                         secnum,
                         lecnum,
                         lecname,
                         title,
                         fmt):
    """
    Prepare a destination lecture filename.

    @param combined_section_lectures_nums: Flag that indicates whether
        section lectures should have combined numbering.
    @type combined_section_lectures_nums: bool

    @param section_dir: Path to current section directory.
    @type section_dir: str

    @param secnum: Section number.
    @type secnum: int

    @param lecnum: Lecture number.
    @type lecnum: int

    @param lecname: Lecture name.
    @type lecname: str

    @param title: Resource title.
    @type title: str

    @param fmt: Format of the resource (pdf, csv, etc)
    @type fmt: str

    @return: Lecture file name.
    @rtype: str
    """
    # Format lecture file name
    if combined_section_lectures_nums:
        lecture_filename = os.path.join(
            section_dir,
            format_combine_number_resource(
                secnum + 1, lecnum + 1, lecname, title, fmt))
    else:
        lecture_filename = os.path.join(
            section_dir, format_resource(lecnum + 1, lecname, title, fmt))

    return lecture_filename


def download_lectures(downloader,
                      class_name,
                      sections,
                      file_formats,
                      overwrite=False,
                      skip_download=False,
                      section_filter=None,
                      lecture_filter=None,
                      resource_filter=None,
                      path='',
                      verbose_dirs=False,
                      preview=False,
                      combined_section_lectures_nums=False,
                      hooks=None,
                      playlist=False,
                      unrestricted_filenames=False,
                      ignored_formats=None,
                      resume=False,
                      skipped_urls=None,
                      failed_urls=None,
                      video_resolution='540p'):
    """
    Download lecture resources described by sections.

    Returns True if the class appears completed, False otherwise.
    """
    last_update = -1

    for (secnum, (section, lectures)) in enumerate(sections):
        if section_filter and not re.search(section_filter, section):
            logging.debug('Skipping b/c of sf: %s %s', section_filter,
                          section)
            continue

        section_dir = os.path.join(
            path, class_name,
            format_section(secnum + 1, section, class_name, verbose_dirs))
        for (lecnum, (lecname, lecture)) in enumerate(lectures):
            if lecture_filter and not re.search(lecture_filter,
                                                lecname):
                logging.debug('Skipping b/c of lf: %s %s', lecture_filter,
                              lecname)
                continue

            if not os.path.exists(section_dir):
                mkdir_p(normalize_path(section_dir))

            resources_to_get = find_resources_to_get(lecture,
                                                     file_formats,
                                                     resource_filter,
                                                     ignored_formats)

            # write lecture resources
            for fmt, url, title in resources_to_get:
                lecture_filename = get_lecture_filename(
                    combined_section_lectures_nums,
                    section_dir, secnum, lecnum, lecname, title, fmt)

                lecture_filename = normalize_path(lecture_filename)

                try:
                    last_update = handle_resource(
                        downloader, lecture_filename, fmt, url,
                        overwrite, resume, skip_download,
                        section_dir, skipped_urls, last_update)
                except requests.exceptions.RequestException as e:
                    logging.error('The following error has occurred while '
                                  'downloading URL %s: %s', url, str(e))
                    if failed_urls is None:
                        logging.info('If you want to ignore HTTP errors, '
                                     'please use "--ignore-http-errors" option')
                        raise
                    else:
                        failed_urls.append(url)



        # After fetching resources, create a playlist in M3U format with the
        # videos downloaded.
        if playlist:
            create_m3u_playlist(section_dir)

        if hooks:
            for hook in hooks:
                logging.info('Running hook %s for section %s.', hook, section_dir)
                os.chdir(section_dir)
                subprocess.call(hook)

    # if we haven't updated any files in 1 month, we're probably
    # done with this course
    rv = is_course_complete(last_update)
    if rv:
        logging.info('COURSE PROBABLY COMPLETE: ' + class_name)

    return rv


def total_seconds(td):
    """
    Compute total seconds for a timedelta.

    Added for backward compatibility, pre 2.7.
    """
    return (td.microseconds +
            (td.seconds + td.days * 24 * 3600) * 10 ** 6) // 10 ** 6


def parse_args(args=None):
    """
    Parse the arguments/options passed to the program on the command line.
    """

    parser = argparse.ArgumentParser(
        description='Download Coursera.org lecture material and resources.')

    # Basic options
    group_basic = parser.add_argument_group('Basic options')

    group_basic.add_argument('class_names',
                             action='store',
                             nargs='+',
                             help='name(s) of the class(es) (e.g. "ml-005")')

    group_basic.add_argument('-u',
                             '--username',
                             dest='username',
                             action='store',
                             default=None,
                             help='coursera username')

    group_basic.add_argument('-p',
                             '--password',
                             dest='password',
                             action='store',
                             default=None,
                             help='coursera password')

    group_basic.add_argument('--on-demand', # FIXME: remove this option
                             dest='on_demand',
                             action='store_true',
                             default=False,
                             help='[DEPRECATED] get on-demand videos. Do not use'
                             ' this option, it is deprecated. The script will'
                             ' try to detect course type automatically.')

    group_basic.add_argument('-b',  # FIXME: kill this one-letter option
                             '--preview',
                             dest='preview',
                             action='store_true',
                             default=False,
                             help='get videos from preview pages. (Default: False)')

    group_basic.add_argument('--path',
                             dest='path',
                             action='store',
                             default='',
                             help='path to where to save the file. (Default: current directory)')

    group_basic.add_argument('-sl',  # FIXME: deprecate this option
                             '--subtitle-language',
                             dest='subtitle_language',
                             action='store',
                             default='all',
                             help='Choose language to download subtitles and transcripts. (Default: all)'
                             'Use special value "all" to download all available.')

    # Selection of material to download
    group_material = parser.add_argument_group('Selection of material to download')

    group_material.add_argument('--about',  # FIXME: should be --about-course
                                dest='about',
                                action='store_true',
                                default=False,
                                help='download "about" metadata. (Default: False)')

    group_material.add_argument('-f',
                                '--formats',
                                dest='file_formats',
                                action='store',
                                default='all',
                                help='file format extensions to be downloaded in'
                                ' quotes space separated, e.g. "mp4 pdf" '
                                '(default: special value "all")')

    group_material.add_argument('--ignore-formats',
                                dest='ignore_formats',
                                action='store',
                                default=None,
                                help='file format extensions of resources to ignore'
                                ' (default: None)')

    group_material.add_argument('-sf',  # FIXME: deprecate this option
                                '--section_filter',
                                dest='section_filter',
                                action='store',
                                default=None,
                                help='only download sections which contain this'
                                ' regex (default: disabled)')

    group_material.add_argument('-lf',  # FIXME: deprecate this option
                                '--lecture_filter',
                                dest='lecture_filter',
                                action='store',
                                default=None,
                                help='only download lectures which contain this regex'
                                ' (default: disabled)')

    group_material.add_argument('-rf',  # FIXME: deprecate this option
                                '--resource_filter',
                                dest='resource_filter',
                                action='store',
                                default=None,
                                help='only download resources which match this regex'
                                ' (default: disabled)')

    group_material.add_argument('--video-resolution',
                                dest='video_resolution',
                                action='store',
                                default='540p',
                                help='video resolution to download (default: 540p); '
                                'only valid for on-demand courses; '
                                'only values allowed: 360p, 540p, 720p')

    group_material.add_argument('--ignore-http-errors',
                                dest='ignore_http_errors',
                                action='store_true',
                                default=False,
                                help='ignore http errors so that an error does '
                                'not stop course downloading process. Please '
                                'note that this option only affects internal '
                                'downloader during resource download stage, '
                                'not syllabus parsing stage (default: False)')

    group_material.add_argument('--disable-url-skipping',
                                dest='disable_url_skipping',
                                action='store_true',
                                default=False,
                                help='disable URL skipping, all URLs will be '
                                'downloaded (default: False)')

    # Selection of material to download
    group_external_dl = parser.add_argument_group('External downloaders')

    group_external_dl.add_argument('--wget',
                                   dest='wget',
                                   action='store',
                                   nargs='?',
                                   const='wget',
                                   default=None,
                                   help='use wget for downloading,'
                                   'optionally specify wget bin')
    group_external_dl.add_argument('--curl',
                                   dest='curl',
                                   action='store',
                                   nargs='?',
                                   const='curl',
                                   default=None,
                                   help='use curl for downloading,'
                                   ' optionally specify curl bin')
    group_external_dl.add_argument('--aria2',
                                   dest='aria2',
                                   action='store',
                                   nargs='?',
                                   const='aria2c',
                                   default=None,
                                   help='use aria2 for downloading,'
                                   ' optionally specify aria2 bin')
    group_external_dl.add_argument('--axel',
                                   dest='axel',
                                   action='store',
                                   nargs='?',
                                   const='axel',
                                   default=None,
                                   help='use axel for downloading,'
                                   ' optionally specify axel bin')
    group_external_dl.add_argument('--downloader-arguments',
                                   dest='downloader_arguments',
                                   default='',
                                   help='additional arguments passed to the'
                                   ' downloader')

    parser.add_argument('--resume',
                        dest='resume',
                        action='store_true',
                        default=False,
                        help='resume incomplete downloads (default: False)')

    parser.add_argument('-o',
                        '--overwrite',
                        dest='overwrite',
                        action='store_true',
                        default=False,
                        help='whether existing files should be overwritten'
                             ' (default: False)')

    parser.add_argument('--verbose-dirs',
                        dest='verbose_dirs',
                        action='store_true',
                        default=False,
                        help='include class name in section directory name')

    parser.add_argument('--quiet',
                        dest='quiet',
                        action='store_true',
                        default=False,
                        help='omit as many messages as possible'
                             ' (only printing errors)')

    parser.add_argument('-r',
                        '--reverse',
                        dest='reverse',
                        action='store_true',
                        default=False,
                        help='download sections in reverse order')

    parser.add_argument('--combined-section-lectures-nums',
                        dest='combined_section_lectures_nums',
                        action='store_true',
                        default=False,
                        help='include lecture and section name in final files')

    parser.add_argument('--unrestricted-filenames',
                        dest='unrestricted_filenames',
                        action='store_true',
                        default=False,
                        help='Do not limit filenames to be ASCII-only')

    # Advanced authentication
    group_adv_auth = parser.add_argument_group('Advanced authentication options')

    group_adv_auth.add_argument('-c',
                                '--cookies_file',
                                dest='cookies_file',
                                action='store',
                                default=None,
                                help='full path to the cookies.txt file')

    group_adv_auth.add_argument('-n',
                                '--netrc',
                                dest='netrc',
                                nargs='?',
                                action='store',
                                const=True,
                                default=False,
                                help='use netrc for reading passwords, uses default'
                                ' location if no path specified')

    group_adv_auth.add_argument('-k',
                                '--keyring',
                                dest='use_keyring',
                                action='store_true',
                                default=False,
                                help='use keyring provided by operating system to '
                                'save and load credentials')

    group_adv_auth.add_argument('--clear-cache',
                                dest='clear_cache',
                                action='store_true',
                                default=False,
                                help='clear cached cookies')

    # Advanced miscellaneous options
    group_adv_misc = parser.add_argument_group('Advanced miscellaneous options')

    group_adv_misc.add_argument('--hook',
                                dest='hooks',
                                action='append',
                                default=[],
                                help='hooks to run when finished')

    group_adv_misc.add_argument('-pl',
                                '--playlist',
                                dest='playlist',
                                action='store_true',
                                default=False,
                                help='generate M3U playlists for course weeks')

    # Debug options
    group_debug = parser.add_argument_group('Debugging options')

    group_debug.add_argument('--skip-download',
                             dest='skip_download',
                             action='store_true',
                             default=False,
                             help='for debugging: skip actual downloading of files')

    group_debug.add_argument('--debug',
                             dest='debug',
                             action='store_true',
                             default=False,
                             help='print lots of debug information')

    group_debug.add_argument('--version',
                             dest='version',
                             action='store_true',
                             default=False,
                             help='display version and exit')

    group_debug.add_argument('-l',  # FIXME: remove short option from rarely used ones
                             '--process_local_page',
                             dest='local_page',
                             help='uses or creates local cached version of syllabus'
                             ' page')

    # Final parsing of the options
    args = parser.parse_args(args)

    # Initialize the logging system first so that other functions
    # can use it right away
    if args.debug:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(name)s[%(funcName)s] %(message)s')
    elif args.quiet:
        logging.basicConfig(level=logging.ERROR,
                            format='%(name)s: %(message)s')
    else:
        logging.basicConfig(level=logging.INFO,
                            format='%(message)s')

    # show version?
    if args.version:
        # we use print (not logging) function because version may be used
        # by some external script while logging may output excessive information
        print(__version__)
        sys.exit(0)

    # turn list of strings into list
    args.downloader_arguments = args.downloader_arguments.split()

    # turn list of strings into list
    args.file_formats = args.file_formats.split()

    # decode path so we can work properly with cyrillic symbols on different
    # versions on Python
    args.path = decode_input(args.path)

    # check arguments
    if args.use_keyring and args.password:
        logging.warning('--keyring and --password cannot be specified together')
        args.use_keyring = False

    if args.use_keyring and not keyring:
        logging.warning('The python module `keyring` not found.')
        args.use_keyring = False

    if args.cookies_file and not os.path.exists(args.cookies_file):
        logging.error('Cookies file not found: %s', args.cookies_file)
        sys.exit(1)

    if not args.cookies_file:
        try:
            args.username, args.password = get_credentials(
                username=args.username, password=args.password,
                netrc=args.netrc, use_keyring=args.use_keyring)
        except CredentialsError as e:
            logging.error(e)
            sys.exit(1)

    return args


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
                                  args.video_resolution)

    return completed


def download_on_demand_class(args, class_name):
    """
    Download all requested resources from the on-demand class given in class_name.

    Returns True if the class appears completed.
    """

    session = get_session()
    login(session, args.username, args.password)

    # get the syllabus listing
    page = get_on_demand_syllabus(session, class_name)

    ignored_formats = []
    if args.ignore_formats:
        ignored_formats = args.ignore_formats.split(",")

    # parse it
    modules = parse_on_demand_syllabus(session, page,
                                       args.reverse,
                                       args.unrestricted_filenames,
                                       args.subtitle_language,
                                       args.video_resolution)

    if is_debug_run():
        with open('%s-syllabus-parsed.json' % class_name, 'w') as file_object:
            json.dump(modules, file_object, indent=4)

    downloader = get_downloader(session, class_name, args)

    # obtain the resources

    skipped_urls = []
    failed_urls = []

    completed = True
    for idx, module in enumerate(modules):
        module_name = '%02d_%s' % (idx + 1, module[0])
        sections = module[1]

        result = download_lectures(
            downloader,
            module_name,
            sections,
            args.file_formats,
            args.overwrite,
            args.skip_download,
            args.section_filter,
            args.lecture_filter,
            args.resource_filter,
            os.path.join(args.path, class_name),
            args.verbose_dirs,
            args.preview,
            args.combined_section_lectures_nums,
            args.hooks,
            args.playlist,
            args.unrestricted_filenames,
            ignored_formats,
            args.resume,
            None if args.disable_url_skipping else skipped_urls,
            failed_urls if args.ignore_http_errors else None
        )
        completed = completed and result

    # Print skipped URLs if any
    if skipped_urls:
        logging.info('The following URLs (%d) have been skipped and not '
                     'downloaded:', len(skipped_urls))
        logging.info('(if you want to download these URLs anyway, please '
                     'add "--disable-url-skipping" option)')
        logging.info('-' * 80)
        for url in skipped_urls:
            logging.info(url)
        logging.info('-' * 80)

    # Print failed URLs if any
    # FIXME: should we set non-zero exit code if we have failed URLs?
    if failed_urls:
        logging.info('The following URLs (%d) could not be downloaded:',
                     len(failed_urls))
        logging.info('-' * 80)
        for url in failed_urls:
            logging.info(url)
        logging.info('-' * 80)

    return completed


def download_class(args, class_name):
    """
    Try to download class as if it were an old style class, and if it fails,
    try it as an on-demand class.

    Returns True if the class appears completed.
    """
    try:
        logging.debug('Downloading old style class %s', class_name)
        return download_old_style_class(args, class_name)
    except ClassNotFound:
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
