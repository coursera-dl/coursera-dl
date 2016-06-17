# Change Log

## 0.6.0 (YYYY-MM-DD)

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
