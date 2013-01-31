Coursera Downloader
===================

[Coursera][1] is creating some fantastic, free educational classes (e.g.,
algorithms, machine learning, natural language processing, SaaS).  This
script allows one to batch download lecture resources (e.g., videos, ppt,
etc) for a Coursera class.  Given a class name and related cookie file, it
scrapes the course listing page to get the week and class names, and then
downloads the related materials into appropriately named files and
directories.

Why is this helpful?  Before I was using [*wget*][2], but I had the
following problems:

1. Video names have a number in them, but this does not correspond to the
   actual order.  Manually renaming them is a pain.
2. Using names from the syllabus page provides more informative names.
3. Using a wget in a for loop picks up extra videos which are not
   posted/linked, and these are sometimes duplicates.

*DownloadThemAll* can also work, but this provides better names.

Inspired in part by [youtube-dl][3] by which I've downloaded many other good
videos such as those from Khan Academy.


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

Requires Python 2.6 (or newer) and a free Coursera account enrolled in
the class of interest.

1\. Install any missing dependencies.

  * [Beautiful Soup 3][4] or [Beautiful Soup 4][5]
    - Ubuntu/Debian for BS3: `sudo apt-get install python-beautifulsoup`
    - Ubuntu/Debian for BS4: `sudo apt-get install python-bs4`
    - Mac OSX: `bs4` may be required instead.
    - Other: `easy_install BeautifulSoup`
  * [Argparse][6]: Only necessary if using Python 2.6.
    - Ubuntu/Debian: `sudo apt-get install python-argparse`
    - Other: `easy_install argparse`
  * [easy_install][7]: Only necessary if not using prepackaged dependencies.
    - Ubuntu/Debian: `sudo apt-get install python-setuptools`

On Mac OSX using MacPort, the following may be used:

    port
    > install py-beautifulsoup
    > install py-argparse
    > install py24-distribute  # for "py-setuptools", the obsolete name

If you are using pip, you can directly install all the dependencies from the
requirements file using `pip install -r requirements.txt`.

2\. Create a Coursera.org account and enroll in a class.
e.g. http://saas-class.org

3\. Run the script to download the materials by providing your Coursera
username, password (or a `~/.netrc` file), the class names

    General:                     coursera-dl -u <user> -p <pass> saas
    Multiple classes:            coursera-dl -u <user> -p <pass> saas nlp ml
    Filter by section name:      coursera-dl -u <user> -p <pass> -sf "Chapter_Four" saas
    Filter by lecture name:      coursera-dl -u <user> -p <pass> -lf "3.1_" saas
    Download only ppt files:     coursera-dl -u <user> -p <pass> -f "ppt" saas
    Use a ~/.netrc file:         coursera-dl -n saas
    Specify download path:       coursera-dl -n --path=C:\Coursera\Classes\ saas

On \*nix platforms\*, the use of a `~/.netrc` file is a good alternative to
specifying both your username and password every time on the command
line. To use it, simply add a line like the one below to a file named
`.netrc` in your home directory (or the [equivalent][8], if you are using
Windows) with contents like:

    machine coursera-dl login <user> password <pass>

Create the file if it doesn't exist yet.  From then on, you can switch from
using `-u` and `-p` to simply call `coursera-dl` with the option `-n`
instead.  This is especially convenient, as typing usernames and passwords
directly on the command line can get tiresome (even more if you happened to
choose a "strong" password).

\* if this works on Windows, please add additional instructions for it if
any are needed.

Troubleshooting
---------------

* When reporting bugs against `coursera-dl`, please don't forget to include
  enough information so that you can help us help you:
  - Is the problem happening with the latest version of the script?
  - What is the course that you are trying to access:
  - What is the precise command line that you are using (feel free to hide
    your username and password with asterisks, but leave all other
    information untouched).
  - What are the precise messages that you get? Please, copy and past them.
    Don't reword the messages.

* Make sure the classname you are using corresponds to the resource name used in
  the URL for that class:
    `https://class.coursera.org/<CLASS_NAME>/class/index`

* Previously one could export a Netscape-style cookies file with a browser
  extension ([1][9], [2][10]) for use with the `-c` option, but this
  approach does not appear to work with recent classes. Use the `-u` and
  `-p` flags instead or use the `-n` flag.

* If results show 0 sections, you most likely have provided invalid
  credentials (username and/or password in the command line or in your
  `.netrc` file).


Contact
-------

Post bugs and issues on [github][11]. Send other comments to John Lehmann:
first last at geemail dotcom or [@jplehmann][12]

[1]: https://www.coursera.org
[2]: http://sourceforge.net/projects/gnuwin32/files/wget/1.11.4-1/wget-1.11.4-1-setup.exe
[3]: https://rg3.github.com/youtube-dl
[4]: http://www.crummy.com/software/BeautifulSoup/bs3
[5]: http://www.crummy.com/software/BeautifulSoup
[6]: http://pypi.python.org/pypi/argparse
[7]: http://pypi.python.org/pypi/setuptools
[8]: http://stackoverflow.com/a/6031266/962311
[9]: https://chrome.google.com/webstore/detail/lopabhfecdfhgogdbojmaicoicjekelh
[10]: https://addons.mozilla.org/en-US/firefox/addon/export-cookies
[11]: https://github.com/jplehmann/coursera/issues
[12]: https://twitter.com/jplehmann
