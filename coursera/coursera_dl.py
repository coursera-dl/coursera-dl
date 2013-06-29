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
  https://github.com/jplehmann/coursera

Authors and copyright:
    © 2012-2013, John Lehmann (first last at geemail dotcom or @jplehmann)
    © 2012-2013, Rogério Brito (r lastname at ime usp br)
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
import cookielib
import datetime
import errno
import logging
import os
import re
import string
import StringIO
import subprocess
import sys
import time
import urlparse

import requests

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup as BeautifulSoup_
    try:
        # Use html5lib for parsing if available
        import html5lib
        BeautifulSoup = lambda page: BeautifulSoup_(page, 'html5lib')
    except ImportError:
        BeautifulSoup = lambda page: BeautifulSoup_(page, 'html.parser')


from credentials import get_credentials, CredentialsError


AUTH_URL = 'https://www.coursera.org/maestro/api/user/login'
CLASS_URL = 'https://class.coursera.org/{class_name}'
AUTH_REDIRECT_URL = 'https://class.coursera.org/{class_name}' \
                    '/auth/auth_redirector?type=login&subtype=normal'

# Monkey patch cookielib.Cookie.__init__.
# Reason: The expires value may be a decimal string,
# but the Cookie class uses int() ...
__orginal_init__ = cookielib.Cookie.__init__


def __fixed_init__(self, version, name, value,
                   port, port_specified,
                   domain, domain_specified, domain_initial_dot,
                   path, path_specified,
                   secure,
                   expires,
                   discard,
                   comment,
                   comment_url,
                   rest,
                   rfc2109=False,
                   ):
    expires = float(expires)
    __orginal_init__(self, version, name, value,
                     port, port_specified,
                     domain, domain_specified, domain_initial_dot,
                     path, path_specified,
                     secure,
                     expires,
                     discard,
                     comment,
                     comment_url,
                     rest,
                     rfc2109=False,)

cookielib.Cookie.__init__ = __fixed_init__


class ClassNotFound(BaseException):
    """
    Class to be thrown if a course is not found in Coursera's site.
    """

    pass


class AuthenticationFailed(BaseException):
    """
    Class to be thrown if we cannot authenticate on Coursera's site.
    """

    pass


class BandwidthCalc(object):
    """
    Class for calculation of bandwidth for the "native" downloader.
    """

    def __init__(self):
        self.nbytes = 0
        self.prev_time = time.time()
        self.prev_bw = 0
        self.prev_bw_length = 0

    def received(self, data_length):
        now = time.time()
        self.nbytes += data_length
        time_delta = now - self.prev_time

        if time_delta > 1:  # average over 1+ second
            bw = float(self.nbytes) / time_delta
            self.prev_bw = (self.prev_bw + 2 * bw) / 3
            self.nbytes = 0
            self.prev_time = now

    def __str__(self):
        if self.prev_bw == 0:
            bw = ''
        elif self.prev_bw < 1000:
            bw = ' (%dB/s)' % self.prev_bw
        elif self.prev_bw < 1000000:
            bw = ' (%.2fKB/s)' % (self.prev_bw / 1000)
        elif self.prev_bw < 1000000000:
            bw = ' (%.2fMB/s)' % (self.prev_bw / 1000000)
        else:
            bw = ' (%.2fGB/s)' % (self.prev_bw / 1000000000)

        length_diff = self.prev_bw_length - len(bw)
        self.prev_bw_length = len(bw)

        if length_diff > 0:
            return '%s%s' % (bw, length_diff * ' ')
        else:
            return bw


def get_syllabus_url(class_name, preview):
    """
    Return the Coursera index/syllabus URL, depending on if we want to only
    preview or if we are enrolled in the course.
    """
    class_type = 'preview' if preview else 'index'
    page = CLASS_URL.format(class_name=class_name) + '/lecture/' + class_type
    logging.debug('Using %s mode with page: %s', class_type, page)

    return page


def login(session, class_name, username, password):
    """
    Login on www.coursera.org with the given credentials.
    """

    # Hit class url to obtain csrf_token
    class_url = CLASS_URL.format(class_name=class_name)
    r = requests.get(class_url, allow_redirects=False)

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ClassNotFound(class_name)

    csrftoken = r.cookies.get('csrf_token')

    if not csrftoken:
        raise AuthenticationFailed('Did not recieve csrf_token cookie.')

    # Now make a call to the authenticator url.
    headers = {
        'Cookie': 'csrftoken=' + csrftoken,
        'Referer': 'https://www.coursera.org',
        'X-CSRFToken': csrftoken,
    }

    data = {
        'email_address': username,
        'password': password
    }

    r = session.post(AUTH_URL, data=data,
                     headers=headers, allow_redirects=False)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        raise AuthenticationFailed('Cannot login on www.coursera.org.')

    logging.info('Logged in on www.coursera.org.')


def down_the_wabbit_hole(session, class_name):
    """
    Authenticate on class.coursera.org
    """

    auth_redirector_url = AUTH_REDIRECT_URL.format(class_name=class_name)
    r = session.get(auth_redirector_url)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        raise AuthenticationFailed('Cannot login on class.coursera.org.')


def get_authentication_cookies(session, class_name):
    """
    Get the necessary cookies to authenticate on class.coursera.org.

    At this moment we should have the following cookies on www.coursera.org:
        maestro_login_flag, sessionid, maestro_login
    To access the class pages we need two cookies on class.coursera.org:
        csrf_token, session
    """

    # First, check if we already have the class.coursera.org cookies.
    enough = do_we_have_enough_cookies(session.cookies, class_name)

    if not enough:
        # Get the class.coursera.org cookies. Remember that we need
        # the cookies from www.coursera.org!
        down_the_wabbit_hole(session, class_name)

        enough = do_we_have_enough_cookies(session.cookies, class_name)

        if not enough:
            raise AuthenticationFailed('Did not find necessary cookies.')

    logging.info('Found authentication cookies.')

    session.cookie_values = make_cookie_values(session.cookies, class_name)


def do_we_have_enough_cookies(cj, class_name):
    """
    Checks whether we have all the required cookies
    to authenticate on class.coursera.org.
    """
    domain = 'class.coursera.org'
    path = "/" + class_name

    return cj.get('session', domain=domain, path=path) \
        and cj.get('csrf_token', domain=domain, path=path)


def make_cookie_values(cj, class_name):
    """
    Makes a string of cookie keys and values.
    Can be used to set a Cookie header.
    """
    path = "/" + class_name

    cookies = [c.name + '=' + c.value
               for c in cj
               if c.domain == "class.coursera.org"
               and c.path == path]

    return '; '.join(cookies)


def find_cookies_for_class(cookies_file, class_name):
    """
    Return a RequestsCookieJar containing the cookies for
    www.coursera.org and class.coursera.org found in the given cookies_file.
    """

    path = "/" + class_name

    def cookies_filter(c):
        return c.domain == "www.coursera.org" \
            or (c.domain == "class.coursera.org" and c.path == path)

    cj = get_cookie_jar(cookies_file)
    cookies_list = filter(cookies_filter, cj)

    new_cj = requests.cookies.RequestsCookieJar()
    for c in cookies_list:
        new_cj.set_cookie(c)

    return new_cj


def load_cookies_file(cookies_file):
    """
    Loads the cookies file.

    We pre-pend the file with the special Netscape header because the cookie
    loader is very particular about this string.
    """

    cookies = StringIO.StringIO()
    cookies.write('# Netscape HTTP Cookie File')
    cookies.write(open(cookies_file, 'rU').read())
    cookies.flush()
    cookies.seek(0)
    return cookies


def get_cookie_jar(cookies_file):
    cj = cookielib.MozillaCookieJar()
    cookies = load_cookies_file(cookies_file)

    # nasty hack: cj.load() requires a filename not a file, but if I use
    # stringio, that file doesn't exist. I used NamedTemporaryFile before,
    # but encountered problems on Windows.
    cj._really_load(cookies, 'StringIO.cookies', False, False)

    return cj


def get_page(session, url, skip_errors):
    """
    Download an HTML page using the requests session.
    """

    r = session.get(url)

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error("Error getting page %s", url)
        if not skip_errors:
            raise

    return r.text


def grab_hidden_video_url(session, href, skip_errors=False):
    """
    Follow some extra redirects to grab hidden video URLs (like those from
    University of Washington).
    """
    page = get_page(session, href, skip_errors)
    soup = BeautifulSoup(page)
    l = soup.find('source', attrs={'type': 'video/mp4'})
    if l is not None:
        return l['src']
    else:
        return None


def get_syllabus(session, class_name, local_page=False, preview=False, skip_errors=False):
    """
    Get the course listing webpage.

    If we are instructed to use a local page and it already exists, then
    that page is used instead of performing a download.  If we are
    instructed to use a local page and it does not exist, then we download
    the page and save a copy of it for future use.
    """

    if not (local_page and os.path.exists(local_page)):
        url = get_syllabus_url(class_name, preview)
        page = get_page(session, url, skip_errors)
        logging.info('Downloaded %s (%d bytes)', url, len(page))

        # cache the page if we're in 'local' mode
        if local_page:
            with open(local_page, 'w') as f:
                f.write(page)
    else:
        with open(local_page) as f:
            page = f.read()
        logging.info('Read (%d bytes) from local file', len(page))

    return page


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


def transform_preview_url(a):
    """
    Given a preview lecture URL, transform it into a regular video URL.

    If the given URL is not a preview URL, we simply return None.
    """

    # Example URLs
    # "https://class.coursera.org/modelthinking/lecture/preview_view/8"
    # "https://class.coursera.org/nlp/lecture/view?lecture_id=124"
    mobj = re.search(r'preview_view/(\d+)$', a)
    if mobj:
        return re.sub(r'preview_view/(\d+)$', r'view?lecture_id=\1', a)
    else:
        return None


def get_video(session, url):
    """
    Parses a Coursera video page
    """

    page = get_page(session, url)
    soup = BeautifulSoup(page)
    return soup.find(attrs={'type': re.compile('^video/mp4')})['src']


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


def parse_syllabus(session, page, reverse=False, skip_errors=False):
    """
    Parses a Coursera course listing/syllabus page.  Each section is a week
    of classes.
    """

    sections = []
    soup = BeautifulSoup(page)

    # traverse sections
    for stag in soup.findAll(attrs={'class':
                                    re.compile('^course-item-list-header')}):
        assert stag.contents[0] is not None, "couldn't find section"
        section_name = clean_filename(stag.contents[0].contents[1])
        logging.info(section_name)
        lectures = []  # resources for 1 lecture

        # traverse resources (e.g., video, ppt, ..)
        for vtag in stag.nextSibling.findAll('li'):
            assert vtag.a.contents[0], "couldn't get lecture name"
            vname = clean_filename(vtag.a.contents[0])
            logging.info('  %s', vname)
            lecture = {}
            lecture_page = None

            for a in vtag.findAll('a'):
                href = fix_url(a['href'])
                fmt = get_anchor_format(href)
                logging.debug('    %s %s', fmt, href)
                if fmt:
                    lecture[fmt] = href
                    continue

                # Special case: find preview URLs
                lecture_page = transform_preview_url(href)
                if lecture_page:
                    try:
                        href = get_video(session, lecture_page)
                        lecture['mp4'] = fix_url(href)
                    except TypeError:
                        logging.warn('Could not get resource: %s', lecture_page)

            # Special case: we possibly have hidden video links---thanks to
            # the University of Washington for that.
            if 'mp4' not in lecture:
                for a in vtag.findAll('a'):
                    if a.get('data-modal-iframe'):
                        href = grab_hidden_video_url(session, a['data-modal-iframe'], skip_errors)
                        href = fix_url(href)
                        fmt = 'mp4'
                        logging.debug('    %s %s', fmt, href)
                        if href is not None:
                            lecture[fmt] = href

            lectures.append((vname, lecture))

        sections.append((section_name, lectures))

    logging.info('Found %d sections and %d lectures on this page',
                 len(sections), sum(len(s[1]) for s in sections))

    if sections and reverse:
        sections.reverse()

    if not len(sections):
        logging.error('Probably bad cookies file (or wrong class name)')

    return sections


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


def download_lectures(session,
                      wget_bin,
                      curl_bin,
                      aria2_bin,
                      axel_bin,
                      class_name,
                      sections,
                      file_formats,
                      overwrite=False,
                      skip_download=False,
                      section_filter=None,
                      lecture_filter=None,
                      path='',
                      verbose_dirs=False,
                      preview=False,
                      combined_section_lectures_nums=False,
                      hooks=None,
											skip_errors=False
                      ):
    """
    Downloads lecture resources described by sections.
    Returns True if the class appears completed.
    """
    last_update = -1

    def format_section(num, section):
        sec = '%02d_%s' % (num, section)
        if verbose_dirs:
            sec = class_name.upper() + '_' + sec
        return sec

    def format_resource(num, name, fmt):
        return '%02d_%s.%s' % (num, name, fmt)

    def format_combine_number_resource(secnum, lecnum, lecname, fmt):
        return '%02d_%02d_%s.%s' % (secnum, lecnum, lecname, fmt)

    for (secnum, (section, lectures)) in enumerate(sections):
        if section_filter and not re.search(section_filter, section):
            logging.debug('Skipping b/c of sf: %s %s', section_filter,
                          section)
            continue
        sec = os.path.join(path, class_name, format_section(secnum + 1,
                                                            section))
        for (lecnum, (lecname, lecture)) in enumerate(lectures):
            if lecture_filter and not re.search(lecture_filter,
                                                lecname):
                continue
            if not os.path.exists(sec):
                mkdir_p(sec)

            # Select formats to download
            lectures_to_get = []
            for i in lecture.items():
                if i[0] in file_formats or 'all' in file_formats:
                    lectures_to_get.append(i)
                else:
                    logging.debug('Skipping b/c format %s not in %s', i[0], file_formats)

            # write lecture resources
            for fmt, url in lectures_to_get:
                if combined_section_lectures_nums:
                    lecfn = os.path.join(sec, format_combine_number_resource(secnum + 1,
                                                         lecnum + 1, lecname, fmt))
                else:
                    lecfn = os.path.join(sec, format_resource(lecnum + 1, lecname, fmt))

                if overwrite or not os.path.exists(lecfn):
                    if not skip_download:
                        logging.info('Downloading: %s', lecfn)
                        download_file(session, url, lecfn, wget_bin,
                                      curl_bin, aria2_bin, axel_bin)
                    else:
                        open(lecfn, 'w').close()  # touch
                    last_update = time.time()
                else:
                    logging.info('%s already downloaded', lecfn)
                    # if this file hasn't been modified in a long time,
                    # record that time
                    last_update = max(last_update, os.path.getmtime(lecfn))

        if hooks:
            for hook in hooks:
                logging.info('Running hook %s for section %s.', hook, sec)
                os.chdir(sec)
                subprocess.call(hook)

    # if we haven't updated any files in 1 month, we're probably
    # done with this course
    if last_update >= 0:
        if time.time() - last_update > total_seconds(datetime.timedelta(days=30)):
            logging.info('COURSE PROBABLY COMPLETE: ' + class_name)
            return True
    return False


def total_seconds(td):
    """
    Compute total seconds for a timedelta.

    Added for backward compatibility, pre 2.7.
    """
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) // 10**6


def download_file(session,
                  url,
                  fn,
                  wget_bin,
                  curl_bin,
                  aria2_bin,
                  axel_bin,
                  ):
    """
    Decides which download method to use for a given file. When the download
    is aborted by the user, the partially downloaded file is also removed.
    """

    try:
        if wget_bin:
            download_file_wget(wget_bin, url, fn, session.cookie_values)
        elif curl_bin:
            download_file_curl(curl_bin, url, fn, session.cookie_values)
        elif aria2_bin:
            download_file_aria2(aria2_bin, url, fn, session.cookie_values)
        elif axel_bin:
            download_file_axel(axel_bin, url, fn, session.cookie_values)
        else:
            download_file_nowget(session, url, fn)
    except KeyboardInterrupt:
        logging.info('Keyboard Interrupt -- Removing partial file: %s', fn)
        os.remove(fn)
        sys.exit()


def download_file_wget(wget_bin, url, fn, cookie_values):
    """
    Downloads a file using wget.  Could possibly use python to stream files
    to disk, but wget is robust and gives nice visual feedback.
    """

    cmd = [wget_bin, url, '-O', fn, '--no-cookies', '--header',
           "Cookie: " + cookie_values,
           '--no-check-certificate']
    logging.debug('Executing wget: %s', cmd)
    return subprocess.call(cmd)


def download_file_curl(curl_bin, url, fn, cookie_values):
    """
    Downloads a file using curl.  Could possibly use python to stream files
    to disk, but curl is robust and gives nice visual feedback.
    """

    cmd = [curl_bin, url, '-k', '-#', '-L', '-o', fn,
           '--cookie', cookie_values]
    logging.debug('Executing curl: %s', cmd)
    return subprocess.call(cmd)


def download_file_aria2(aria2_bin, url, fn, cookie_values):
    """
    Downloads a file using aria2.  Could possibly use python to stream files
    to disk, but aria2 is robust. Unfortunately, it does not give a nice
    visual feedback, bug gets the job done much faster than the
    alternatives.
    """

    cmd = [aria2_bin, url, '-o', fn, '--header',
           "Cookie: " + cookie_values,
           '--check-certificate=false', '--log-level=notice',
           '--max-connection-per-server=4', '--min-split-size=1M']
    logging.debug('Executing aria2: %s', cmd)
    return subprocess.call(cmd)


def download_file_axel(axel_bin, url, fn, cookie_values):
    """
    Downloads a file using axel.  Could possibly use python to stream files
    to disk, but axel is robust and it both gives nice visual feedback and
    get the job done fast.
    """

    cmd = [axel_bin, '-H', "Cookie: " + cookie_values,
           '-o', fn, '-n', '4', '-a', url]
    logging.debug('Executing axel: %s', cmd)
    return subprocess.call(cmd)


def download_file_nowget(session, url, fn):
    """
    'Native' python downloader -- slower than wget.

    For consistency with subprocess.call, returns 0 to indicate success and
    1 to indicate problems.
    """

    logging.info('Downloading %s -> %s', url, fn)

    attempts_count = 0
    error_msg = ''
    while (attempts_count < 5):
        r = session.get(url, stream=True)

        if (r.status_code is not 200):
            logging.warn('Probably the file is missing from the AWS repository...'
                         ' waiting.')

            if r.reason:
                error_msg = r.reason + ' ' + str(r.status_code)
            else:
                error_msg = 'HTTP Error ' + str(r.status_code)

            wait_interval = 2 ** (attempts_count + 1)
            print 'Error to downloading, will retry in %s seconds ...' % wait_interval
            time.sleep(wait_interval)
            attempts_count += 1
            continue

        bw = BandwidthCalc()
        chunk_sz = 1048576
        bytesread = 0
        with open(fn, 'wb') as f:
            while True:
                data = r.raw.read(chunk_sz)
                if not data:
                    print '.'
                    break
                bw.received(len(data))
                f.write(data)
                bytesread += len(data)
                print '\r%d bytes read%s' % (bytesread, bw),
                sys.stdout.flush()
        r.close()
        return 0

    if attempts_count == 5:
        logging.warn('Skipping, can\'t download file ...')
        print error_msg
        return 1


def parseArgs():
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

    # optional
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
    parser.add_argument('--wget',
                        dest='wget',
                        action='store',
                        nargs='?',
                        const='wget',
                        default=None,
                        help='use wget for downloading, optionally specify wget bin')
    parser.add_argument('--curl',
                        dest='curl',
                        action='store',
                        nargs='?',
                        const='curl',
                        default=None,
                        help='use curl for downloading, optionally specify curl bin')
    parser.add_argument('--aria2',
                        dest='aria2',
                        action='store',
                        nargs='?',
                        const='aria2c',
                        default=None,
                        help='use aria2 for downloading, optionally specify aria2 bin')
    parser.add_argument('--axel',
                        dest='axel',
                        action='store',
                        nargs='?',
                        const='axel',
                        default=None,
                        help='use axel for downloading, optionally specify axel bin')
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
                        help='whether existing files should be overwritten (default: False)')
    parser.add_argument('-l',
                        '--process_local_page',
                        dest='local_page',
                        help='uses or creates local cached version of syllabus page')
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
                        help='omit as many messages as possible (only printing errors)')
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
    parser.add_argument('--skip-errors',
                        dest='skip_errors',
                        action='store_true',
                        default=False,
                        help='skip errors in download')

    args = parser.parse_args()

    # Initialize the logging system first so that other functions can use it right away
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

    for bin in ['wget_bin', 'curl_bin', 'aria2_bin', 'axel_bin']:
        if getattr(args, bin):
            logging.error('The --%s option is deprecated, please use --%s',
                bin, bin[:-4])
            sys.exit(1)

    # check arguments
    if args.cookies_file and not os.path.exists(args.cookies_file):
        logging.error('Cookies file not found: %s', args.cookies_file)
        sys.exit(1)

    if not args.cookies_file:
        try:
            args.username, args.password = get_credentials(
                username=args.username, password=args.password, netrc=args.netrc)
        except CredentialsError as e:
            logging.error(e)
            sys.exit(1)

    return args


def download_class(args, class_name):
    """
    Download all requested resources from the class given in class_name.
    Returns True if the class appears completed.
    """

    session = requests.Session()

    if args.preview:
        # Todo, remove this.
        session.cookie_values = 'dummy=dummy'
    else:
        if args.cookies_file:
            cookies = find_cookies_for_class(args.cookies_file, class_name)
            session.cookies.update(cookies)
        else:
            login(session, class_name, args.username, args.password)

        get_authentication_cookies(session, class_name)

    # get the syllabus listing
    page = get_syllabus(session, class_name, args.local_page, args.preview, args.skip_errors)

    # parse it
    sections = parse_syllabus(session, page, args.reverse, args.skip_errors)

    # obtain the resources
    completed = download_lectures(
        session,
        args.wget,
        args.curl,
        args.aria2,
        args.axel,
        class_name,
        sections,
        args.file_formats,
        args.overwrite,
        args.skip_download,
        args.section_filter,
        args.lecture_filter,
        args.path,
        args.verbose_dirs,
        args.preview,
        args.combined_section_lectures_nums,
        args.hooks,
				args.skip_errors)

    return completed


def main():
    """
    Main entry point for execution as a program (instead of as a module).
    """

    args = parseArgs()
    completed_classes = []

    for class_name in args.class_names:
        try:
            logging.info('Downloading class: %s', class_name)
            if download_class(args, class_name):
                completed_classes.append(class_name)
        except requests.exceptions.HTTPError as e:
            logging.error('HTTPError %s', e)
        except ClassNotFound as cnf:
            logging.error('Could not find class: %s', cnf)
        except AuthenticationFailed as af:
            logging.error('Could not authenticate: %s', af)

    if completed_classes:
        logging.info("Classes which appear completed: " + " ".join(completed_classes))


if __name__ == '__main__':
    main()
