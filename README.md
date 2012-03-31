Coursera Downloader
===================

[Coursera] is creating some fantastic, free educational classes (e.g., algorithms, machine learning, natural language processing, SaaS).  This script allows one to batch download lecture resources (e.g., videos, ppt, etc) for a Coursera class.  Given a class name and related cookie file, it scrapes the course listing page to get the week and class names, and then downloads the related materials into appropriately named files and directories.

Why is this helpful?  Before I was using *wget*, but I had the following problems:

  1. Video names have a number in them, but this does not correspond to the actual order.  Manually renaming them is a pain.
  2. Using names from the syllabus page provides more informative names.
  3. Using a wget in a forloop picks up extra videos which are not posted/linked, and these are sometimes duplicates.

*DownloadThemAll* can also work, but this provides better names.

Features:

  * Intentionally detailed names, so that it will display and sort properly
    on most interfaces (e.g., MX Video on Andriod phone).
  * Regex-based section (week) and lecture name filters to download only
    certain resources.
  * File format extension filter to grab resource types you want.
  * Tested on both Linux and Windows.

Inspired in part by [youtube-dl] by which I've downloaded many other good videos such those from Khan Academy.  


Directions
----------

Requires Python 2.x (where x >= 5) and a free Coursera account.

1. Install any missing dependencies.

  a. [Beautiful Soup 3]
    Ubuntu/Debian: `sudo apt-get install python-beautifulsoup`
    Other*: `easy_install BeautifulSoup`

  b. [Argparse] (Not necessary if Python version >= 2.7)
    Ubuntu/Debian: `sudo apt-get install python-argparse`
    Other*: `easy_install argparse`

  c. [wget] (needed on Windows)
    This is a temporary workaround as currently the python download 
    has a problem.
    
    \* To install *easy_install*:
    Ubuntu: `sudo apt-get install python-setuptools`
    Windows: http://pypi.python.org/pypi/setuptools  

2. Create a Coursera.org account and login.
    e.g. http://saas-class.org

3. Locate or export your Netscape-style cookies file with a browser extension.
    Chrome: [Cookie.txt Export]
    Firefox: [Export Cookies 1.2]
      

4. Run the script to download the materials.
    Linux:
      `coursera-dl saas -c cookies.txt`
    Filter by section name:
      `coursera-dl saas -c cookies.txt -sf "Chapter_Four"`
    Filter by lecture name:
      `coursera-dl saas -c cookies.txt -lf "3.1_"`
    Download only ppt files:
      `coursera-dl saas -c cookies.txt -f "ppt"`
    Windows:
      You need to use wget right now.
      `coursera-dl saas -c cookies.txt -w C:\...\wget.exe`


Troubleshooting
---------------

If it's finding 0 sections, you probably have a bad cookies file.
Use -l listing.html and then examine that file -- if it's the non-logged-in
page then this is definitely your problem.

Tested on:

  * Ubuntu/Python 2.6.5
  * Win7/Python2.5 (with wget)


Contact
-------
Send any questions, comments, or problems to:
John Lehmann: first last at geemail dotcom or [@jplehmann]
  


[@jplehmann]: www.twitter.com/jplehmann
[Cookie.txt Export]: https://chrome.google.com/webstore/detail/lopabhfecdfhgogdbojmaicoicjekelh
[youtube-dl]: http://rg3.github.com/youtube-dl
[Coursera]: http://www.coursera.org
[Beautiful Soup 3]: http://www.crummy.com/software/BeautifulSoup
[Argparse]: http://pypi.python.org/pypi/argparse
[wget]: http://sourceforge.net/projects/gnuwin32/files/wget/1.11.4-1/wget-1.11.4-1-setup.exe
[Export Cookies 1.2]: https://addons.mozilla.org/en-US/firefox/addon/export-cookies
