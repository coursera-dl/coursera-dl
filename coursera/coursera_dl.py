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
import getpass
import logging
import netrc
import os
import platform
import re
import string
import StringIO
import subprocess
import sys
import tempfile
import time
import urllib
import urllib2

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup as BeautifulSoup_
    # Use html5lib for parsing if available
    try:
        import html5lib
        BeautifulSoup = lambda page: BeautifulSoup_(page, 'html5lib')
    except ImportError:
        BeautifulSoup = BeautifulSoup_

csrftoken = ''
session = ''
AUTH_URL = 'https://www.coursera.org/maestro/api/user/login'

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


def get_syllabus_url(className, preview):
    """
    Return the Coursera index/syllabus URL.
    """
    classType = 'preview' if preview else 'index'
    return 'https://class.coursera.org/%s/lecture/%s' % (className, classType)


def write_cookie_file(className, username, password, preview):
    """
    Automatically generate a cookie file for the Coursera site.
    """
    try:
        hn, fn = tempfile.mkstemp()
        cookies = cookielib.LWPCookieJar()
        handlers = [
            urllib2.HTTPHandler(),
            urllib2.HTTPSHandler(),
            urllib2.HTTPCookieProcessor(cookies)
        ]
        opener = urllib2.build_opener(*handlers)

        req = urllib2.Request(get_syllabus_url(className, preview))
        opener.open(req)

        csrftoken = None
        for cookie in cookies:
            if cookie.name == 'csrf_token':
                csrftoken = cookie.value
                break
        opener.close()

        if not csrftoken:
            raise AuthenticationFailed('Did not recieve csrf_token cookie.')

        # Now make a call to the authenticator url:
        cj = cookielib.MozillaCookieJar(fn)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj),
                                      urllib2.HTTPHandler(),
                                      urllib2.HTTPSHandler())

        # Preparation of headers and of data that we will send in a POST
        # request.
        std_headers = {
            'Cookie': ('csrftoken=%s' % csrftoken),
            'Referer': 'https://www.coursera.org',
            'X-CSRFToken': csrftoken,
            }

        auth_data = {
            'email_address': username,
            'password': password
            }

        formatted_data = urllib.urlencode(auth_data)

        req = urllib2.Request(AUTH_URL, formatted_data, std_headers)

        opener.open(req)
    except urllib2.HTTPError as e:
        if e.code == 404:
            raise ClassNotFound(className)
        else:
            raise

    cj.save()
    opener.close()
    os.close(hn)
    return fn


def down_the_wabbit_hole(className, cj, preview):
    """
    Authenticate on class.coursera.org
    """
    quoted_class_url = urllib.quote_plus(get_syllabus_url(className, preview))
    url = 'https://class.coursera.org/%s/auth/auth_redirector' \
          '?type=login&subtype=normal&email=&visiting=%s'
    auth_redirector_url = url % (className, quoted_class_url)

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj),
                                  urllib2.HTTPHandler(),
                                  urllib2.HTTPSHandler())

    req = urllib2.Request(auth_redirector_url)
    opener.open(req)
    opener.close()


def set_session_and_csrftoken(className, cookies_file, preview):
    """
    Set the global variables
    """
    global csrftoken
    global session

    # At this moment we should have the following cookies on www.coursera.org:
    #     maestro_login_flag, sessionid, maestro_login
    # To access the class pages we need two cookies on class.coursera.org:
    #     csrf_token, session
    cj = get_cookie_jar(cookies_file)

    # First, check if we have the class.coursera.org cookies.
    extract_session_and_csrftoken_from_cookiejar(className, cj)

    if not (csrftoken and session):
        # Get the class.coursera.org cookies. Remember that we need
        # the cookies from www.coursera.org!
        down_the_wabbit_hole(className, cj, preview)

        extract_session_and_csrftoken_from_cookiejar(className, cj)

        if not (csrftoken and session):
            raise AuthenticationFailed('Did not find csrf_token or session cookie.')

    logging.info('Found authentication cookies.')


def extract_session_and_csrftoken_from_cookiejar(className, cj):
    """
    Extract the class.coursera.org cookies from the cookiejar.
    """
    global csrftoken
    global session

    path = "/" + className
    for cookie in cj:
        if cookie.domain == 'class.coursera.org' and cookie.path == path:
            if cookie.name == 'session':
                session = cookie.value
            if cookie.name == 'csrf_token':
                csrftoken = cookie.value


def get_config_paths(config_name, user_specified_path=None):
    """
    Returns a list of config files paths to try in order, given config file
    name and possibly a user-specified path
    """

    # For Windows platforms, there are several paths that can be tried to
    # retrieve the netrc file. There is, however, no "standard way" of doing
    # things.
    #
    # A brief recap of the situation (all file paths are written in Unix
    # convention):
    #
    # 1. By default, Windows does not define a $HOME path. However, some
    # people might define one manually, and many command-line tools imported
    # from Unix will search the $HOME environment variable first. This
    # includes MSYSGit tools (bash, ssh, ...) and Emacs.
    #
    # 2. Windows defines two 'user paths': $USERPROFILE, and the
    # concatenation of the two variables $HOMEDRIVE and $HOMEPATH. Both of
    # these paths point by default to the same location, e.g.
    # C:\Users\Username
    #
    # 3. $USERPROFILE cannot be changed, however $HOMEDRIVE and $HOMEPATH
    # can be changed. They are originally intended to be the equivalent of
    # the $HOME path, but there are many known issues with them
    #
    # 4. As for the name of the file itself, most of the tools ported from
    # Unix will use the standard '.dotfile' scheme, but some of these will
    # instead use "_dotfile". Of the latter, the two notable exceptions are
    # vim, which will first try '_vimrc' before '.vimrc' (but it will try
    # both) and git, which will require the user to name its netrc file
    # '_netrc'.
    #
    # Relevant links :
    # http://markmail.org/message/i33ldu4xl5aterrr
    # http://markmail.org/message/wbzs4gmtvkbewgxi
    # http://stackoverflow.com/questions/6031214/
    #
    # Because the whole thing is a mess, I suggest we tried various sensible
    # defaults until we succeed or have depleted all possibilities.

    if user_specified_path is not None:
        return [user_specified_path]

    if platform.system() != 'Windows':
        return [None]

    # a useful helper function that converts None to the empty string
    getenv_or_empty = lambda s: os.getenv(s) or ""

    # Now, we only treat the case of Windows
    env_vars = [["HOME"],
                ["HOMEDRIVE", "HOMEPATH"],
                ["USERPROFILE"],
                ["SYSTEMDRIVE"]]

    env_dirs = []
    for v in env_vars:
        directory = ''.join(map(getenv_or_empty, v))
        if not directory:
            logging.debug('Environment var(s) %s not defined, skipping', v)
        else:
            env_dirs.append(directory)

    additional_dirs = ["C:", ""]

    all_dirs = env_dirs + additional_dirs

    leading_chars = [".", "_"]

    res = [''.join([directory, os.sep, lc, config_name])
           for directory in all_dirs
           for lc in leading_chars]

    return res


def authenticate_through_netrc(user_specified_path=None):
    """
    Returns the tuple user / password given a path for the .netrc file
    """
    res = None
    errors = []
    paths_to_try = get_config_paths("netrc", user_specified_path)
    for p in paths_to_try:
        try:
            logging.debug('Trying netrc file %s', p)
            auths = netrc.netrc(p).authenticators('coursera-dl')
            res = (auths[0], auths[2])
            break
        except (IOError, TypeError, netrc.NetrcParseError) as e:
            errors.append(e)

    if res is None:
        for e in errors:
            logging.error(str(e))
        sys.exit(1)

    return res


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


def get_opener(cookies_file):
    """
    Use cookie file to create a url opener.
    """

    cj = get_cookie_jar(cookies_file)

    return urllib2.build_opener(urllib2.HTTPCookieProcessor(cj),
                                urllib2.HTTPHandler(),
                                urllib2.HTTPSHandler())


def get_page(url):
    """
    Download an HTML page using the cookiejar.
    """

    opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler())
    req = urllib2.Request(url)

    opener.addheaders.append(('Cookie', 'csrf_token=%s;session=%s' % (csrftoken, session)))
    try:
        ret = opener.open(req).read()
    except urllib2.HTTPError as e:
        logging.error("Error %s getting page %s", str(e), url)
        ret = ''

    # opener = get_opener(cookies_file)
    # ret = opener.open(url).read()
    opener.close()
    return ret


def grab_hidden_video_url(href):
    """
    Follow some extra redirects to grab hidden video URLs (like those from
    University of Washington).
    """

    page = get_page(href)
    soup = BeautifulSoup(page)
    l = soup.find('source', attrs={'type': 'video/mp4'})
    if l is not None:
        return l['src']
    else:
        return None


def get_syllabus(class_name, cookies_file, local_page=False, preview=False):
    """
    Get the course listing webpage.

    If we are instructed to use a local page and it already exists, then
    that page is used instead of performing a download.  If we are
    instructed to use a local page and it does not exist, then we download
    the page and save a copy of it for future use.
    """

    if not (local_page and os.path.exists(local_page)):
        url = get_syllabus_url(class_name, preview)
        page = get_page(url)
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


def get_video(url):
    """
    Parses a Coursera video page
    """

    page = get_page(url)
    soup = BeautifulSoup(page)
    return soup.find(attrs={'type': re.compile('^video/mp4')})['src']


def parse_syllabus(page, reverse=False):
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
                href = a['href']
                fmt = get_anchor_format(href)
                logging.debug('    %s %s', fmt, href)
                if fmt:
                    lecture[fmt] = href
                    continue

                # Special case: find preview URLs
                lecture_page = transform_preview_url(href)
                if lecture_page:
                    try:
                        lecture['mp4'] = get_video(lecture_page)
                    except TypeError:
                        logging.warn('Could not get resource: %s', lecture_page)

            # Special case: we possibly have hidden video links---thanks to
            # the University of Washington for that.
            if 'mp4' not in lecture:
                for a in vtag.findAll('a'):
                    if a.get('data-modal-iframe'):
                        href = grab_hidden_video_url(a['data-modal-iframe'])
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


def download_lectures(wget_bin,
                      curl_bin,
                      aria2_bin,
                      axel_bin,
                      cookies_file,
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

            # write lecture resources
            for fmt, url in [i for i in lecture.items() if i[0]
                             in file_formats or 'all'
                             in file_formats]:
                if combined_section_lectures_nums:
                    lecfn = os.path.join(sec, format_combine_number_resource(secnum + 1,
                                                         lecnum + 1, lecname, fmt))
                else:
                    lecfn = os.path.join(sec, format_resource(lecnum + 1, lecname, fmt))

                if overwrite or not os.path.exists(lecfn):
                    if not skip_download:
                        logging.info('Downloading: %s', lecfn)
                        download_file(url, lecfn, cookies_file, wget_bin,
                                      curl_bin, aria2_bin, axel_bin)
                    else:
                        open(lecfn, 'w').close()  # touch
                    last_update = time.time()
                else:
                    logging.info('%s already downloaded', lecfn)
                    # if this file hasn't been modified in a long time,
                    # record that time
                    last_update = max(last_update, os.path.getmtime(lecfn))

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


def download_file(url,
                  fn,
                  cookies_file,
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
            download_file_wget(wget_bin, url, fn)
        elif curl_bin:
            download_file_curl(curl_bin, url, fn)
        elif aria2_bin:
            download_file_aria2(aria2_bin, url, fn)
        elif axel_bin:
            download_file_axel(axel_bin, url, fn)
        else:
            download_file_nowget(url, fn, cookies_file)
    except KeyboardInterrupt:
        logging.info('Keyboard Interrupt -- Removing partial file: %s', fn)
        os.remove(fn)
        sys.exit()


def download_file_wget(wget_bin, url, fn):
    """
    Downloads a file using wget.  Could possibly use python to stream files
    to disk, but wget is robust and gives nice visual feedback.
    """

    cmd = [wget_bin, url, '-O', fn, '--no-cookies', '--header',
           "Cookie: csrf_token=%s; session=%s" % (csrftoken, session),
           '--no-check-certificate']
    logging.debug('Executing wget: %s', cmd)
    return subprocess.call(cmd)


def download_file_curl(curl_bin, url, fn):
    """
    Downloads a file using curl.  Could possibly use python to stream files
    to disk, but curl is robust and gives nice visual feedback.
    """

    cmd = [curl_bin, url, '-k', '-#', '-L', '-o', fn, '--cookie',
           "csrf_token=%s; session=%s" % (csrftoken, session)]
    logging.debug('Executing curl: %s', cmd)
    return subprocess.call(cmd)


def download_file_aria2(aria2_bin, url, fn):
    """
    Downloads a file using aria2.  Could possibly use python to stream files
    to disk, but aria2 is robust. Unfortunately, it does not give a nice
    visual feedback, bug gets the job done much faster than the
    alternatives.
    """

    cmd = [aria2_bin, url, '-o', fn, '--header',
           "Cookie: csrf_token=%s; session=%s" % (csrftoken, session),
           '--check-certificate=false', '--log-level=notice',
           '--max-connection-per-server=4', '--min-split-size=1M']
    logging.debug('Executing aria2: %s', cmd)
    return subprocess.call(cmd)


def download_file_axel(axel_bin, url, fn):
    """
    Downloads a file using axel.  Could possibly use python to stream files
    to disk, but axel is robust and it both gives nice visual feedback and
    get the job done fast.
    """

    cmd = [axel_bin, '-H', "Cookie: csrf_token=%s; session=%s" % (csrftoken, session),
           '-o', fn, '-n', '4', '-a', url]
    logging.debug('Executing axel: %s', cmd)
    return subprocess.call(cmd)


def download_file_nowget(url, fn, cookies_file):
    """
    'Native' python downloader -- slower than wget.

    For consistency with subprocess.call, returns 0 to indicate success and
    1 to indicate problems.
    """

    logging.info('Downloading %s -> %s', url, fn)

    attempts_count = 0
    error_msg = ''
    while (attempts_count < 5):
        try:
            opener = get_opener(cookies_file)
            opener.addheaders.append(('Cookie', 'csrf_token=%s;session=%s' %
                                  (csrftoken, session)))
            urlfile = opener.open(url)
        except urllib2.HTTPError as e:
            logging.warn('Probably the file is missing from the AWS repository...'
                         ' waiting.')

            if hasattr(e, 'reason'):
                error_msg = e.reason + ' ' + str(e.code)
            else:
                error_msg = 'HTTP Error ' + str(e.code)

            wait_interval = 2 ** (attempts_count + 1)
            print 'Error to downloading, will retry in %s seconds ...' % wait_interval
            time.sleep(wait_interval)
            attempts_count += 1
            continue
        else:
            bw = BandwidthCalc()
            chunk_sz = 1048576
            bytesread = 0
            with open(fn, 'wb') as f:
                while True:
                    data = urlfile.read(chunk_sz)
                    if not data:
                        print '.'
                        break
                    bw.received(len(data))
                    f.write(data)
                    bytesread += len(data)
                    print '\r%d bytes read%s' % (bytesread, bw),
                    sys.stdout.flush()
            urlfile.close()
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
                        default=None,
                        help='use netrc for reading passwords, uses default'
                             ' location if no path specified')

    # required if username selected above
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
    parser.add_argument('-w',
                        '--wget_bin',
                        dest='wget_bin',
                        action='store',
                        default=None,
                        help='wget binary if it should be used for downloading')
    parser.add_argument('--curl_bin',
                        dest='curl_bin',
                        action='store',
                        default=None,
                        help='curl binary if it should be used for downloading')
    parser.add_argument('--aria2_bin',
                        dest='aria2_bin',
                        action='store',
                        default=None,
                        help='aria2 binary if it should be used for downloading')
    parser.add_argument('--axel_bin',
                        dest='axel_bin',
                        action='store',
                        default=None,
                        help='axel binary if it should be used for downloading')
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

    # check arguments
    if args.cookies_file and not os.path.exists(args.cookies_file):
        logging.error('Cookies file not found: %s', args.cookies_file)
        sys.exit(1)

    if not args.cookies_file and not args.username:
        args.username, args.password = authenticate_through_netrc(args.netrc)

    if args.username and not args.password:
        args.password = getpass.getpass('Coursera password for %s: '
                                        % args.username)

    return args


def download_class(args, class_name):
    """
    Download all requested resources from the class given in class_name.
    Returns True if the class appears completed.
    """

    if args.username:
        tmp_cookie_file = write_cookie_file(class_name, args.username,
                                            args.password, args.preview)

    cookies_file = args.cookies_file or tmp_cookie_file

    set_session_and_csrftoken(class_name, cookies_file, args.preview)

    # get the syllabus listing
    page = get_syllabus(class_name, cookies_file,
                        args.local_page, args.preview)

    # parse it
    sections = parse_syllabus(page, args.reverse)

    # obtain the resources
    completed = download_lectures(
                      args.wget_bin,
                      args.curl_bin,
                      args.aria2_bin,
                      args.axel_bin,
                      cookies_file,
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
                      )

    if not args.cookies_file:
        os.unlink(tmp_cookie_file)

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
        except urllib2.HTTPError as e:
            logging.error('Could not download class: %s', e)
        except ClassNotFound as cnf:
            logging.error('Could not find class: %s', cnf)
        except AuthenticationFailed as af:
            logging.error('Could not authenticate: %s', af)

    if completed_classes:
        logging.info("Classes which appear completed: " + " ".join(completed_classes))


if __name__ == '__main__':
    main()
