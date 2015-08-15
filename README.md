# Coursera Downloader

[![Build Status](https://travis-ci.org/coursera-dl/coursera.png?branch=master)](https://travis-ci.org/coursera-dl/coursera)
[![Coverage Status](https://coveralls.io/repos/coursera-dl/coursera/badge.png)](https://coveralls.io/r/coursera-dl/coursera)
[![Latest version on PyPI](https://img.shields.io/pypi/v/coursera.svg)](https://pypi.python.org/pypi/coursera)
[![Downloads from PyPI](https://img.shields.io/pypi/dm/coursera.svg)](https://pypi.python.org/pypi/coursera)
[![Code Climate](https://codeclimate.com/github/coursera-dl/coursera/badges/gpa.svg)](https://codeclimate.com/github/coursera-dl/coursera)

# Introduction

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

Why is this helpful?  A utility like [wget][2] can work, but has the
following limitations:

1. Video names have numbers in them, but this does not correspond to
    the actual order.  Manually renaming them is a pain that is best left
    for computers.
2. Using names from the syllabus page provides more informative names.
3. Using `wget` in a for loop picks up extra videos which are not
    posted/linked, and these are sometimes duplicates.

Browser extensions like *DownloadThemAll* is another possibility, but
`coursera-dl` provides more features such as appropriately named files.

This work was originally inspired in part by [youtube-dl][3] by which
I've downloaded many other good videos such as those from Khan Academy.


# Features

  * Intentionally detailed names, so that it will display and sort properly
    on most interfaces (e.g., MX Video, or [VLC][4] on Android devices).
  * Regex-based section (week) and lecture name filters to download only
    certain resources.
  * File format extension filter to grab resource types you want.
  * Login credentials accepted on command-line or from `.netrc` file.
  * Core functionality tested on Linux, Mac and Windows.
  * Support for both regular (i.e., time-based) courses as well as on-demand
    courses.

# Disclaimer

`coursera-dl` is meant to be used only for your material that Coursera gives
you access to download.

We do not encourage any use that violates their [Terms Of Use][20]. A
relevant excerpt:

> "[...] Coursera grants you a personal, non-exclusive, non-transferable
> license to access and use the Sites. You may download material from the
> Sites only for your own personal, non-commercial use. You may not
> otherwise copy, reproduce, retransmit, distribute, publish, commercially
> exploit or otherwise transfer any material, nor may you modify or create
> derivatives works of the material."


# Installation instructions

`coursera-dl` requires Python 2 or Python 3 and a free Coursera account
enrolled in the class of interest. (At present/May of 2015, we test
automatically the execution of the program with Python versions 2.6, 2.7,
Pypy, 3.2, 3.3, and 3.4).

On any operating system, ensure that the Python executable location is added
to your `PATH` environment variable and, once you have the dependencies
installed (see next section), for a *basic* usage, you will need to invoke
the script from the main directory of the project and prepend it with the
word `python`.  You can also use more advanced features of the program by
looking at the "Running the script" section of this document.

*Note:* You must already have (manually) agreed to the Honor of Code of the
particular courses that you want to use with `coursera-dl`.

## Recommended installation method for all Operating Systems

From a command line (preferrably, from a virtual environment), simply issue
the command:

    pip install coursera


This will dowload [the latest released version][23] of the program from the
[Python Package Index (PyPI)][22] along with *all* the necessary
dependencies. At this point, you should be ready to start using it.

**Note 1:** Note that the PyPI package is called simply `coursera`, but the
command-line is called `coursera-dl`. This is an unfortunate fact related to
conflicting names.

**Note 2:** We strongly recommend that you *don't* install the package
globally on your machine (i.e., with root/administrator privileges), as the
installed modules may conflict with other Python applications that you have
installed in your system (or they can interfere with `coursera-dl`).  Prefer
to use the option `--user` to `pip install`, if you need can.

## Alternative ways of installing missing dependencies

We strongly recommend that you consider installing Python packages with
[pip][17], as in it is the current [preferred method][18], unless directed
otherwise by one of the project members (for instance, when testing or
debugging a new feature or using the source code directly from our git
repository).  If you are using `pip`, you can directly install all the
dependencies from the requirements file using `pip install -r
requirements.txt`.

### Alternative installation method for Unix systems

We strongly recommend that you install `coursera-dl` and all its
dependencies in a way that does *not* interfere with the rest of your Python
installation. This is accomplished by the creation of a *virtual
environment*, or "virtualenv".

For the initial setup, in a Unix-like operating system, please use the
following steps (create/adapt first the directory
`/directory/where/I/want/my/courses`):

    cd /directory/where/I/want/my/courses
    virtualenv my-coursera
    cd my-coursera
    source bin/activate
    git clone https://github.com/coursera-dl/coursera
    cd coursera
    pip install -r requirements.txt
    ./coursera-dl ...

To further download new videos from your classes, simply perform:

    cd /directory/where/I/want/my/courses/my-coursera
    source bin/activate
    cd coursera
    ./coursera-dl ...

We are working on streamlining this whole process so that it is as simple as
possible, but to support older versions of Python and to cope with Coursera
disabling SSLv3, we have to take a few extra steps.  In any case, it is
*highly* recommended that you always install the latest version of the
Python interpreter that you can.


### Installing dependencies on your own

**Warning:** This method is not recommended unless you know what you are
doing.

You can use the `pip` program to install the dependencies on your own.  They
are all listed in the `requirements.txt` file (and the extra dependencies
needed for development are listed in the `requirements-dev.txt` file).

To use this method, you would proceed as:

    pip install -r requirements.txt
    pip install -r requirements-dev.txt

The second line above should only be needed if you intend to help with
development (and help is *always* welcome) or if a maintainer of the project
asks you to install extra packages for debugging purposes.

Once again, before filing bug reports, if you installed the dependencies on
your own, please check that the versions of your modules are at least those
recommended according to the `requirements.txt` file (and,
`requirements-dev.txt` file, if applicable).

## Create an account with Coursera

If you don't already have one, create a [Coursera][1] account and enroll in
a class. See https://www.coursera.org/courses for the list of classes.

## Running the script

Run the script to download the materials by providing your Coursera account
credentials (e.g. email address and password or a `~/.netrc` file), the
class names, as well as any additional parameters:

    General:                     coursera-dl -u <user> -p <pass> modelthinking-004
    On-Demand course:            coursera-dl -u <user> -p <pass> --on-demand calculus1
    Multiple classes:            coursera-dl -u <user> -p <pass> saas historyofrock1-001 algo-2012-002
    Filter by section name:      coursera-dl -u <user> -p <pass> -sf "Chapter_Four" crypto-004
    Filter by lecture name:      coursera-dl -u <user> -p <pass> -lf "3.1_" ml-2012-002
    Download only ppt files:     coursera-dl -u <user> -p <pass> -f "ppt" qcomp-2012-001
    Use a ~/.netrc file:         coursera-dl -n -- matrix-001
    Get the preview classes:     coursera-dl -n -b ni-001
    Specify download path:       coursera-dl -n --path=C:\Coursera\Classes\ comnetworks-002
    Display help:                coursera-dl --help

**Note:** Some of the options like `-sf` and `-f` may not work with on-demand courses.
Downloading on-demand courses are mutually exclusive with regular courses.

    Maintain a list of classes in a dir:
      Initialize:              mkdir -p CURRENT/{class1,class2,..classN}
      Update:                  coursera-dl -n --path CURRENT `\ls CURRENT`

**Note:** If your `ls` command is aliased to display a colorized output, you
may experience problems.  Be sure to escape the `ls` command (use `\ls`) to
assure that no special characters get sent to the script.

Note that we *do* support the new On Demand classes. You have to use the
option `--on-demand` for that purpose. You also have to download those
classes *separately* for regular, time-based classes.

On \*nix platforms, the use of a `~/.netrc` file is a good alternative to
specifying both your username (i.e., your email address) and password every
time on the command line. To use it, simply add a line like the one below to
a file named `.netrc` in your home directory (or the [equivalent][8], if you
are using Windows) with contents like:

    machine coursera-dl login <user> password <pass>

Create the file if it doesn't exist yet.  From then on, you can switch from
using `-u` and `-p` to simply call `coursera-dl` with the option `-n`
instead.  This is especially convenient, as typing usernames (email
addresses) and passwords directly on the command line can get tiresome (even
more if you happened to choose a "strong" password).

In default mode when you interrupt the download process by pressing
CTRL+C, partially downloaded files will be deleted from your disk and
you have to start the download process from the begining. If your
download was interrupted by something other than KeyboardInterrupt
(CTRL+C) like sudden system crash, partially downloaded files will
remain on your disk and the next time you start the process again,
these files will be discraded from download list!, therefore it's your
job to delete them manually before next start. For this reason we
added an option called `--resume` which continues your downloads from
where they stopped:

	coursera-dl -u <user> -p <pass> --resume sdn1-001

This option can also be used with external downloaders:

	coursera-dl --wget -u <user> -p <pass> --resume sdn1-001

*Note 1*: Some external downloaders use their own built-in resume feature
which may not be compatible with others, so use them at your own risk.

*Note 2*: Remember that in resume mode, interrupted files **WON'T** be deleted from
your disk.

**NOTE**: If your password contains punctuation, quotes or other "funny
characters" (e.g., `<`, `>`, `#`, `&`, `|` and so on), then you may have to
escape them from your shell. With bash or other Bourne-shell clones (and
probably with many other shells) one of the better ways to do so is to
enclose your password in single quotes, so that you don't run into
problems.  See [issue #213][issue213] for more information.

# Troubleshooting

If you have problems when downloading class materials, please try to see if
one of the following actions solve your problem:

* Make sure the class name you are using corresponds to the resource name
  used in the URL for that class:
    `https://class.coursera.org/<CLASS_NAME>/class/index`

* To download an On Demand course, use the `--on-demand` option of the
  program.

* Have you tried to clean the cached cookies/credentials with the
  `--clear-cache` option?

* Note that many courses (most, perhaps?) may remove the materials after a
  little while after the course is completed, while other courses may retain
  the materials up to a next session/offering of the same course (to avoid
  problems with academic dishonesty, apparently).
    
    In short, it is not guaranteed that you will be able to download after the
    course is finished and this is, unfortunately, nothing that we can help
    you with.

* Make sure you have installed and/or updated all of your dependencies
  according to the `requirements.txt` file as described above.

* One can export a Netscape-style cookies file with a browser extension ([1][9], [2][10])
  and use it with the `-c` option. This comes in handy
  when the authentication via password is not working (the authentication
  process changes now and then).

* If results show 0 sections, you most likely have provided invalid
  credentials (username and/or password in the command line or in your
  `.netrc` file).

* For courses that have not started yet, but have had a previous iteration
  sometimes a preview is available, containing all the classes from the last
  course. These files can be downloaded by passing the `--preview`
  parameter.

* If you get an error like `Could not find class: <CLASS_NAME>`, then:
    * Verify that the name of the course is correct. Current class
    names in coursera are composed by a short course name e.g. `class` and
    the current version of the course (a number). For example, for a
    class named `class`, you would have to use `class-001`, `class-002`
    etc.
    * Second, verify that you are enrolled in the course. You won't be
    able to access the course materials if you are not officially
    enrolled and agreed to the honor course *via the website*.

* If:
    * You get an error when using `-n` to specify that you want to use a
      `.netrc` file and,
    * You want the script to use your default netrc file and,
    * You get a message saying `coursera-dl: error: too few arguments`  
    
      Then you should specify `--` as an argument after `-n`, that is, `-n --`
      or change the order in which you pass the arguments to the script, so that
      the argument after `-n` begins with an hyphen (`-`).  Otherwise, Python's
      `argparse` module will think that what you are passing is the name of the
      netrc file that you want to use. See issue #162.

# Filing an issue/Reporting a bug

When reporting bugs against `coursera-dl`, please don't forget to include
enough information so that you can help us help you:

* Is the problem happening with the latest version of the script?
* What operating system are you using?
* Do you have all the recommended versions of the modules? See them in
  the file `requirements.txt`.
* What is the course that you are trying to access?
* What is the precise command line that you are using (feel free to hide
  your username and password with asterisks, but leave all other
  information untouched).
* What are the precise messages that you get? Please, use the `--debug`
  option before posting the messages as a bug report. Please, copy and paste
  them.  Don't reword/paraphrase the messages.

# Feedback

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

# Contact

Please, post bugs and issues on [github][11]. Send other comments to Rogério
Theodoro de Brito (the current maintainer): rbrito@ime.usp.br (twitter:
[@rtdbrito][21]) or to John Lehmann (the original author): first last at
geemail dotcom (twitter: [@jplehmann][12]).

[1]: https://www.coursera.org
[2]: http://sourceforge.net/projects/gnuwin32/files/wget/1.11.4-1/wget-1.11.4-1-setup.exe
[3]: https://rg3.github.com/youtube-dl
[4]: https://f-droid.org/repository/browse/?fdid=org.videolan.vlc
[5]: http://www.crummy.com/software/BeautifulSoup
[6]: http://pypi.python.org/pypi/argparse
[7]: http://pypi.python.org/pypi/setuptools
[8]: http://stackoverflow.com/a/6031266/962311
[9]: https://chrome.google.com/webstore/detail/lopabhfecdfhgogdbojmaicoicjekelh
[10]: https://addons.mozilla.org/en-US/firefox/addon/export-cookies
[11]: https://github.com/coursera-dl/coursera-dl/issues
[12]: https://twitter.com/jplehmann
[13]: http://techcrunch.com/2013/02/20/coursera-adds-29-schools-90-courses-and-4-new-languages-to-its-online-learning-platform
[14]: http://www.tunapanda.org
[15]: https://github.com/html5lib/html5lib-python
[16]: http://docs.python-requests.org/en/latest/
[17]: http://www.pip-installer.org/en/latest/
[18]: http://python-distribute.org/pip_distribute.png
[19]: https://pypi.python.org/pypi/six/
[20]: https://www.coursera.org/about/terms
[21]: https://twitter.com/rtdbrito
[22]: http://pypi.python.org/
[23]: http://pypi.python.org/pypi/coursera
[issue213]: https://github.com/coursera-dl/coursera-dl/issues/213

[![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/coursera-dl/coursera/trend.png)](https://bitdeli.com/free "Bitdeli Badge")
