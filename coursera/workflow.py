import os
import re
import abc
import time
import codecs
import logging
import subprocess

import requests

from .formatting import format_section, get_lecture_filename
from .playlist import create_m3u_playlist
from .utils import is_course_complete, mkdir_p, normalize_path
from .filter import find_resources_to_get, skip_format_url
from .define import IN_MEMORY_MARKER


def handle_resource(downloader,
                    lecture_filename,
                    fmt,
                    url,
                    overwrite,
                    resume,
                    skip_download,
                    skipped_urls,
                    last_update):
    """
    Handle resource. This function builds up resource file name and
    downloads it if necessary.

    @param downloader: Resource downloader instance.
    @type downloader: downloaders.Downloader

    @param fmt: Format of the resource (pdf, csv, etc)
    @type fmt: str

    @param url: URL of the resource.
    @type url: str

    @param overwrite: Flag that indicates whether files should be overwritten.
    @type overwrite: bool

    @param resume: Flag that indicates whether download should be resumed.
    @type resume: bool

    @param skip_download: Flag that indicates whether download should be skipped.
    @type skip_download: bool

    @param skipped_urls: List of skipped urls to update.
    @type skipped_urls: None or list

    @param last_update: Latest mtime across files.
    @type last_update: timestamp

    @return: Updated latest mtime.
    @rtype: timestamp
    """
    # Decide whether we need to download it
    if overwrite or not os.path.exists(lecture_filename) or resume:
        if not skip_download:
            if url.startswith(IN_MEMORY_MARKER):
                page_content = url[len(IN_MEMORY_MARKER):]
                logging.info('Saving page contents to: %s', lecture_filename)
                with codecs.open(lecture_filename, 'w', 'utf-8') as file_object:
                    file_object.write(page_content)
            else:
                if skipped_urls is not None and skip_format_url(fmt, url):
                    skipped_urls.append(url)
                else:
                    logging.info('Downloading: %s', lecture_filename)
                    downloader.download(url, lecture_filename, resume=resume)
        else:
            open(lecture_filename, 'w').close()  # touch
        last_update = time.time()
    else:
        logging.info('%s already downloaded', lecture_filename)
        # if this file hasn't been modified in a long time,
        # record that time
        last_update = max(last_update, os.path.getmtime(lecture_filename))

    return last_update


class CourseDownloader(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        pass

    @abc.abstractmethod
    def download_modules(self, modules):
        pass


class CourseraDownloader(CourseDownloader):
    def __init__(self,
                 downloader,
                 commandline_args,
                 class_name,
                 path='',
                 ignored_formats=None,
                 disable_url_skipping=False):
        super(CourseraDownloader, self).__init__()

        self._downloader = downloader
        self._args = commandline_args
        self._class_name = class_name
        self._path = path
        self._ignored_formats = ignored_formats
        self._disable_url_skipping = disable_url_skipping

        self.skipped_urls = [] if disable_url_skipping else None
        self.failed_urls = []

        self._last_update = -1

    def download_modules(self, modules):
        completed = True
        for idx, module in enumerate(modules):
            module_name = '%02d_%s' % (idx + 1, module[0])
            sections = module[1]
            result = self._download_sections(module_name, sections)
            completed = completed and result
        return completed

    def _download_sections(self, module_name, sections):
        """
        Download lecture resources described by sections.

        Returns True if the class appears completed, False otherwise.
        """
        self._last_update = -1

        section_filter = self._args.section_filter
        verbose_dirs = self._args.verbose_dirs
        hooks = self._args.hooks
        playlist = self._args.playlist

        for (secnum, (section, lectures)) in enumerate(sections):
            if section_filter and not re.search(section_filter, section):
                logging.debug('Skipping b/c of sf: %s %s', section_filter,
                              section)
                continue

            section_dir = os.path.join(
                self._path, self._class_name, module_name,
                format_section(secnum + 1, section,
                               self._class_name, verbose_dirs))

            self._download_lectures(lectures, secnum, section_dir)

            # After fetching resources, create a playlist in M3U format with the
            # videos downloaded.
            if playlist:
                create_m3u_playlist(section_dir)

            if hooks:
                original_dir = os.getcwd()
                for hook in hooks:
                    logging.info('Running hook %s for section %s.', hook, section_dir)
                    os.chdir(section_dir)
                    subprocess.call(hook)
                os.chdir(original_dir)

        # if we haven't updated any files in 1 month, we're probably
        # done with this course
        is_complete = is_course_complete(self._last_update)
        if is_complete:
            logging.info('COURSE PROBABLY COMPLETE: ' + self._class_name)

        return is_complete

    def _download_lectures(self, lectures, secnum, section_dir):
        lecture_filter = self._args.lecture_filter
        file_formats = self._args.file_formats
        resource_filter = self._args.resource_filter
        combined_section_lectures_nums = self._args.combined_section_lectures_nums
        overwrite = self._args.overwrite
        resume = self._args.resume
        skip_download = self._args.skip_download

        for (lecnum, (lecname, lecture)) in enumerate(lectures):
            if lecture_filter and not re.search(lecture_filter,
                                                lecname):
                logging.debug('Skipping b/c of lf: %s %s', lecture_filter,
                              lecname)
                continue

            if not os.path.exists(section_dir):
                mkdir_p(normalize_path(section_dir))

            resources_to_get = find_resources_to_get(lecture,
                                                     file_formats,
                                                     resource_filter,
                                                     self._ignored_formats)

            # write lecture resources
            for fmt, url, title in resources_to_get:
                lecture_filename = get_lecture_filename(
                    combined_section_lectures_nums,
                    section_dir, secnum, lecnum, lecname, title, fmt)

                lecture_filename = normalize_path(lecture_filename)

                try:
                    self._last_update = handle_resource(
                        self._downloader, lecture_filename, fmt, url,
                        overwrite, resume, skip_download,
                        self.skipped_urls, self._last_update)
                except requests.exceptions.RequestException as e:
                    logging.error('The following error has occurred while '
                                  'downloading URL %s: %s', url, str(e))
                    self.failed_urls.append(url)
