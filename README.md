Coursera Downloader
===================
[Coursera] is creating some fantastic, free educational classes (e.g., algorithms, machine learning, natural language processing, SaaS).  This script allows one to batch download lecture resources (e.g., videos, ppt, etc) for a Coursera class.  Given a class name and related cookie file, it scrapes the course listing page to get the week and class names, and then downloads the related materials into appropriately named files and directories.

Why is this helpful?  Before I was using *wget*, but I had the following problems:

1. Video names have a number in them, but this does not correspond to the actual order.  Manually renaming them is a pain.
2. Using names from the syllabus page provides more informative names.
3. Using a wget in a for loop picks up extra videos which are not posted/linked, and these are sometimes duplicates.

*DownloadThemAll* can also work, but this provides better names.  

Inspired in part by [youtube-dl] by which I've downloaded many other good videos such as those from Khan Academy.


Features
--------

  * Intentionally detailed names, so that it will display and sort properly
    on most interfaces (e.g., MX Video on Android phone).
  * Regex-based section (week) and lecture name filters to download only
    certain resources.
  * File format extension filter to grab resource types you want.
  * Login credentials accepted on command-line or from `.netrc` file
  * Core functionality tested on Linux, Mac and Windows.


Directions
----------

Requires Python 2.x (where x >= 5) and a free Coursera account enrolled in the class of interest.

1\. Install any missing dependencies.

  * [Beautiful Soup 3]  
  Ubuntu/Debian: `sudo apt-get install python-beautifulsoup`  
  Mac OSX: bs4 may be required instead (modify import as well)
  Other: `easy_install BeautifulSoup`  
  * [Argparse] (Not necessary if Python version >= 2.7)  
  Ubuntu/Debian: `sudo apt-get install python-argparse`  
  Other: `easy_install argparse`  
  * [easy_install] (for the above)  
  Ubuntu: `sudo apt-get install python-setuptools`  

On Mac OSX using MacPort, the following may be used:

    port
    > install py-beautifulsoup
    > install py-argparse
    > install py24-distribute  # for "py-setuptools", the obsolete name
  
2\. Create a Coursera.org account and enroll in a class.
e.g. http://saas-class.org  

3\. Run the script to download the materials by providing your Coursera
username, password (or a `~/.netrc` file) and the class name.

    General:                     coursera-dl saas -u <user> -p <pass>
    Filter by section name:      coursera-dl saas -u <user> -p <pass> -sf "Chapter_Four"
    Filter by lecture name:      coursera-dl saas -u <user> -p <pass> -lf "3.1_"
    Download only ppt files:     coursera-dl progfun-2012-001 -u <user> -p <pass> -f "ppt"
    Use a ~/.netrc file:         coursera-dl progfun-2012-001 -n
    Specify download path:       coursera-dl progfun-2012-001 -n --path=C:\Coursera\Classes\
    Download multiple classes:   coursera-dl progfun-2012-001 -n --add-class=hetero-2012-001 --add-class=thinkagain-2012-001

On \*nix platforms\*, the use of a `~/.netrc` file is a good alternative to specifying both your username and password every time on the command line. To use it, simply add a line like the one below to a file named `.netrc` in your home directory (or the [equivalent], if you are using Windows) with contents like:

    machine coursera-dl login <user> password <pass>

Create the file if it doesn't exist yet.  From then on, you can switch from using `-u` and `-p` to simply call `coursera-dl` with the option `-n` instead.  This is especially convenient, as typing usernames and passwords directly on the command line can get tiresome (even more if you happened to choose a "strong" password).

\* if this works on Windows, please add additional instructions for it if any are needed.

Troubleshooting
---------------

* Make sure the classname you are using corresponds to the resource name used in
  the URL for that class:
    `https://class.coursera.org/<CLASS_NAME>/class/index`

* Previously one could export a Netscape-style cookies file with a browser
  extension ([1], [2]) for use with the `-c` option, but this approach does
  not appear to work with recent classes. Use the `-u` and `-p` flags
  instead or use the `-n` flag.

* If results show 0 sections, you most likely have provided invalid
  credentials (username and/or password in the command line or in your
  `.netrc` file).


Contact
-------
Post bugs and issues on [github].  Send other comments to John Lehmann: first last at geemail dotcom or [@jplehmann]  

  

[@jplehmann]: www.twitter.com/jplehmann
[1]: https://chrome.google.com/webstore/detail/lopabhfecdfhgogdbojmaicoicjekelh
[2]: https://addons.mozilla.org/en-US/firefox/addon/export-cookies
[youtube-dl]: http://rg3.github.com/youtube-dl
[Coursera]: http://www.coursera.org
[Beautiful Soup 3]: http://www.crummy.com/software/BeautifulSoup
[Argparse]: http://pypi.python.org/pypi/argparse
[wget]: http://sourceforge.net/projects/gnuwin32/files/wget/1.11.4-1/wget-1.11.4-1-setup.exe
[easy_install]: http://pypi.python.org/pypi/setuptools
[github]: https://github.com/jplehmann/coursera/issues
[workaround]: https://github.com/jplehmann/coursera/issues/6
[here]: https://github.com/wiedi/coursera
[equivalent]: http://stackoverflow.com/a/6031266/962311
