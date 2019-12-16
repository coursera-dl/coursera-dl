# Change Log

## 0.11.5 (2019-12-16)

Features:
  - add --cauth argument to specify CAUTH cookie directly from command-line (#724)

## 0.11.4 (2018-06-24)

Features:
  - Do not expand class names if there is a specialization with the same name,
    but add --specialization flag to do that explicitly (#673)

## 0.11.3 (2018-06-24)

Bugfixes:
  - Switch to newer API for syllabus and lecture retrieval (#665, #673, #634)

Features:
  - You can now download specializations: the child courses will be
    downloaded automatically

## 0.11.2 (2018-06-03)

Bugfixes:
  - Use TLS v1.2 instead of v1.0
  - Switched to api.coursera.org subdomain for subtitles requests (#664)

## 0.11.1 (2018-06-02)

Bugfixes:
  - Specify utf-8 encoding in setup.py to fix installation on Windows (#662)

## 0.11.0 (2018-06-02)

Features:
  - Add support for "peer assignment" section (#650)

Bugfixes:
  - Switched to api.coursera.org subdomain for API requests (#660)

## 0.10.0 (2018-02-19)

Features:
  - Support Coursera Notebooks (option: `--download-notebooks`)
  - Add hints in the documentation for users in China

## 0.9.0 (2017-05-25)

Features:
  - Default arguments are loaded from `coursera-dl.conf` file
  - Added option `--mathjax-cdn <MATHJAX_CDN>` to specify alternative MathJax CDN
  - Added support for Resources section

## 0.8.0 (2016-10-04)

Features:
  - Add `--download-delay` option that adds a specified delay in seconds
    before downloading next course. This is useful when downloading many
    courses at once. Default value is 60 seconds.
  - Add `--only-syllabus` option which is when activated, allows to skip
    download of the course content. Only syllabus is parsed.
  - Add support for `reflect` and `mcqReflect` question types in quizzes.
  - Courses that encountered an error while parsing syllabus will be listed
    in the end of the program execution, after all courses have been
    processed (hopefully, downloaded). This helps skip vast output and easily
    see which courses need user's attention, e.g. enrollment, session
    switching or just patience until the course start date.

Bugfixes:
  - Locked programming assignments in syllabus used to crash coursera-dl.
    Now the script goes on parsing syllabus and skips locked assignments.
  - Add missing import statement to playlist generation module

## 0.7.0 (2016-07-28)

Features:
  - Added option `--list-courses` to list currently enrolled courses (#514)
  - Added option `--jobs N` to download resources in N threads simultaneously (#553)
  - Added option `--download-quizzes` to download contents of graded and
    ungraded quizzes (#490)
  - Added option `--cache-syllabus` to avoid downloading course syllabus on
    every run (this option is rather for developers)

Bugfixes:
  - Locked lectures are also requested from server now, which allows to
    download some programming assignments that were not downloaded before (#555)

Deletions:
  - Support for old-style courses has been removed (Coursera discontinued old courses:
    http://coursera.tumblr.com/post/145882467032/courseras-transition-to-a-new-technology-platform)
  - `--ignore-http-errors` option has been removed and the default behavior
    has been adjusted to include this option
  - Removed deprecated `--on-demand` option. Now OnDemand classes are downloaded
    by default

## 0.6.1 (2016-06-20)

Bugfixes:
  - When using `--process_local_page` option, errors downloading About
    page will not stop course download
  - Limit file name part to 200 characters and file extension part to 20
    characters to alleviate "Filename is too long" issue

## 0.6.0 (2016-06-17)

Features:
  - Descriptions of assignments are saved in more cases (different courses
    implement it in a different way)
  - Images are embedded into descriptions of assignments and are available
    offline locally
  - MathJax is injected into descriptions of assignments to render math
    locally (requires Internet connection)
  - Add option `--ignore-http-errors` to ignore errors in internal
    downloader during resource downloading stage
  - Add option `--disable-url-skipping` to always try downloading
    all the URLs that were found by the parser
  - Add option `--downloader-arguments` (#464)
  - Add option `--version` (#477)
  - Better looking progress output: during the syllabus parsing stage
    lecture/section names are printed in a hierarchical structure

Bugfixes:
  - Stricter filename cleaning in on-demand course parser
  - Better URL filtering
  - Detect SSL errors and suggest link to the solution in the output
  - Added workaround for "Filename is too long" on Windows
