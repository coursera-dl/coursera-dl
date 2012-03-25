#!/usr/bin/env python
"""
For downloading videos for Coursera classes. Given a class name and related cookie file, it scrapes the course listing page to get the week and class names, and then downloads the related videos into appropriately named files and directories.

Tested on Python 2.6.5.

Dependencies:
- BeautifulSoup 3
- argparser         # sudo easy_install argparse
- wget

Other:
- must point script at your browser's cookie file for authentication
  to coursera.org
  - Chrome users use "cookie.txt export" extension
"""

import sys, os, re
import urllib2
import cookielib 
import tempfile
import subprocess
import string
import argparse
from collections import namedtuple
from BeautifulSoup import BeautifulSoup        

COURSERA_INDEX = "http://www.coursera.org/%s/lecture/index"

def get_index_url(className):
  """Return the Coursera index/syllabus URL."""
  return COURSERA_INDEX  % className

def get_cookies_file(cookies_file):
  """Loads the cookies file. I am pre-pending the file with the special
  Netscape header because the cookie loader is being very particular about this
  string."""
  NETSCAPE_HEADER = "# Netscape HTTP Cookie File"
  cookies = tempfile.NamedTemporaryFile()
  cookies.write(NETSCAPE_HEADER)
  cookies.write(open(cookies_file, 'r').read())
  cookies.flush()
  return cookies

def get_page(url, cookies_file):
  """Download an HTML page using the cookiejar."""
  cj = cookielib.MozillaCookieJar()
  cookies = get_cookies_file(cookies_file)
  cj.load(cookies.name)
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
  return opener.open(url).read()

def clean_filename(s):
  """Sanitize a string to be used as a filename."""
  # strip paren portions which contain trailing time length (...)
  s = re.sub("\(.*", "", s)
  s = s.strip().replace(':','-').replace(' ', '_')
  valid_chars = "-_.()%s%s" % (string.ascii_letters, string.digits)
  return ''.join(c for c in s if c in valid_chars)

def parse_page(page):
  """Parses a Coursera course listing/syllabus page."""
  # a section corresponds to a week of classes
  Section = namedtuple('Section', 'name videos')
  Video = namedtuple('Video', 'name url')
  sections = []
  videos = []
  section_name = None
  soup = BeautifulSoup(page)

  def push(sections, videos):
    if (videos):
      sections.append(Section(section_name, videos))
      return []
    return videos
    
  # sections and videos are interspersed
  for tag in soup.findAll(attrs={"class":
                         re.compile('^(list_header$|item_row )')}):
    # section
    if tag.string != None:
      videos = push(sections, videos)
      section_name = clean_filename(tag.string)
      print section_name
    # video
    else:
      assert tag.a.contents[0], "couldn't get video name"
      vname = clean_filename(tag.a.contents[0])
      print "  ", vname,
      # find the anchor with .mp4 reference
      url = tag.find("a", {"href":re.compile("\.mp4")})["href"]
      print "  ", url
      videos.append(Video(vname, url))
  push(sections, videos)
  return sections

def download_videos(cookies_file, class_name, sections, overwrite=False, skip_download=False):
  """Downloads videos described by sections."""

  def format_section(num, section):
    return "%s_%02d_%s" % (class_name.upper(), num, section)

  def format_video(num, video):
    return "%02d_%s.mp4" % (num, video)

  for (weeknum, (section, videos)) in enumerate(sections, 1):
    sec = format_section(weeknum, section)
    if not os.path.exists(sec):
      os.mkdir(sec)
    for (vidnum, (vname, url)) in enumerate(videos, 1):
      vidfn = os.path.join(sec, format_video(vidnum, vname))
      if overwrite or not os.path.exists(vidfn):
        if not skip_download: 
          download_file(url, vidfn, cookies_file)
        else: 
          open(vidfn, 'w').close()  # touch

def download_file(url, fn, cookies_file):
  """Downloads a file using wget.  Could possibly use python to stream files to
  disk, but wget is robust and gives nice visual feedback."""
  cmd = ["wget", url, "-O", fn, "--load-cookies", cookies_file]
  print "Executing wget:", cmd 
  retcode = subprocess.call(cmd)

def get_syllabus(class_name, cookies_file, local_page=False):
  # get the page from the web
  if (not local_page or not os.path.exists(local_page)):
    page = get_page(get_index_url(class_name), cookies_file)
    print "Downloaded course page: %d bytes" % len(page)
    # cache the page if we're in 'local' mode
    if (local_page):
      open(local_page, 'w').write(page)
  else:
    page = open(local_page).read()
  return page

def parseArgs():
  parser = argparse.ArgumentParser(description='Download Coursera.org videos.')
  # positional
  parser.add_argument('class_name', action='store', 
    help='name of the class (e.g. "nlp")')
  # required
  parser.add_argument('-c', '--cookies_file', dest='cookies_file', 
    action='store', required=True, help='full path to the cookies.txt file')
  # optional
  parser.add_argument('-o', '--overwrite', dest='overwrite', 
    action='store_true', default=False, 
    help='whether existing video files should be overwritten (default: False)')
  parser.add_argument('-l', '--process_local_page', dest='local_page', 
    help='for debugging: uses or creates local cached version of syllabus page')
  parser.add_argument('--skip-download', dest='skip_download', 
    action='store_true', default=False, 
    help='for debugging: skip actual downloading of videos')
  args = parser.parse_args()
  # check arguments
  if not os.path.exists(args.cookies_file):
    raise IOError("Cookies file not found: " + args.cookies_file)
  return args

def main():
  args = parseArgs()
  page = get_syllabus(args.class_name, args.cookies_file, args.local_page)
  sections = parse_page(page)
  download_videos(args.cookies_file, args.class_name, sections, args.overwrite, args.skip_download)

if __name__ == "__main__":
  main()
