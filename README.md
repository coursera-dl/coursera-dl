Coursera Downloader
===================
[Coursera] is creating some fantastic, free educational classes (e.g., algorithms, machine learning, natural language processing, SaaS).  This script allows one to batch download lecture resources (e.g., videos, ppt, etc) for a Coursera class.  Given a class name and related cookie file, it scrapes the course listing page to get the week and class names, and then downloads the related materials into appropriately named files and directories.

Why is this helpful?  Before I was using *wget*, but I had the following problems:

1. Video names have a number in them, but this does not correspond to the actual order.  Manually renaming them is a pain.
2. Using names from the syllabus page provides more informative names.
3. Using a wget in a forloop picks up extra videos which are not posted/linked, and these are sometimes duplicates.

*DownloadThemAll* can also work, but this provides better names.  

Inspired in part by [youtube-dl] by which I've downloaded many other good videos such those from Khan Academy.  


Features
--------

  * Intentionally detailed names, so that it will display and sort properly
    on most interfaces (e.g., MX Video on Andriod phone).
  * Regex-based section (week) and lecture name filters to download only
    certain resources.
  * File format extension filter to grab resource types you want.
  * Tested on both Linux and Windows.


Directions
----------

Requires Python 2.x (where x >= 5) and a free Coursera account.

1. Install any missing dependencies.

  * [Beautiful Soup 3]  
  Ubuntu/Debian: `sudo apt-get install python-beautifulsoup`  
  Other: `easy_install BeautifulSoup`  
  * [Argparse] (Not necessary if Python version >= 2.7)  
  Ubuntu/Debian: `sudo apt-get install python-argparse`  
  Other: `easy_install argparse`  
  * [easy_install] (for the above)  
  Ubuntu: `sudo apt-get install python-setuptools`  
  
2. Create a Coursera.org account.
e.g. http://saas-class.org  

3. Login with your web browser.

4. Locate or export your Netscape-style cookies file with a browser extension.  
    Chrome: [Cookie.txt Export]  
    Firefox: [Export Cookies 1.2]  
      
5. Run the script to download the materials.  
    General:                 `coursera-dl saas -c cookies.txt`  
    Filter by section name:  `coursera-dl saas -c cookies.txt -sf "Chapter_Four"`  
    Filter by lecture name:  `coursera-dl saas -c cookies.txt -lf "3.1_"`  
    Download only ppt files: `coursera-dl saas -c cookies.txt -f "ppt"`  


Troubleshooting
---------------

* If it's finding 0 sections, you most likely have an invalid cookies file.
  * It's possible the cookies are already expired. This can happen very quickly.
    Try recreating your cookies.txt by logging in and re-copying the cookie file (step 3-5 above).  
  * If you get the error: "ValueError: need more than 1 value to unpack", the
    process or text editor you used to copy the cookie.txt probably converted the
    tabs to spaces.

* If you've tried recreating your cookies.txt and still have problems, please post to [issues].


Contact
-------
Post bugs and enhancement requests to [issues].  Send any other questions or comments to:  
John Lehmann: first last at geemail dotcom or [@jplehmann]  

  

[@jplehmann]: www.twitter.com/jplehmann
[Cookie.txt Export]: https://chrome.google.com/webstore/detail/lopabhfecdfhgogdbojmaicoicjekelh
[youtube-dl]: http://rg3.github.com/youtube-dl
[Coursera]: http://www.coursera.org
[Beautiful Soup 3]: http://www.crummy.com/software/BeautifulSoup
[Argparse]: http://pypi.python.org/pypi/argparse
[wget]: http://sourceforge.net/projects/gnuwin32/files/wget/1.11.4-1/wget-1.11.4-1-setup.exe
[Export Cookies 1.2]: https://addons.mozilla.org/en-US/firefox/addon/export-cookies
[easy_install]: http://pypi.python.org/pypi/setuptools
[issues]: https://github.com/jplehmann/coursera/issues
