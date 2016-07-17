# Change Log

## 0.7.0 (2016-??-??)

Features:
  - Added option `--list-courses` to list currently enrolled courses (#514)
  - Added option `--jobs N` to download resources in N threads simultaneously (#553)
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
    by default.

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
