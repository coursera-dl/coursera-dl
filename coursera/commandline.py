"""
This module contains code that is related to command-line argument
handling. The primary candidate is argument parser.
"""

import logging
import os
import sys

import configargparse as argparse

from coursera import __version__
from .credentials import CredentialsError, get_credentials, keyring
from .utils import decode_input

LOCAL_CONF_FILE_NAME = "coursera-dl.conf"


def class_name_arg_required(args):
    """
    Evaluates whether class_name arg is required.

    @param args: Command-line arguments.
    @type args: namedtuple
    """
    no_class_name_flags = ["list_courses", "version"]
    return not any(getattr(args, flag) for flag in no_class_name_flags)


def parse_args(args=None):
    """
    Parse the arguments/options passed to the program on the command line.
    """

    parse_kwargs = {
        "description": "Download Coursera.org lecture material and resources."
    }

    conf_file_path = os.path.join(os.getcwd(), LOCAL_CONF_FILE_NAME)
    if os.path.isfile(conf_file_path):
        parse_kwargs["default_config_files"] = [conf_file_path]
    parser = argparse.ArgParser(**parse_kwargs)

    # Basic options
    group_basic = parser.add_argument_group("Basic options")

    group_basic.add_argument(
        "class_names",
        action="store",
        nargs="*",
        help='name(s) of the class(es) (e.g. "ml-005")',
    )

    group_basic.add_argument(
        "-u",
        "--username",
        dest="username",
        action="store",
        default=None,
        help="username (email) that you use to login to Coursera",
    )

    group_basic.add_argument(
        "-p",
        "--password",
        dest="password",
        action="store",
        default=None,
        help="coursera password",
    )

    group_basic.add_argument(
        "--jobs",
        dest="jobs",
        action="store",
        default=1,
        type=int,
        help="number of parallel jobs to use for "
        "downloading resources. (Default: 1)",
    )

    group_basic.add_argument(
        "--download-delay",
        dest="download_delay",
        action="store",
        default=60,
        type=int,
        help="number of seconds to wait before downloading "
        "next course. (Default: 60)",
    )

    group_basic.add_argument(
        "-b",  # FIXME: kill this one-letter option
        "--preview",
        dest="preview",
        action="store_true",
        default=False,
        help="get videos from preview pages. (Default: False)",
    )

    group_basic.add_argument(
        "--path",
        dest="path",
        action="store",
        default="",
        help="path to where to save the file. (Default: current directory)",
    )

    group_basic.add_argument(
        "-sl",  # FIXME: deprecate this option
        "--subtitle-language",
        dest="subtitle_language",
        action="store",
        default="all",
        help="Choose language to download subtitles and transcripts."
        '(Default: all) Use special value "all" to download all available.'
        "To download subtitles and transcripts of multiple languages,"
        "use comma(s) (without spaces) to seperate the names of the languages,"
        ' i.e., "en,zh-CN".'
        "To download subtitles and transcripts of alternative language(s) "
        "if only the current language is not available,"
        'put an "|<lang>" for each of the alternative languages after '
        'the current language, i.e., "en|fr,zh-CN|zh-TW|de", and make sure '
        'the parameter are wrapped with quotes when "|" presents.',
    )

    # Selection of material to download
    group_material = parser.add_argument_group("Selection of material to download")

    group_material.add_argument(
        "--specialization",
        dest="specialization",
        action="store_true",
        default=False,
        help="treat given class names as specialization names and try to "
        "download its courses, if available. Note that there are name "
        'clashes, e.g. "machine-learning" is both a course and a '
        "specialization (Default: False)",
    )

    group_material.add_argument(
        "--only-syllabus",
        dest="only_syllabus",
        action="store_true",
        default=False,
        help="download only syllabus, skip course content. " "(Default: False)",
    )

    group_material.add_argument(
        "--download-quizzes",
        dest="download_quizzes",
        action="store_true",
        default=False,
        help="download quiz and exam questions. (Default: False)",
    )

    group_material.add_argument(
        "--download-notebooks",
        dest="download_notebooks",
        action="store_true",
        default=False,
        help="download Python Jupyther Notebooks. (Default: False)",
    )

    group_material.add_argument(
        "--about",  # FIXME: should be --about-course
        dest="about",
        action="store_true",
        default=False,
        help='download "about" metadata. (Default: False)',
    )

    group_material.add_argument(
        "-f",
        "--formats",
        dest="file_formats",
        action="store",
        default="all",
        help="file format extensions to be downloaded in"
        ' quotes space separated, e.g. "mp4 pdf" '
        '(default: special value "all")',
    )

    group_material.add_argument(
        "--ignore-formats",
        dest="ignore_formats",
        action="store",
        default=None,
        help="file format extensions of resources to ignore" " (default: None)",
    )

    group_material.add_argument(
        "-sf",  # FIXME: deprecate this option
        "--section_filter",
        dest="section_filter",
        action="store",
        default=None,
        help="only download sections which contain this" " regex (default: disabled)",
    )

    group_material.add_argument(
        "-lf",  # FIXME: deprecate this option
        "--lecture_filter",
        dest="lecture_filter",
        action="store",
        default=None,
        help="only download lectures which contain this regex" " (default: disabled)",
    )

    group_material.add_argument(
        "-rf",  # FIXME: deprecate this option
        "--resource_filter",
        dest="resource_filter",
        action="store",
        default=None,
        help="only download resources which match this regex" " (default: disabled)",
    )

    group_material.add_argument(
        "--video-resolution",
        dest="video_resolution",
        action="store",
        default="540p",
        help="video resolution to download (default: 540p); "
        "only valid for on-demand courses; "
        "only values allowed: 360p, 540p, 720p",
    )

    group_material.add_argument(
        "--disable-url-skipping",
        dest="disable_url_skipping",
        action="store_true",
        default=False,
        help="disable URL skipping, all URLs will be " "downloaded (default: False)",
    )

    # Parameters related to external downloaders
    group_external_dl = parser.add_argument_group("External downloaders")

    group_external_dl.add_argument(
        "--wget",
        dest="wget",
        action="store",
        nargs="?",
        const="wget",
        default=None,
        help="use wget for downloading," "optionally specify wget bin",
    )

    group_external_dl.add_argument(
        "--curl",
        dest="curl",
        action="store",
        nargs="?",
        const="curl",
        default=None,
        help="use curl for downloading," " optionally specify curl bin",
    )

    group_external_dl.add_argument(
        "--aria2",
        dest="aria2",
        action="store",
        nargs="?",
        const="aria2c",
        default=None,
        help="use aria2 for downloading," " optionally specify aria2 bin",
    )

    group_external_dl.add_argument(
        "--axel",
        dest="axel",
        action="store",
        nargs="?",
        const="axel",
        default=None,
        help="use axel for downloading," " optionally specify axel bin",
    )

    group_external_dl.add_argument(
        "--downloader-arguments",
        dest="downloader_arguments",
        default="",
        help="additional arguments passed to the" " downloader",
    )

    parser.add_argument(
        "--list-courses",
        dest="list_courses",
        action="store_true",
        default=False,
        help="list course names (slugs) and quit. Listed "
        "course names can be put into program arguments",
    )

    parser.add_argument(
        "--resume",
        dest="resume",
        action="store_true",
        default=False,
        help="resume incomplete downloads (default: False)",
    )

    parser.add_argument(
        "-o",
        "--overwrite",
        dest="overwrite",
        action="store_true",
        default=False,
        help="whether existing files should be overwritten" " (default: False)",
    )

    parser.add_argument(
        "--verbose-dirs",
        dest="verbose_dirs",
        action="store_true",
        default=False,
        help="include class name in section directory name",
    )

    parser.add_argument(
        "--quiet",
        dest="quiet",
        action="store_true",
        default=False,
        help="omit as many messages as possible" " (only printing errors)",
    )

    parser.add_argument(
        "-r",
        "--reverse",
        dest="reverse",
        action="store_true",
        default=False,
        help="download sections in reverse order",
    )

    parser.add_argument(
        "--combined-section-lectures-nums",
        dest="combined_section_lectures_nums",
        action="store_true",
        default=False,
        help="include lecture and section name in final files",
    )

    parser.add_argument(
        "--unrestricted-filenames",
        dest="unrestricted_filenames",
        action="store_true",
        default=False,
        help="Do not limit filenames to be ASCII-only",
    )

    # Advanced authentication
    group_adv_auth = parser.add_argument_group("Advanced authentication options")

    group_adv_auth.add_argument(
        "-ca",
        "--cauth",
        dest="cookies_cauth",
        action="store",
        default=None,
        help="cauth cookie value from browser",
    )

    group_adv_auth.add_argument(
        "-c",
        "--cookies_file",
        dest="cookies_file",
        action="store",
        default=None,
        help="full path to the cookies.txt file",
    )

    group_adv_auth.add_argument(
        "-n",
        "--netrc",
        dest="netrc",
        nargs="?",
        action="store",
        const=True,
        default=False,
        help="use netrc for reading passwords, uses default"
        " location if no path specified",
    )

    group_adv_auth.add_argument(
        "-k",
        "--keyring",
        dest="use_keyring",
        action="store_true",
        default=False,
        help="use keyring provided by operating system to " "save and load credentials",
    )

    group_adv_auth.add_argument(
        "--clear-cache",
        dest="clear_cache",
        action="store_true",
        default=False,
        help="clear cached cookies",
    )

    # Advanced miscellaneous options
    group_adv_misc = parser.add_argument_group("Advanced miscellaneous options")

    group_adv_misc.add_argument(
        "--hook",
        dest="hooks",
        action="append",
        default=[],
        help="hooks to run when finished",
    )

    group_adv_misc.add_argument(
        "-pl",
        "--playlist",
        dest="playlist",
        action="store_true",
        default=False,
        help="generate M3U playlists for course weeks",
    )

    group_adv_misc.add_argument(
        "--mathjax-cdn",
        dest="mathjax_cdn_url",
        default="https://cdn.mathjax.org/mathjax/latest/MathJax.js",
        help="the cdn address of MathJax.js",
    )

    # Debug options
    group_debug = parser.add_argument_group("Debugging options")

    group_debug.add_argument(
        "--skip-download",
        dest="skip_download",
        action="store_true",
        default=False,
        help="for debugging: skip actual downloading of files",
    )

    group_debug.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        default=False,
        help="print lots of debug information",
    )

    group_debug.add_argument(
        "--cache-syllabus",
        dest="cache_syllabus",
        action="store_true",
        default=False,
        help="cache course syllabus into a file",
    )

    group_debug.add_argument(
        "--version",
        dest="version",
        action="store_true",
        default=False,
        help="display version and exit",
    )

    group_debug.add_argument(
        "-l",  # FIXME: remove short option from rarely used ones
        "--process_local_page",
        dest="local_page",
        help="uses or creates local cached version of syllabus" " page",
    )

    # Final parsing of the options
    args = parser.parse_args(args)

    # Initialize the logging system first so that other functions
    # can use it right away
    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG, format="%(name)s[%(funcName)s] %(message)s"
        )
    elif args.quiet:
        logging.basicConfig(level=logging.ERROR, format="%(name)s: %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    if class_name_arg_required(args) and not args.class_names:
        parser.print_usage()
        logging.error("You must supply at least one class name")
        sys.exit(1)

    # show version?
    if args.version:
        # we use print (not logging) function because version may be used
        # by some external script while logging may output excessive
        # information
        print(__version__)
        sys.exit(0)

    # turn list of strings into list
    args.downloader_arguments = args.downloader_arguments.split()

    # turn list of strings into list
    args.file_formats = args.file_formats.split()

    # decode path so we can work properly with cyrillic symbols on different
    # versions on Python
    args.path = decode_input(args.path)

    # check arguments
    if args.use_keyring and args.password:
        logging.warning("--keyring and --password cannot be specified together")
        args.use_keyring = False

    if args.use_keyring and not keyring:
        logging.warning("The python module `keyring` not found.")
        args.use_keyring = False

    if args.cookies_file and not os.path.exists(args.cookies_file):
        logging.error("Cookies file not found: %s", args.cookies_file)
        sys.exit(1)

    if not args.cookies_file and not args.cookies_cauth:
        try:
            args.username, args.password = get_credentials(
                username=args.username,
                password=args.password,
                netrc=args.netrc,
                use_keyring=args.use_keyring,
            )
        except CredentialsError as e:
            logging.error(e)
            sys.exit(1)

    return args
