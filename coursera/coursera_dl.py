#!/usr/bin/env python
"""
For downloading lecture resources such as videos for Coursera classes. Given
a class name, username and password, it scrapes the coarse listing page to
get the section (week) and lecture names, and then downloads the related
materials into appropriately named files and directories.

Examples:
  coursera-dl -u <user> -p <passwd> saas
  coursera-dl -u <user> -p <passwd> -l listing.html -o saas --skip-download

Author:
  John Lehmann (first last at geemail dotcom or @jplehmann)

Contributions are welcome, but please add new unit tests to test your changes
and/or features.  Also, please try to make changes platform independent and
backward compatible.
"""

import argparse
import cookielib
import errno
import getpass
import logging
import netrc
import os
import re
import string
import StringIO
import subprocess
import sys
import tempfile
import urllib
import urllib2
import platform

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    # for OSX, bs4 is recommended
    from bs4 import BeautifulSoup


class ClassNotFoundException(BaseException):
  """
  Class to be thrown if a course is not found in coursera's site.
  """
  pass


def get_syllabus_url(className):
  """
  Return the Coursera index/syllabus URL.
  """
  return "http://class.coursera.org/%s/lecture/index" % className


def get_auth_url(className):
  return "http://class.coursera.org/%s/auth/auth_redirector?type=login&subtype=normal&email=&visiting=&minimal=true" % className


def write_cookie_file(className, username, password):
  """
  Automatically generate a cookie file for the coursera site.
  """
  try:
    (hn, fn) = tempfile.mkstemp()
    cj = cookielib.MozillaCookieJar(fn)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj),
                                  urllib2.HTTPHandler())

    req = urllib2.Request(get_auth_url(className))
    ref = opener.open(req).geturl()

    data = urllib.urlencode({'email': username,
                             'password': password,
                             'login': 'Login'})
    req = urllib2.Request(ref, data)

    opener.open(req)
  except Exception as e:
    if '404' in str(e):
      raise ClassNotFoundException(className)

  cj.save()
  opener.close()
  os.close(hn)

  return fn

def get_netrc_path(path=None):
  """
  Loads netrc file from given path or default location
  """
  if not path and platform.system() == 'Windows':
    # set some sane default on windows
    if os.path.isfile('_netrc'):
      path = '_netrc'
    else:
      profilepath = os.getenv('USERPROFILE')
      if profilepath:
        path = '%s\\_netrc' % profilepath
      else:
        path = '\\_netrc'
    return path


def load_cookies_file(cookies_file):
  """
  Loads the cookies file. I am pre-pending the file with the special
  Netscape header because the cookie loader is being very particular about
  this string.
  """
  cookies = StringIO.StringIO()
  NETSCAPE_HEADER = "# Netscape HTTP Cookie File"
  cookies.write(NETSCAPE_HEADER)
  cookies.write(open(cookies_file, 'r').read())
  cookies.flush()
  cookies.seek(0)
  return cookies


def get_opener(cookies_file):
  """
  Use cookie file to create a url opener.
  """
  cj = cookielib.MozillaCookieJar()
  cookies = load_cookies_file(cookies_file)
  # nasty hack: cj.load() requires a filename not a file, but if
  # I use stringio, that file doesn't exist. I used NamedTemporaryFile
  # before, but encountered problems on Windows.
  cj._really_load(cookies, "StringIO.cookies", False, False)
  return urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))


def get_page(url, cookies_file):
  """
  Download an HTML page using the cookiejar.
  """
  opener = get_opener(cookies_file)
  ret = opener.open(url).read()
  opener.close()
  return ret


def grab_hidden_video_url(href, cookies_file):
  """
  Follow some extra redirects to grab hidden video URLs (like those from
  University of Washington).
  """
  page = get_page(href, cookies_file)
  soup = BeautifulSoup(page)
  l = soup.find('source', attrs={'type': 'video/mp4'})
  return l['src']


def get_syllabus(class_name, cookies_file, local_page=False):
  """
  Get the course listing webpage.
  """
  if not (local_page and os.path.exists(local_page)):
    url = get_syllabus_url(class_name)
    page = get_page(url, cookies_file)
    logging.info("Downloaded %s (%d bytes)", url, len(page))
    # cache the page if we're in 'local' mode
    if local_page:
      open(local_page, 'w').write(page)
  else:
    page = open(local_page).read()
    logging.info("Read (%d bytes) from local file", len(page))
  return page


def clean_filename(s):
  """
  Sanitize a string to be used as a filename.
  """
  # strip paren portions which contain trailing time length (...)
  s = re.sub("\([^\(]*$", "", s)
  s = s.strip().replace(':', '-').replace(' ', '_')
  s = s.replace('nbsp', '')
  valid_chars = "-_.()%s%s" % (string.ascii_letters, string.digits)
  return ''.join(c for c in s if c in valid_chars)


def get_anchor_format(a):
  """
  Extract the resource file-type format from the anchor
  """
  # (. or format=) then (file_extension) then (? or $)
  # e.g. "...format=txt" or "...download.mp4?..."
  fmt = re.search("(?:\.|format=)(\w+)(?:\?.*)?$", a)
  return fmt.group(1) if fmt else None


def parse_syllabus(page, cookies_file):
  """
  Parses a Coursera course listing/syllabus page.  Each section is a week of
  classes.
  """
  sections = []
  soup = BeautifulSoup(page)
  # traverse sections
  for stag in soup.findAll(attrs={'class': re.compile('^course-item-list-header')}):
    assert stag.contents[0] is not None, "couldn't find section"
    section_name = clean_filename(stag.contents[0].contents[1])
    logging.info(section_name)
    lectures = [] # resources for 1 lecture
    # traverse resources (e.g., video, ppt, ..)
    for vtag in stag.nextSibling.findAll('li'):
      assert vtag.a.contents[0], "couldn't get lecture name"
      vname = clean_filename(vtag.a.contents[0])
      logging.info("  %s", vname)
      lecture = {}
      for a in vtag.findAll('a'):
        href = a['href']
        fmt = get_anchor_format(href)
        logging.info("    %s %s", fmt, href)
        if fmt:
          lecture[fmt] = href

      # Special case: we possibly have hidden video links---thanks to the
      # University of Washington for that.
      if 'mp4' not in lecture:
        for a in vtag.findAll('a'):
          if a.get('data-lecture-view-link'):
            href = grab_hidden_video_url(a['data-lecture-view-link'],
                                         cookies_file)
            fmt = 'mp4'
            logging.info("    %s %s", fmt, href)
            lecture[fmt] = href

      lectures.append((vname, lecture))
    sections.append((section_name, lectures))
  logging.info("Found %d sections and %d lectures on this page",
    len(sections), sum((len(s[1]) for s in sections)))
  if not len(sections):
    logging.error("Probably bad cookies file (or wrong class name)")
  return sections


def mkdir_p(path):
    """
    Create subdirectory hierarcy given in the paths argument.
    """
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
          raise


def download_lectures(
  wget_bin,
  curl_bin,
  aria2_bin,
  cookies_file,
  class_name,
  sections,
  file_formats,
  overwrite=False,
  skip_download=False,
  section_filter=None,
  lecture_filter=None,
  path='',
  verbose_dirs=False
  ):
  """
  Downloads lecture resources described by sections.
  """

  def format_section(num, section):
    sec = "%02d_%s" % (num, section)
    if verbose_dirs:
      sec = class_name.upper() + "_" + sec
    return sec

  def format_resource(num, name, fmt):
    return "%02d_%s.%s" % (num, name, fmt)

  for (secnum, (section, lectures)) in enumerate(sections):
    if section_filter and not re.search(section_filter, section):
      logging.debug("Skipping b/c of sf: %s %s", section_filter, section)
      continue
    sec = os.path.join(path, class_name, format_section(secnum + 1, section))
    for (lecnum, (lecname, lecture)) in enumerate(lectures):
      if lecture_filter and not re.search(lecture_filter, lecname):
        continue
      if not os.path.exists(sec):
          mkdir_p(sec)
      # write lecture resources
      for fmt, url in [i for i in lecture.items()
                       if ((i[0] in file_formats) or "all" in file_formats)]:
        lecfn = os.path.join(sec, format_resource(lecnum + 1, lecname, fmt))
        logging.info(lecfn)
        if overwrite or not os.path.exists(lecfn):
          if not skip_download:
            download_file(url, lecfn, cookies_file,
                          wget_bin, curl_bin, aria2_bin)
          else:
            open(lecfn, 'w').close()  # touch


def download_file(url, fn, cookies_file, wget_bin, curl_bin, aria2_bin):
  """
  Downloads file and removes current file if aborted by user.
  """
  try:
    if wget_bin:
      download_file_wget(wget_bin, url, fn, cookies_file)
    elif curl_bin:
      download_file_curl(curl_bin, url, fn, cookies_file)
    elif aria2_bin:
      download_file_aria2(aria2_bin, url, fn, cookies_file)
    else:
      download_file_nowget(url, fn, cookies_file)
  except KeyboardInterrupt:
    logging.info("Keyboard Interrupt -- Removing partial file: %s", fn)
    os.remove(fn)
    sys.exit()


def download_file_wget(wget_bin, url, fn, cookies_file):
  """
  Downloads a file using wget.  Could possibly use python to stream files to
  disk, but wget is robust and gives nice visual feedback.
  """
  cmd = [wget_bin, url, "-O", fn, "--load-cookies",
         cookies_file, "--no-check-certificate"]
  logging.debug("Executing wget: %s", cmd)
  subprocess.call(cmd)


def download_file_curl(curl_bin, url, fn, cookies_file):
  """
  Downloads a file using curl.  Could possibly use python to stream files to
  disk, but curl is robust and gives nice visual feedback.
  """
  cmd = [curl_bin, url, "-k", "-L", "-o", fn, "--cookie", cookies_file]
  logging.debug("Executing curl: %s", cmd)
  subprocess.call(cmd)


def download_file_aria2(aria2_bin, url, fn, cookies_file):
  """
  Downloads a file using aria2.  Could possibly use python to stream files
  to disk, but aria2 is robust. Unfortunately, it does not give a nice
  visual feedback, bug gets the job done much faster than the alternatives.
  """
  cmd = [aria2_bin, url, "-o", fn, "--load-cookies", cookies_file,
         "--check-certificate=false", "--log-level=notice",
         "--max-connection-per-server=4", "--min-split-size=1M"]
  logging.debug("Executing aria2: %s", cmd)
  subprocess.call(cmd)


def download_file_nowget(url, fn, cookies_file):
  """
  'Native' python downloader -- slower than wget.
  """
  logging.info("Downloading %s -> %s", url, fn)
  try:
    urlfile = get_opener(cookies_file).open(url)
  except urllib2.HTTPError:
    logging.warn("Probably the file is missing from the AWS repository... skipping it.")
  else:
    chunk_sz = 1048576
    bytesread = 0
    f = open(fn, "wb")
    while True:
	data = urlfile.read(chunk_sz)
        if not data:
          print "."
          break
        f.write(data)
        bytesread += len(data)
        print "\r%d bytes read" % bytesread,
        sys.stdout.flush()
    urlfile.close()


def parseArgs():
  """
  Parse the arguments/options passed to the program on the command line.
  """
  parser = argparse.ArgumentParser(
    description='Download Coursera.org lecture material and resources.')

  # positional
  parser.add_argument('class_names', action='store', nargs='+',
    help='name(s) of the class(es) (e.g. "nlp")')

  parser.add_argument('-c', '--cookies_file', dest='cookies_file',
    action='store', default=None, help='full path to the cookies.txt file')
  parser.add_argument('-u', '--username', dest='username',
    action='store', default=None, help='coursera username')
  parser.add_argument('-n', '--netrc', dest='netrc',
    action='store', default=None,
    help='use netrc for reading passwords, uses default location if no path specified')

  # required if username selected above
  parser.add_argument('-p', '--password', dest='password',
    action='store', default=None, help='coursera password')

  # optional
  parser.add_argument('-f', '--formats', dest='file_formats',
    action='store', default="all",
    help='file format extensions to be downloaded in quotes space separated, e.g. "mp4 pdf" (default: special value "all")')
  parser.add_argument('-sf', '--section_filter', dest='section_filter',
    action='store', default=None,
    help='only download sections which contain this regex (default: disabled)')
  parser.add_argument('-lf', '--lecture_filter', dest='lecture_filter',
    action='store', default=None,
    help='only download lectures which contain this regex (default: disabled)')
  parser.add_argument('-w', '--wget_bin', dest='wget_bin',
    action='store', default=None,
    help='wget binary if it should be used for downloading')
  parser.add_argument('--curl_bin', dest='curl_bin',
    action='store', default=None,
    help='curl binary if it should be used for downloading')
  parser.add_argument('--aria2_bin', dest='aria2_bin',
    action='store', default=None,
    help='aria2 binary if it should be used for downloading')
  parser.add_argument('-o', '--overwrite', dest='overwrite',
    action='store_true', default=False,
    help='whether existing files should be overwritten (default: False)')
  parser.add_argument('-l', '--process_local_page', dest='local_page',
    help='uses or creates local cached version of syllabus page')
  parser.add_argument('--skip-download', dest='skip_download',
    action='store_true', default=False,
    help='for debugging: skip actual downloading of files')
  parser.add_argument('--path', dest='path',
    action='store', default='',
    help='path to save the file')
  parser.add_argument('--verbose-dirs', dest='verbose_dirs',
    action='store_true', default=False,
    help='include class name in section directory name')
  parser.add_argument('--debug', dest='debug',
    action='store_true', default=False,
    help='print lots of debug information')
  parser.add_argument('--quiet', dest='quiet',
    action='store_true', default=False,
    help='omit as many messages as possible (only printing errors)')
  parser.add_argument('--add-class', dest='add_class',
    action='append', default=[],
    help='additional classes to get')
  args = parser.parse_args()

  # turn list of strings into list
  args.file_formats = args.file_formats.split()

  # check arguments
  if args.cookies_file and not os.path.exists(args.cookies_file):
    logging.error("Cookies file not found: %s", args.cookies_file)
    sys.exit(1)

  if not args.cookies_file and not args.username:
    path = get_netrc_path(args.netrc)
    try:
      auths = netrc.netrc(path).authenticators('coursera-dl')
      args.username = auths[0]
      args.password = auths[2]
    except Exception as e:
      logging.error("%s" % e)
      sys.exit(1)

  if args.username and not args.password:
    args.password = getpass.getpass("Coursera password for %s: " % args.username)

  if args.debug:
    logging.basicConfig(level=logging.DEBUG)
  elif args.quiet:
    logging.basicConfig(level=logging.ERROR)
  else:
    logging.basicConfig(level=logging.INFO)

  return args


def download_class(args, class_name):
  """
  Download all requested resources from the class given in class_name.
  """
  if args.username:
    tmp_cookie_file = write_cookie_file(class_name,
                                        args.username,
                                        args.password)
  # get the syllabus listing
  page = get_syllabus(class_name,
                      args.cookies_file or tmp_cookie_file,
                      args.local_page)
  # parse it
  sections = parse_syllabus(page,
                            args.cookies_file or tmp_cookie_file)

  # obtain the resources
  download_lectures(
    args.wget_bin,
    args.curl_bin,
    args.aria2_bin,
    args.cookies_file or tmp_cookie_file,
    class_name,
    sections,
    args.file_formats,
    args.overwrite,
    args.skip_download,
    args.section_filter,
    args.lecture_filter,
    args.path,
    args.verbose_dirs
  )

  if not args.cookies_file:
    os.unlink(tmp_cookie_file)


def main():
  """
  Main entry point for execution as a program (instead of as a module).
  """
  args = parseArgs()
  for class_name in args.class_names:
    try:
      logging.info("Downloading class: %s", class_name)
      download_class(args, class_name)
    except ClassNotFoundException as cnf:
      logging.error("Could not find class: %s", cnf)


if __name__ == "__main__":
  main()
