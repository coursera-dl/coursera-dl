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

        # Wait for all downloads to complete
        self._downloader.join()

        # Iterate over modules again to apply playlist creation/other hooks
        # after download has finished
        self._apply_postprocessing(modules)

        return completed

    def _apply_postprocessing(self, modules):
        """
        Apply postprocessing hooks to downloaded modules.
        """
        section_filter = self._args.section_filter
        hooks = self._args.hooks
        playlist = self._args.playlist
        verbose_dirs = self._args.verbose_dirs

        for idx, module in enumerate(modules):
            module_name = '%02d_%s' % (idx + 1, module[0])
            sections = module[1]

            for (secnum, (section, lectures)) in enumerate(sections):
                if section_filter and not re.search(section_filter, section):
                    continue

                section_dir = os.path.join(
                    self._path, self._class_name, module_name,
                    format_section(secnum + 1, section,
                                   self._class_name, verbose_dirs))

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

    def _download_sections(self, module_name, sections):
        """
        Download lecture resources described by sections.

        Returns True if the class appears completed, False otherwise.
        """
        self._last_update = -1

        section_filter = self._args.section_filter
        verbose_dirs = self._args.verbose_dirs

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
                self._handle_resource(url, fmt, lecture_filename,
                                      self._download_completion_handler)

    def _download_completion_handler(self, url, result):
        if isinstance(result, requests.exceptions.RequestException):
            logging.error('The following error has occurred while '
                          'downloading URL %s: %s', url, str(result))
            self.failed_urls.append(url)
        elif isinstance(result, Exception):
            logging.error('Unknown exception occurred: %s' % result)
            self.failed_urls.append(url)

    def _handle_resource(self, url, fmt, lecture_filename, callback):
        """
        Handle resource. This function builds up resource file name and
        downloads it if necessary.

        @param fmt: Format of the resource (pdf, csv, etc)
        @type fmt: str

        @param url: URL of the resource.
        @type url: str

        @return: Updated latest mtime.
        @rtype: timestamp
        """
        overwrite = self._args.overwrite
        resume = self._args.resume
        skip_download = self._args.skip_download

        # Decide whether we need to download it
        if overwrite or not os.path.exists(lecture_filename) or resume:
            if not skip_download:
                if url.startswith(IN_MEMORY_MARKER):
                    page_content = url[len(IN_MEMORY_MARKER):]
                    logging.info('Saving page contents to: %s', lecture_filename)
                    with codecs.open(lecture_filename, 'w', 'utf-8') as file_object:
                        file_object.write(page_content)
                else:
                    if self.skipped_urls is not None and skip_format_url(fmt, url):
                        self.skipped_urls.append(url)
                    else:
                        logging.info('Downloading: %s', lecture_filename)
                        self._downloader.download(callback, url, lecture_filename, resume=resume)
            else:
                open(lecture_filename, 'w').close()  # touch
            self._last_update = time.time()
        else:
            logging.info('%s already downloaded', lecture_filename)
            # if this file hasn't been modified in a long time,
            # record that time
            self._last_update = max(self._last_update,
                                    os.path.getmtime(lecture_filename))
