# Coursera Downloader

[![Build Status](https://travis-ci.org/jplehmann/coursera.png?branch=master)](https://travis-ci.org/jplehmann/coursera)

[Coursera][1] is arguably the leader in *massive open online courses* (MOOC)
with a selection of more than 300 classes from 62 different institutions [as of
February 2013][13]. Generous contributions by educators and institutions are
making excellent education available to many who could not afford it otherwise.
There are even non-profits with "feet on the ground" in remote areas of the
world who are helping spread the wealth (see the feedback below from [Tunapanda][14]).

This script makes it easier to batch download lecture resources (e.g., videos, ppt,
etc) for Coursera classes.  Given one or more class names and account credentials,
it obtains week and class names from the *lectures* page, and then downloads
the related materials into appropriately named files and directories.

Why is this helpful?  A utility like [`wget`][2] can work, but has the
following limitations:

1. Video names have a number in them, but this does not correspond to the
   actual order.  Manually renaming them is a pain.
2. Using names from the syllabus page provides more informative names.
3. Using a wget in a for loop picks up extra videos which are not
   posted/linked, and these are sometimes duplicates.

*DownloadThemAll* is another possiblity, but this script provides more features such
as appropriately named files.

This work was originally inspired in part by [youtube-dl][3] by which
I've downloaded many other good videos such as those from Khan Academy.


## Features

  * Intentionally detailed names, so that it will display and sort properly
    on most interfaces (e.g., MX Video on Android phone).
  * Regex-based section (week) and lecture name filters to download only
    certain resources.
  * File format extension filter to grab resource types you want.
  * Login credentials accepted on command-line or from `.netrc` file
  * Core functionality tested on Linux, Mac and Windows.


## Instructions

`coursera-dl` requires Python 2 (2.6 or newer) and a free Coursera account
enrolled in the class of interest.  *Note:* You must already have (manually)
agreed to the Honor of Code of the particular courses that you want to use
with `coursera-dl`.

1\. Install any missing dependencies.

  We strongly recommend that you consider installing Python packages with
  [`pip`][17], as in it is the current [preferred method][18].  If you are
  using `pip`, you can directly install all the dependencies from the
  requirements file using `pip install -r requirements.txt`.

  You may choose to install the dependencies yourself, but our users had
  issues that not all resources (videos etc.) were downloaded with versions
  of the dependencies different than those listed in the `requirements.txt`
  file.

  In any case, you may want to install:

  * [Beautiful Soup 4][5]: Required. See also html5lib below.
    - Ubuntu/Debian: `sudo apt-get install python-bs4`
    - Mac OSX + MacPorts: `sudo port install py-beautifulsoup4`
    - Other: `pip beautifulsoup4`
  * [Argparse][6]: Required (but you only need to install with Python 2.6)
    - Ubuntu/Debian: `sudo apt-get install python-argparse`
    - Other: `pip argparse`
  * [requests][16]: Required.
    - Ubuntu/Debian: `sudo apt-get install python-requests`
    - Mac OSX + MacPorts: `sudo port install requests`
    - Other: `pip requests`
  * [html5lib][15]: Not required, but recommended for parsing pages.
    - Ubuntu/Debian: `sudo apt-get install python-html5lib`
    - Mac OSX + MacPorts: `sudo port install py-html5lib`
    - Other: `pip html5lib`
  * [easy_install][7]: Only necessary if not using prepackaged
    dependencies. Also, `pip` supersedes it.
    - Ubuntu/Debian: `sudo apt-get install python-setuptools`

  Again, make sure that you have the versions mentioned in the file
  `requirements.txt` (later versions may be OK).

On Mac OSX using MacPorts, the following may be used:

    port
    > install py-beautifulsoup
    > install py-argparse
    > install py-setuptools

2\. Create a Coursera.org account and enroll in a class.
e.g. http://saas-class.org

3\. Run the script to download the materials by providing your Coursera
account (e.g., email address), password (or a `~/.netrc` file), the class names

    General:                     coursera-dl -u <user> -p <pass> saas
    Multiple classes:            coursera-dl -u <user> -p <pass> saas nlp proglang-2012-001
    Filter by section name:      coursera-dl -u <user> -p <pass> -sf "Chapter_Four" saas
    Filter by lecture name:      coursera-dl -u <user> -p <pass> -lf "3.1_" saas
    Download only ppt files:     coursera-dl -u <user> -p <pass> -f "ppt" saas
    Use a ~/.netrc file:         coursera-dl -n saas
    Get the preview classes:     coursera-dl -n -b saas
    Specify download path:       coursera-dl -n --path=C:\Coursera\Classes\ saas
    
    Maintain a list of classes in a dir:
      Initialize:              mkdir -p CURRENT/{class1,class2,..classN}
      Update:                  coursera-dl -n --path CURRENT `ls CURRENT`

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

## Troubleshooting

* When reporting bugs against `coursera-dl`, please don't forget to include
  enough information so that you can help us help you:
    * Is the problem happening with the latest version of the script?
    * What operating system are you using?
    * Do you have all the recommended versions of the modules? See them in
      the file `requirements.txt`.
    * What is the course that you are trying to access?
    * What is the precise command line that you are using (feel free to hide
      your username and password with asterisks, but leave all other
      information untouched).
    * What are the precise messages that you get? Please, copy and past them.
      Don't reword the messages.

* Make sure the classname you are using corresponds to the resource name used in
  the URL for that class:
    `https://class.coursera.org/<CLASS_NAME>/class/index`

* Make sure you have installed and/or updated all of your dependencies
  according to the `requirements.txt` file as described above.
 
* One can export a Netscape-style cookies file with a browser
  extension ([1][9], [2][10]) and use it with the `-c` option. This comes in
  handy when the authentication via password is not working (the
  authentication process changes now and then).

* If results show 0 sections, you most likely have provided invalid
  credentials (username and/or password in the command line or in your
  `.netrc` file).

* For courses that have not started yet, but have had a previous iteration
  sometimes a preview is available, containing all the classes from the
  last course. These files can be downloaded by passing the -b parameter.

* If you are using Beautiful Soup 4, make sure you have installed
  html5lib:

        $ python
        >>> import html5lib
        >>> print(html5lib.__version__)
        0.95-dev

* If you get an error like `Could not find class: <CLASS_NAME>`:
    * Verify that the name of the course is correct. Current class
      names in coursera are composed by a short course name e.g. `class`
      and the current version of the course (a number). For example, for a
      class named `class`, you would have to use `class-001`, `class-002`
      etc.
    * Second, verify that you are enrolled in the course. You won't be
      able to access the course materials if you are not officially
      enrolled and agreed to the honor course *via the website*.

## Feedback

I enjoy getting feedback. Here are a few of the comments I've received:

* "Thanks for the good job! Knowledge will flood the World a little more thanks
  to your script!"
  <br>Guillaume V. 11/8/2012
  
* "Just wanted to send you props for your Python script to download Coursera
  courses. I've been using it in Kenya for my non-profit to get online courses
  to places where internet is really expensive and unreliable. Mostly kids here
  can't afford high school, and downloading one of these classes by the usual
  means would cost more than the average family earns in one week. Thanks!"
  <br>Jay L., [Tunapanda][14] 3/20/2013

* "I am a big fan of Coursera and attend lots of different courses. Time
  constraints don't allow me to attend all the courses I want at the same time.
  I came across your script, and I am very happily using it!  Great stuff and
  thanks for making this available on Github - well done!"
  <br>William G.  2/18/2013
  
* "This script is awesome! I was painstakingly downloading each and every video
  and ppt by hand -- looked into wget but ran into wildcard issues with HTML,
  and then.. I came across your script.  Can't tell you how many hours you've
  just saved me :) If you're ever in Paris / Stockholm, it is absolutely
  mandatory that I buy you a beer :)"
  <br>Razvan T. 11/26/2012

* "Thanks a lot! :)"
  <br>Viktor V. 24/04/2013

## Contact

Post bugs and issues on [github][11]. Send other comments to John Lehmann:
first last at geemail dotcom or [@jplehmann][12]

[1]: https://www.coursera.org
[2]: http://sourceforge.net/projects/gnuwin32/files/wget/1.11.4-1/wget-1.11.4-1-setup.exe
[3]: https://rg3.github.com/youtube-dl
[5]: http://www.crummy.com/software/BeautifulSoup
[6]: http://pypi.python.org/pypi/argparse
[7]: http://pypi.python.org/pypi/setuptools
[8]: http://stackoverflow.com/a/6031266/962311
[9]: https://chrome.google.com/webstore/detail/lopabhfecdfhgogdbojmaicoicjekelh
[10]: https://addons.mozilla.org/en-US/firefox/addon/export-cookies
[11]: https://github.com/jplehmann/coursera/issues
[12]: https://twitter.com/jplehmann
[13]: http://techcrunch.com/2013/02/20/coursera-adds-29-schools-90-courses-and-4-new-languages-to-its-online-learning-platform
[14]: http://www.tunapanda.org
[15]: https://github.com/html5lib/html5lib-python
[16]: http://docs.python-requests.org/en/latest/
[17]: http://www.pip-installer.org/en/latest/
[18]: http://python-distribute.org/pip_distribute.png
