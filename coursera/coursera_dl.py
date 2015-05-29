#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
For downloading lecture resources such as videos for Coursera classes. Given
a class name, username and password, it scrapes the course listing page to
get the section (week) and lecture names, and then downloads the related
materials into appropriately named files and directories.

Examples:
  coursera-dl -u <user> -p <passwd> saas
  coursera-dl -u <user> -p <passwd> -l listing.html -o saas --skip-download

For further documentation and examples, visit the project's home at:
  https://github.com/coursera-dl/coursera

Authors and copyright:
    © 2012-2013, John Lehmann (first last at geemail dotcom or @jplehmann)
    © 2012-2015, Rogério Brito (r lastname at ime usp br)
    © 2013, Jonas De Taeye (first dt at fastmail fm)

Contributions are welcome, but please add new unit tests to test your changes
and/or features.  Also, please try to make changes platform independent and
backward compatible.

Legalese:

 This program is free software: you can redistribute it and/or modify it
 under the terms of the GNU Lesser General Public License as published by
 the Free Software Foundation, either version 3 of the License, or (at your
 option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
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

from distutils.version import LooseVersion as V

import requests

from six import iteritems
from bs4 import BeautifulSoup as BeautifulSoup_

# Force us of bs4 with html5lib
BeautifulSoup = lambda page: BeautifulSoup_(page, 'html5lib')


from .cookies import (
    AuthenticationFailed, ClassNotFound,
    get_cookies_for_class, make_cookie_values, login, TLSAdapter)
from .credentials import get_credentials, CredentialsError, keyring
from .define import CLASS_URL, ABOUT_URL, PATH_CACHE, \
    OPENCOURSE_CONTENT_URL, OPENCOURSE_VIDEO_URL
from .downloaders import get_downloader
from .utils import clean_filename, get_anchor_format, mkdir_p, fix_url, \
    decode_input, make_coursera_absolute_url

# URL containing information about outdated modules
_SEE_URL = " See https://github.com/coursera-dl/coursera/issues/139"

# Test versions of some critical modules.
# We may, perhaps, want to move these elsewhere.
import bs4
import six

assert V(requests.__version__) >= V('2.4'), "Upgrade requests!" + _SEE_URL
assert V(six.__version__) >= V('1.5'), "Upgrade six!" + _SEE_URL
assert V(bs4.__version__) >= V('4.1'), "Upgrade bs4!" + _SEE_URL


def get_on_demand_video_url(session, video_id, subtitle_language='en'):
    """
    Return the download URL of on-demand course video.
    """

    url = OPENCOURSE_VIDEO_URL.format(video_id=video_id)
    page = get_page(session, url)

    video_content = {}
    dom = json.loads(page)

    # videos
    sources = dom['sources']
    sources.sort(key=lambda src: src['resolution'])
    sources.reverse()
    video_url = sources[0]['formatSources']['video/mp4']
    video_content['mp4'] = video_url

    # subtitles
    subtitles = dom.get('subtitles')
    if subtitles is not None:
        if subtitle_language != 'en' and subtitle_language not in subtitles:
            logging.warning("Subtitle unavailable in '%s' language, moving "
                            "back to 'en' subtitle", subtitle_language)
            subtitle_language = 'en'

        subtitle_url = subtitles.get(subtitle_language)
        if subtitle_url is not None:
            # some subtitle urls are relative!
            video_content['srt'] = make_coursera_absolute_url(subtitle_url)

    return video_content


def get_syllabus_url(class_name, preview):
    """
    Return the Coursera index/syllabus URL, depending on if we want to only
    preview or if we are enrolled in the course.
    """
    class_type = 'preview' if preview else 'index'
    page = CLASS_URL.format(class_name=class_name) + '/lecture/' + class_type
    logging.debug('Using %s mode with page: %s', class_type, page)

    return page


def get_page(session, url):
    """
    Download an HTML page using the requests session.
    """

    r = session.get(url)

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error("Error %s getting page %s", e, url)
        raise

    return r.text


def get_session():
    """
    Create a session with TLS v1.2 certificate.
    """

    session = requests.Session()
    session.mount('https://', TLSAdapter())

    return session


def grab_hidden_video_url(session, href):
    """
    Follow some extra redirects to grab hidden video URLs (like those from
    University of Washington).
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


def get_syllabus(session, class_name, local_page=False, preview=False):
    """
    Get the course listing webpage.

    If we are instructed to use a local page and it already exists, then
    that page is used instead of performing a download.  If we are
    instructed to use a local page and it does not exist, then we download
    the page and save a copy of it for future use.
    """

    if not (local_page and os.path.exists(local_page)):
        url = get_syllabus_url(class_name, preview)
        page = get_page(session, url)
        logging.info('Downloaded %s (%d bytes)', url, len(page))

        # cache the page if we're in 'local' mode
        if local_page:
            with open(local_page, 'w') as f:
                f.write(page.encode("utf-8"))
    else:
        with open(local_page) as f:
            page = f.read().decode("utf-8")
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


def get_video(session, url):
    """
    Parses a Coursera video page
    """

    page = get_page(session, url)
    soup = BeautifulSoup(page)
    return soup.find(attrs={'type': re.compile('^video/mp4')})['src']


def parse_syllabus(session, page, reverse=False, intact_fnames=False,
                   subtitle_language='en'):
    """
    Parses a Coursera course listing/syllabus page.  Each section is a week
    of classes.
    """

    sections = []
    soup = BeautifulSoup(page)

    # traverse sections
    stags = soup.findAll(attrs={'class': re.compile('^course-item-list-header')})
    for stag in stags:
        assert stag.contents[0] is not None, "couldn't find section"
        untouched_fname = stag.contents[0].contents[1]
        section_name = clean_filename(untouched_fname, intact_fnames)
        logging.info(section_name)
        lectures = []  # resources for 1 lecture

        # traverse resources (e.g., video, ppt, ..)
        for vtag in stag.nextSibling.findAll('li'):
            assert vtag.a.contents[0], "couldn't get lecture name"
            untouched_fname = vtag.a.contents[0]
            vname = clean_filename(untouched_fname, intact_fnames)
            logging.info('  %s', vname)
            lecture = {}
            lecture_page = None

            for a in vtag.findAll('a'):
                href = fix_url(a['href'])
                untouched_fname = a.get('title', '')
                title = clean_filename(untouched_fname, intact_fnames)
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
                        href = get_video(session, lecture_page)
                        lecture['mp4'] = lecture.get('mp4', [])
                        lecture['mp4'].append((fix_url(href), ''))
                    except TypeError:
                        logging.warn(
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


def parse_on_demand_syllabus(session, page, reverse=False, intact_fnames=False,
                             subtitle_language='en'):
    """
    Parses a Coursera on-demand course listing/syllabus page.
    """

    dom = json.loads(page)

    logging.info('Parsing syllabus of on-demand course. '
                 'This may take some time, be patient ...')
    modules = []
    json_modules = dom['courseMaterial']['elements']
    for module in json_modules:
        module_slug = module['slug']
        sections = []
        json_sections = module['elements']
        for section in json_sections:
            section_slug = section['slug']
            lectures = []
            json_lectures = section['elements']
            for lecture in json_lectures:
                lecture_slug = lecture['slug']
                if lecture['content']['typeName'] == 'lecture':
                    lecture_video_id = lecture['content']['definition']['videoId']
                    video_content = get_on_demand_video_url(session,
                                                            lecture_video_id,
                                                            subtitle_language)
                    lecture_video_content = {}
                    for key, value in video_content.items():
                        lecture_video_content[key] = [(value, '')]

                    if lecture_video_content:
                        lectures.append((lecture_slug, lecture_video_content))

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


def find_resources_to_get(lecture, file_formats, resource_filter):
    # Select formats to download
    resources_to_get = []
    for fmt, resources in iteritems(lecture):
        if fmt in file_formats or 'all' in file_formats:
            for r in resources:
                if resource_filter and r[1] and not re.search(resource_filter, r[1]):
                    logging.debug('Skipping b/c of rf: %s %s',
                                  resource_filter, r[1])
                    continue
                resources_to_get.append((fmt, r[0], r[1]))
        else:
            logging.debug(
                'Skipping b/c format %s not in %s', fmt, file_formats)

    return resources_to_get


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
                      intact_fnames=False):
    """
    Downloads lecture resources described by sections.
    Returns True if the class appears completed.
    """
    last_update = -1

    for (secnum, (section, lectures)) in enumerate(sections):
        if section_filter and not re.search(section_filter, section):
            logging.debug('Skipping b/c of sf: %s %s', section_filter,
                          section)
            continue

        sec = os.path.join(path, class_name,
                           format_section(secnum + 1, section, class_name, verbose_dirs))
        for (lecnum, (lecname, lecture)) in enumerate(lectures):
            if lecture_filter and not re.search(lecture_filter,
                                                lecname):
                logging.debug('Skipping b/c of lf: %s %s', lecture_filter,
                              lecname)
                continue

            if not os.path.exists(sec):
                mkdir_p(sec)

            resources_to_get = find_resources_to_get(lecture, file_formats, resource_filter)

            # write lecture resources
            for fmt, url, title in resources_to_get:
                if combined_section_lectures_nums:
                    lecfn = os.path.join(
                        sec,
                        format_combine_number_resource(
                            secnum + 1, lecnum + 1, lecname, title, fmt))
                else:
                    lecfn = os.path.join(
                        sec, format_resource(lecnum + 1, lecname, title, fmt))

                if overwrite or not os.path.exists(lecfn):
                    if not skip_download:
                        logging.info('Downloading: %s', lecfn)
                        downloader.download(url, lecfn)
                    else:
                        open(lecfn, 'w').close()  # touch
                    last_update = time.time()
                else:
                    logging.info('%s already downloaded', lecfn)
                    # if this file hasn't been modified in a long time,
                    # record that time
                    last_update = max(last_update, os.path.getmtime(lecfn))

        # After fetching resources, create a playlist in M3U format with the
        # videos downloaded.
        if playlist:
            path_to_return = os.getcwd()

            for (_path, subdirs, files) in os.walk(sec):
                os.chdir(_path)
                globbed_videos = glob.glob("*.mp4")
                m3u_name = os.path.split(_path)[1] + ".m3u"

                if len(globbed_videos):
                    with open(m3u_name, "w") as m3u:
                        for video in globbed_videos:
                            m3u.write(video + "\n")
                    os.chdir(path_to_return)

        if hooks:
            for hook in hooks:
                logging.info('Running hook %s for section %s.', hook, sec)
                os.chdir(sec)
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


def parseArgs(args=None):
    """
    Parse the arguments/options passed to the program on the command line.
    """

    parser = argparse.ArgumentParser(
        description='Download Coursera.org lecture material and resources.')

    # positional
    parser.add_argument('class_names',
                        action='store',
                        nargs='+',
                        help='name(s) of the class(es) (e.g. "nlp")')

    parser.add_argument('-c',
                        '--cookies_file',
                        dest='cookies_file',
                        action='store',
                        default=None,
                        help='full path to the cookies.txt file')
    parser.add_argument('-u',
                        '--username',
                        dest='username',
                        action='store',
                        default=None,
                        help='coursera username')
    parser.add_argument('-n',
                        '--netrc',
                        dest='netrc',
                        nargs='?',
                        action='store',
                        const=True,
                        default=False,
                        help='use netrc for reading passwords, uses default'
                             ' location if no path specified')

    parser.add_argument('-p',
                        '--password',
                        dest='password',
                        action='store',
                        default=None,
                        help='coursera password')

    parser.add_argument('-k',
                        '--keyring',
                        dest='use_keyring',
                        action='store_true',
                        default=False,
                        help='use keyring provided by operating system to '
                             'save and load credentials')
    # optional
    parser.add_argument('--about',
                        dest='about',
                        action='store_true',
                        default=False,
                        help='download "about" metadata. (Default: False)')
    parser.add_argument('--on-demand',
                        dest='on_demand',
                        action='store_true',
                        default=False,
                        help='get on-demand videos. (Default: False)')
    parser.add_argument('-b',
                        '--preview',
                        dest='preview',
                        action='store_true',
                        default=False,
                        help='get preview videos. (Default: False)')
    parser.add_argument('-f',
                        '--formats',
                        dest='file_formats',
                        action='store',
                        default='all',
                        help='file format extensions to be downloaded in'
                             ' quotes space separated, e.g. "mp4 pdf" '
                             '(default: special value "all")')
    parser.add_argument('-sf',
                        '--section_filter',
                        dest='section_filter',
                        action='store',
                        default=None,
                        help='only download sections which contain this'
                             ' regex (default: disabled)')
    parser.add_argument('-lf',
                        '--lecture_filter',
                        dest='lecture_filter',
                        action='store',
                        default=None,
                        help='only download lectures which contain this regex'
                             ' (default: disabled)')
    parser.add_argument('-rf',
                        '--resource_filter',
                        dest='resource_filter',
                        action='store',
                        default=None,
                        help='only download resources which match this regex'
                             ' (default: disabled)')
    parser.add_argument('--wget',
                        dest='wget',
                        action='store',
                        nargs='?',
                        const='wget',
                        default=None,
                        help='use wget for downloading,'
                             'optionally specify wget bin')
    parser.add_argument('--curl',
                        dest='curl',
                        action='store',
                        nargs='?',
                        const='curl',
                        default=None,
                        help='use curl for downloading,'
                             ' optionally specify curl bin')
    parser.add_argument('--aria2',
                        dest='aria2',
                        action='store',
                        nargs='?',
                        const='aria2c',
                        default=None,
                        help='use aria2 for downloading,'
                             ' optionally specify aria2 bin')
    parser.add_argument('--axel',
                        dest='axel',
                        action='store',
                        nargs='?',
                        const='axel',
                        default=None,
                        help='use axel for downloading,'
                             ' optionally specify axel bin')
    # We keep the wget_bin, ... options for backwards compatibility.
    parser.add_argument('-w',
                        '--wget_bin',
                        dest='wget_bin',
                        action='store',
                        default=None,
                        help='DEPRECATED, use --wget')
    parser.add_argument('--curl_bin',
                        dest='curl_bin',
                        action='store',
                        default=None,
                        help='DEPRECATED, use --curl')
    parser.add_argument('--aria2_bin',
                        dest='aria2_bin',
                        action='store',
                        default=None,
                        help='DEPRECATED, use --aria2')
    parser.add_argument('--axel_bin',
                        dest='axel_bin',
                        action='store',
                        default=None,
                        help='DEPRECATED, use --axel')
    parser.add_argument('-o',
                        '--overwrite',
                        dest='overwrite',
                        action='store_true',
                        default=False,
                        help='whether existing files should be overwritten'
                             ' (default: False)')
    parser.add_argument('-l',
                        '--process_local_page',
                        dest='local_page',
                        help='uses or creates local cached version of syllabus'
                             ' page')
    parser.add_argument('--skip-download',
                        dest='skip_download',
                        action='store_true',
                        default=False,
                        help='for debugging: skip actual downloading of files')
    parser.add_argument('--path',
                        dest='path',
                        action='store',
                        default='',
                        help='path to save the file')
    parser.add_argument('--verbose-dirs',
                        dest='verbose_dirs',
                        action='store_true',
                        default=False,
                        help='include class name in section directory name')
    parser.add_argument('--debug',
                        dest='debug',
                        action='store_true',
                        default=False,
                        help='print lots of debug information')
    parser.add_argument('--quiet',
                        dest='quiet',
                        action='store_true',
                        default=False,
                        help='omit as many messages as possible'
                             ' (only printing errors)')
    parser.add_argument('--add-class',
                        dest='add_class',
                        action='append',
                        default=[],
                        help='additional classes to get')
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
    parser.add_argument('--hook',
                        dest='hooks',
                        action='append',
                        default=[],
                        help='hooks to run when finished')
    parser.add_argument('-pl',
                        '--playlist',
                        dest='playlist',
                        action='store_true',
                        default=False,
                        help='generate M3U playlists for course weeks')
    parser.add_argument('--clear-cache',
                        dest='clear_cache',
                        action='store_true',
                        default=False,
                        help='clear cached cookies')
    parser.add_argument('--unrestricted-filenames',
                        dest='intact_fnames',
                        action='store_true',
                        default=False,
                        help='Do not limit filenames to be ASCII-only')
    parser.add_argument('-sl',
                        '--subtitle-language',
                        dest='subtitle_language',
                        action='store',
                        default='en',
                        help='Choose language to download subtitles')

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

    # turn list of strings into list
    args.file_formats = args.file_formats.split()

    # decode path so we can work properly with cyrillic symbols on different
    # versions on Python
    args.path = decode_input(args.path)

    for bin in ['wget_bin', 'curl_bin', 'aria2_bin', 'axel_bin']:
        if getattr(args, bin):
            logging.error('The --%s option is deprecated, please use --%s',
                          bin, bin[:-4])
            sys.exit(1)

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


def download_class(args, class_name):
    """
    Download all requested resources from the class given in class_name.
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
        about = download_about(session,
                               class_name,
                               args.path,
                               args.overwrite,
                               args.subtitle_language)
        # Check if subtitle is available
        if not about["subtitleLanguagesCsv"].split(',').count(args.subtitle_language):
            logging.warning("Subtitle unavailable in specified language")
            subtitle_language = "en"

    # get the syllabus listing
    page = get_syllabus(session, class_name, args.local_page, args.preview)

    # parse it
    sections = parse_syllabus(session, page, args.reverse,
                              args.intact_fnames, subtitle_language)

    downloader = get_downloader(session, class_name, args)

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
                                  args.intact_fnames)

    return completed


def download_on_demand_class(args, class_name):
    """
    Download all requested resources from the on-demand class
    given in class_name. Returns True if the class appears completed.
    """

    session = get_session()
    login(session, args.username, args.password)

    # get the syllabus listing
    page = get_on_demand_syllabus(session, class_name)

    # parse it
    modules = parse_on_demand_syllabus(session, page,
                                       args.reverse,
                                       args.intact_fnames,
                                       args.subtitle_language)

    downloader = get_downloader(session, class_name, args)

    # obtain the resources
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
            args.intact_fnames
        )
        completed = completed and result

    return completed


def main():
    """
    Main entry point for execution as a program (instead of as a module).
    """

    args = parseArgs()
    completed_classes = []

    mkdir_p(PATH_CACHE, 0o700)
    if args.clear_cache:
        shutil.rmtree(PATH_CACHE)

    for class_name in args.class_names:
        try:
            logging.info('Downloading class: %s', class_name)
            result = False
            if args.on_demand:
                result = download_on_demand_class(args, class_name)
            else:
                result = download_class(args, class_name)

            if result:
                completed_classes.append(class_name)
        except requests.exceptions.HTTPError as e:
            logging.error('HTTPError %s', e)
        except ClassNotFound as cnf:
            logging.error('Could not find class: %s', cnf)
        except AuthenticationFailed as af:
            logging.error('Could not authenticate: %s', af)

    if completed_classes:
        logging.info(
            "Classes which appear completed: " + " ".join(completed_classes))


if __name__ == '__main__':
    main()
