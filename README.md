# Coursera Downloader

[![Build Status](https://travis-ci.org/coursera-dl/coursera-dl.svg?branch=master)](https://travis-ci.org/coursera-dl/coursera-dl)
[![Build status](https://ci.appveyor.com/api/projects/status/3hru0ycv5fbny5k8/branch/master?svg=true)](https://ci.appveyor.com/project/balta2ar/coursera-dl/branch/master)
[![Coverage Status](https://coveralls.io/repos/coursera-dl/coursera-dl/badge.svg)](https://coveralls.io/r/coursera-dl/coursera-dl)
[![Latest version on PyPI](https://img.shields.io/pypi/v/coursera-dl.svg)](https://pypi.python.org/pypi/coursera-dl)
[![Code Climate](https://codeclimate.com/github/coursera-dl/coursera-dl/badges/gpa.svg)](https://codeclimate.com/github/coursera-dl/coursera-dl)

<!-- TOC -->

- [Coursera Downloader](#coursera-downloader)
- [Introduction](#introduction)
- [Features](#features)
- [Disclaimer](#disclaimer)
- [Installation instructions](#installation-instructions)
    - [Recommended installation method for all Operating Systems](#recommended-installation-method-for-all-operating-systems)
    - [Alternative ways of installing missing dependencies](#alternative-ways-of-installing-missing-dependencies)
        - [Alternative installation method for Unix systems](#alternative-installation-method-for-unix-systems)
        - [ArchLinux](#archlinux)
        - [Installing dependencies on your own](#installing-dependencies-on-your-own)
    - [Docker](#docker)
    - [Nix](#nix-package-manager)
    - [Windows](#windows)
    - [Create an account with Coursera](#create-an-account-with-coursera)
- [Running the script](#running-the-script)
    - [Resuming downloads](#resuming-downloads)
- [Troubleshooting](#troubleshooting)
    - [China issues](#china-issues)
    - [Found 0 sections and 0 lectures on this page](#found-0-sections-and-0-lectures-on-this-page)
    - [Download timeouts](#download-timeouts)
    - [Windows: proxy support](#windows-proxy-support)
    - [Windows: Failed to create process](#windows-failed-to-create-process)
    - [SSLError: [Errno 1] _ssl.c:504: error:14094410:SSL routines:SSL3_READ_BYTES:sslv3 alert handshake failure](#sslerror-errno-1-_sslc504-error14094410ssl-routinesssl3_read_bytessslv3-alert-handshake-failure)
    - [Alternative CDN for `MathJax.js`](#alternative-cdn-for-mathjaxjs)
- [Reporting issues](#reporting-issues)
- [Filing an issue/Reporting a bug](#filing-an-issuereporting-a-bug)
- [Feedback](#feedback)
- [Contact](#contact)

<!-- /TOC -->

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

  * Support for all kinds of courses (i.e., "Old Platform"/time-based as
    well as "New Platform"/on-demand courses).
  * Intentionally detailed names, so that it will display and sort properly
    on most interfaces (e.g., [VLC][4] or MX Video on Android devices).
  * Regex-based section (week) and lecture name filters to download only
    certain resources.
  * File format extension filter to grab resource types you want.
  * Login credentials accepted on command-line or from `.netrc` file.
  * Default arguments loaded from `coursera-dl.conf` file.
  * Core functionality tested on Linux, Mac and Windows.

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
enrolled in the class of interest. (As of February of 2020, we test
automatically the execution of the program with Python versions 2.7, Pypy,
3.6, 3.7, 3.8, and 3.9).

**Note:** We *strongly* recommend that you use a Python 3 interpreter (3.9
or later).

On any operating system, ensure that the Python executable location is added
to your `PATH` environment variable and, once you have the dependencies
installed (see next section), for a *basic* usage, you will need to invoke
the script from the main directory of the project and prepend it with the
word `python`.  You can also use more advanced features of the program by
looking at the "Running the script" section of this document.

*Note:* You must already have (manually) agreed to the Honor of Code of the
particular courses that you want to use with `coursera-dl`.

## Recommended installation method for all Operating Systems

From a command line (preferably, from a virtual environment), simply issue
the command:

    pip install coursera-dl


This will download [the latest released version][23] of the program from the
[Python Package Index (PyPI)][22] along with *all* the necessary
dependencies. At this point, you should be ready to start using it.

If this does not work, because your Python 2 version is too old (e.g. 2.7.5
on Ubuntu 14.4), try:

    apt-get install python3 python3-pip
    pip3 install coursera-dl

instead.

**Note 1:** We strongly recommend that you *don't* install the package
globally on your machine (i.e., with root/administrator privileges), as the
installed modules may conflict with other Python applications that you have
installed in your system (or they can interfere with `coursera-dl`).  Prefer
to use the option `--user` to `pip install`, if you need can.

**Note 2:** As already mentioned, we *strongly* recommend that you use a new
Python 3 interpreter (e.g., 3.9 or later), since Python 3 has better support
for SSL/TLS (for secure connections) than earlier versions.<br/>
If you must use Python 2, be sure that you have at least Python 2.7.9 (later
versions are OK).<br/>
Otherwise, you can still use `coursera-dl`, but you will have to install the
extra package `ndg-httpsclient`, which may involve compilation (at least on
Linux systems).

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
    git clone https://github.com/coursera-dl/coursera-dl
    cd coursera-dl
    pip install -r requirements.txt
    ./coursera-dl ...

To further download new videos from your classes, simply perform:

    cd /directory/where/I/want/my/courses/my-coursera
    source bin/activate
    cd coursera-dl
    ./coursera-dl ...

We are working on streamlining this whole process so that it is as simple as
possible, but to support older versions of Python and to cope with Coursera
disabling SSLv3, we have to take a few extra steps.  In any case, it is
*highly* recommended that you always install the latest version of the
Python interpreter that you can.

### ArchLinux

AUR package: [coursera-dl](https://aur.archlinux.org/packages/coursera-dl/)

### Installing dependencies on your own

**Warning:** This method is not recommended unless you have experience
working with multiple Python environments.

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
listed in the `requirements.txt` file (and, `requirements-dev.txt` file, if
applicable).

## Docker

If you prefer you can run this software inside Docker:

```
docker run --rm -it -v \
    "$(pwd):/courses" \
    courseradl/courseradl -u <USER> -p <PASSWORD>
```

Or using netrc file:

```
docker run --rm -it \
    -v "$(pwd):/courses" -v "$HOME/.netrc:/netrc" \
    courseradl/courseradl -n /netrc
```

The actual working dir for coursera-dl is /courses, all courses will be
downloaded there if you don't specify otherwise.


## Nix package manager

`nix-env -i coursera-dl`

## Windows

`python -m pip install coursera-dl`

Be sure that the Python install path is added to the PATH system environment
variables. This can be found in Control Panel > System > Advanced System
Settings > Environment Variables.

```
Example:
C:\Python39\Scripts\;C:\Python39\;
```

Or if you have restricted installation permissions and you've installed Python
under AppData, add this to your PATH.

```
Example:
C:\Users\<user>\AppData\Local\Programs\Python\Python39-32\Scripts;C:\Users\<user>\AppData\Local\Programs\Python\Python39-32;
```

Coursera-dl can now be run from commandline or powershell.

## Create an account with Coursera

If you don't already have one, create a [Coursera][1] account and enroll in
a class. See https://www.coursera.org/courses for the list of classes.

# Running the script

Refer to `coursera-dl --help` for a complete, up-to-date reference on the runtime options
supported by this utility.

Run the script to download the materials by providing your Coursera account
credentials (e.g. email address and password or a `~/.netrc` file), the
class names, as well as any additional parameters:
```
    General:                     coursera-dl -u <user> -p <pass> modelthinking-004

    With CAUTH parameter:	 coursera-dl -ca 'some-ca-value-from-browser' modelthinking-004
```
If you don't want to type your password in command line as plain text, you can use the
script without `-p` option. In this case you will be prompted for password  once the
script is run.

Here are some examples of how to invoke `coursera-dl` from the command line:
```
    Without -p field:            coursera-dl -u <user> modelthinking-004
    Multiple classes:            coursera-dl -u <user> -p <pass> saas historyofrock1-001 algo-2012-002
    Filter by section name:      coursera-dl -u <user> -p <pass> -sf "Chapter_Four" crypto-004
    Filter by lecture name:      coursera-dl -u <user> -p <pass> -lf "3.1_" ml-2012-002
    Download only ppt files:     coursera-dl -u <user> -p <pass> -f "ppt" qcomp-2012-001
    Use a ~/.netrc file:         coursera-dl -n -- matrix-001
    Get the preview classes:     coursera-dl -n -b ni-001
	Download videos at 720p:     coursera-dl -n --video-resolution 720p ni-001
    Specify download path:       coursera-dl -n --path=C:\Coursera\Classes\ comnetworks-002
    Display help:                coursera-dl --help

    Maintain a list of classes in a dir:
      Initialize:              mkdir -p CURRENT/{class1,class2,..classN}
      Update:                  coursera-dl -n --path CURRENT `\ls CURRENT`
```
**Note:** If your `ls` command is aliased to display a colorized output, you
may experience problems.  Be sure to escape the `ls` command (use `\ls`) to
assure that no special characters get sent to the script.

Note that we *do* support the New Platform ("on-demand") courses.

By default, videos are downloaded at 540p resolution. For on-demand courses, the
`--video-resolution` flag accepts 360p, 540p, and 720p values.

To download just the `.txt` and/or `.srt` subtitle files instead of the videos,
use `-ignore-formats mp4 --subtitle-language en` or whatever format the videos
are encoded in and desired languages for subtitles.

On \*nix platforms, the use of a `~/.netrc` file is a good alternative to
specifying both your username (i.e., your email address) and password every
time on the command line. To use it, simply add a line like the one below to
a file named `.netrc` in your home directory (or the [equivalent][8], if you
are using Windows) with contents like:
```
    machine coursera-dl login <user> password <pass>
```
Create the file if it doesn't exist yet.  From then on, you can switch from
using `-u` and `-p` to simply call `coursera-dl` with the option `-n`
instead.  This is especially convenient, as typing usernames (email
addresses) and passwords directly on the command line can get tiresome (even
more if you happened to choose a "strong" password).

Alternatively, if you want to store your preferred parameters (which might
also include your username and password), create a file named `coursera-dl.conf`
where the script is supposed to be executed, with the following format:
```
    --username <user>
    --password <pass>
    --subtitle-language en,zh-CN|zh-TW
    --download-quizzes
    #--mathjax-cdn https://cdn.bootcss.com/mathjax/2.7.1/MathJax.js
    # more other parameters
```
Parameters which are specified in the file will be overriden if they are 
provided again on the commandline.

**Note:** In `coursera-dl.conf`, all the parameters should not be wrapped
with quotes.

## Resuming downloads

In default mode when you interrupt the download process by pressing
<kbd>CTRL</kbd>+<kbd>C</kbd>, partially downloaded files will be deleted from your disk and
you have to start the download process from the beginning. If your
download was interrupted by something other than KeyboardInterrupt
(<kbd>CTRL</kbd>+<kbd>C</kbd>) like sudden system crash, partially downloaded files will
remain on your disk and the next time you start the process again,
these files will be discarded from download list!, therefore it's your
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
    `https://www.coursera.org/learn/<CLASS_NAME>/home/welcome`

* Have you tried to clean the cached cookies/credentials with the
  `--clear-cache` option?

* Note that many courses (most, perhaps?) may remove the materials after a
  little while after the course is completed, while other courses may retain
  the materials up to a next session/offering of the same course (to avoid
  problems with academic dishonesty, apparently).
  <br><br>
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
  `.netrc` file or in your `coursera-dl.conf` file).

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

* If your password has spaces, don't forget to write it using quotes.

* Have you installed the right project ?
  <br><br>
  **Warning**: If you installed the script using PyPi (pip) please verify that
  you installed the correct project. We had to use a different name in pip
  because our original name was already taken. Remember to install it using:
  ```
      pip install coursera-dl
  ```

## China issues

If you are from China and you're having problems downloading videos,
adding "52.84.167.78 d3c33hcgiwev3.cloudfront.net" in the hosts file
(/etc/hosts) and freshing DNS with "ipconfig/flushdns" may work
(see https://github.com/googlehosts/hosts for more info).

## Found 0 sections and 0 lectures on this page

First of all, make sure you are enrolled to the course you want to download.

Many old courses have already closed enrollment so often it's not an
option. In this case, try downloading with `--preview` option. Some
courses allow to download lecture materials without enrolling, but
it's not common and is not guaranteed to work for every course.

Finally, you can download the videos if you have, at least, the index
file that lists all the course materials. Maybe your friend who is enrolled
could save that course page for you. In that case use the `--process_local_page`
option.

Alternatively you may want to try this various browser extensions designed for
this problem.

If none of the above works for you, there is nothing we can do.

## Download timeouts

Coursera-dl supports external downloaders but note that they are only used to
download materials after the syllabus has been parsed, e.g. videos, PDFs, some
handouts and additional files (syllabus is always downloaded using the internal
downloader). If you experience problems with downloading such materials, you may
want to start using external downloader and configure its timeout values. For
example, you can use aria2c downloader by passing `--aria` option:

```
coursera-dl -n --path . --aria2  <course-name>
```

And put this into aria2c's configuration file `~/.aria2/aria2.conf` to reduce
timeouts:

```
connect-timeout=2
timeout=2
bt-stop-timeout=1
```

Timeout configuration for internal downloader is not supported.

## Windows: proxy support

If you're on Windows behind a proxy, set up the environment variables
before running the script as follows:

```
set HTTP_PROXY=http://host:port
set HTTPS_PROXY=http://host:port
```

Related discussion: [#205](https://github.com/coursera-dl/coursera-dl/issues/205)

## Windows: Failed to create process

In `C:\Users\<user>\AppData\Local\Programs\Python\Python39-32\Scripts`
or wherever Python installed (above is default for Windows)
edit below file in idle: (right click on script name and select 'edit with idle in menu)

```
coursera-dl-script
```

from

```
#!c:\users\<user>\appdata\local\programs\python\python39-32\python.exe
```

to

```
#"!c:\users\<user>\appdata\local\programs\python\python39-32\python.exe"
```

(add quotes). This is a known pip bug.

Source: [issue #500][issue500] [StackOverflow][pipinstallerbug]

## SSLError: [Errno 1] _ssl.c:504: error:14094410:SSL routines:SSL3_READ_BYTES:sslv3 alert handshake failure

This is a known error, please do not report about this error message! The problem is in **YOUR** environment. To fix it, do the following:

``` bash
sudo apt-get install build-essential python-dev libssl-dev libffi-dev
pip install --user urllib3 pyasn1 ndg-httpsclient pyOpenSSL
```
If the error remains, try installing coursera-dl from github following this instruction:
https://github.com/coursera-dl/coursera-dl#alternative-installation-method-for-unix-systems

If you still have the problem, please read the following issues for more ideas on how to fix it:
[#330](https://github.com/coursera-dl/coursera-dl/issues/330)
[#377](https://github.com/coursera-dl/coursera-dl/issues/377)
[#329](https://github.com/coursera-dl/coursera-dl/issues/329)

This is also worth reading:
https://urllib3.readthedocs.io/en/latest/security.html#insecureplatformwarning

## Alternative CDN for `MathJax.js`

When saving a course page, we enabled `MathJax` rendering for math equations, by
injecting `MathJax.js` in the header. The script is using a cdn service provided
by [mathjax.org](https://cdn.mathjax.org/mathjax/latest/MathJax.js). However, that
url is not accessible in some countries/regions, you can provide a
`--mathjax-cdn <MATHJAX_CDN>` parameter to specify the `MathJax.js` file that is
accessible in your region.

# Reporting issues

Before reporting any issue please follow the steps below:

1. Verify that you are running the latest version of the script, and the
recommended versions of its dependencies, see them in the file
`requirements.txt`.  Use the following command if in doubt:

        pip install --upgrade coursera-dl

2. If the problem persists, feel free to [open an issue][issue] in our
bugtracker, please fill the issue template with *as much information as
possible*.

[issue]: https://github.com/coursera-dl/coursera-dl/issues

# Filing an issue/Reporting a bug

When reporting bugs against `coursera-dl`, please don't forget to include
enough information so that you can help us help you:

* Is the problem happening with the latest version of the script?
* What operating system are you using?
* Do you have all the recommended versions of the modules? See them in the
  file `requirements.txt`.
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

Please, post bugs and issues on [github][11]. Please, **DON'T** send support
requests privately to the maintainers! We are quite swamped with day-to-day
activities. If you have problems, **PLEASE**, file them on the issue tracker.

[1]: https://www.coursera.org
[2]: https://sourceforge.net/projects/gnuwin32/files/wget/1.11.4-1/wget-1.11.4-1-setup.exe
[3]: http://rg3.github.io/youtube-dl
[4]: https://f-droid.org/repository/browse/?fdid=org.videolan.vlc
[5]: https://www.crummy.com/software/BeautifulSoup
[6]: https://pypi.python.org/pypi/argparse
[7]: https://pypi.python.org/pypi/setuptools
[8]: http://stackoverflow.com/a/6031266/962311
[9]: https://chrome.google.com/webstore/detail/cookietxt-export/lopabhfecdfhgogdbojmaicoicjekelh
[10]: https://addons.mozilla.org/en-US/firefox/addon/export-cookies/
[11]: https://github.com/coursera-dl/coursera-dl/issues
[13]: http://techcrunch.com/2013/02/20/coursera-adds-29-schools-90-courses-and-4-new-languages-to-its-online-learning-platform/
[14]: http://www.tunapanda.org
[15]: https://github.com/html5lib/html5lib-python
[16]: http://docs.python-requests.org/en/latest/
[17]: https://pip.pypa.io/en/latest/
[18]: http://ww45.python-distribute.org/pip_distribute.png
[19]: https://pypi.python.org/pypi/six/
[20]: https://www.coursera.org/about/terms
[22]: https://pypi.python.org/
[23]: https://pypi.python.org/pypi/coursera-dl
[issue213]: https://github.com/coursera-dl/coursera-dl/issues/213
[issue500]: https://github.com/coursera-dl/coursera-dl/issues/500
[pipinstallerbug]: http://stackoverflow.com/questions/31808180/installing-pyinstaller-via-pip-leads-to-failed-to-create-process
