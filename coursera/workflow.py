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
from .filtering import find_resources_to_get, skip_format_url
from .define import IN_MEMORY_MARKER


def _iter_modules(modules, class_name, path, ignored_formats, args):
    """
    This huge function generates a hierarchy with hopefully more
    clear structure of modules/sections/lectures.
    """
    file_formats = args.file_formats
    lecture_filter = args.lecture_filter
    resource_filter = args.resource_filter
    section_filter = args.section_filter
    verbose_dirs = args.verbose_dirs
    combined_section_lectures_nums = args.combined_section_lectures_nums

    class IterModule(object):
        def __init__(self, index, module):
            self.index = index
            self.name = '%02d_%s' % (index + 1, module[0])
            self._module = module

        @property
        def sections(self):
            sections = self._module[1]
            for (secnum, (section, lectures)) in enumerate(sections):
                if section_filter and not re.search(section_filter, section):
                    logging.debug('Skipping b/c of sf: %s %s',
                                  section_filter, section)
                    continue

                yield IterSection(self, secnum, section, lectures)

    class IterSection(object):
        def __init__(self, module_iter, secnum, section, lectures):
            self.index = secnum
            self.dir = os.path.join(
                path, class_name, module_iter.name,
                format_section(secnum + 1, section,
                               class_name, verbose_dirs))
            self._lectures = lectures

        @property
        def lectures(self):
            for (lecnum, (lecname, lecture)) in enumerate(self._lectures):
                if lecture_filter and not re.search(lecture_filter, lecname):
                    logging.debug('Skipping b/c of lf: %s %s',
                                  lecture_filter, lecname)
                    continue

                yield IterLecture(self, lecnum, lecname, lecture)

    class IterLecture(object):
        def __init__(self, section_iter, lecnum, lecname, lecture):
            self.index = lecnum
            self.name = lecname
            self._lecture = lecture
            self._section_iter = section_iter

        def filename(self, fmt, title):
            lecture_filename = get_lecture_filename(
                combined_section_lectures_nums,
                self._section_iter.dir, self._section_iter.index,
                self.index, self.name, title, fmt)
            return lecture_filename

        @property
        def resources(self):
            resources_to_get = find_resources_to_get(
                self._lecture, file_formats, resource_filter,
                ignored_formats)

            for fmt, url, title in resources_to_get:
                yield IterResource(fmt, url, title)

    class IterResource(object):
        def __init__(self, fmt, url, title):
            self.fmt = fmt
            self.url = url
            self.title = title

    for index, module in enumerate(modules):
        yield IterModule(index, module)


def _walk_modules(modules, class_name, path, ignored_formats, args):
    """
    Helper generator that traverses modules in returns a flattened
    iterator.
    """
    for module in _iter_modules(modules=modules,
                                class_name=class_name,
                                path=path,
                                ignored_formats=ignored_formats,
                                args=args):
        for section in module.sections:
            for lecture in section.lectures:
                for resource in lecture.resources:
                    yield module, section, lecture, resource


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

    def download_modules(self, modules):
        completed = True
        modules = _iter_modules(
            modules, self._class_name, self._path,
            self._ignored_formats, self._args)

        for module in modules:
            last_update = -1
            for section in module.sections:
                if not os.path.exists(section.dir):
                    mkdir_p(normalize_path(section.dir))

                for lecture in section.lectures:
                    for resource in lecture.resources:
                        lecture_filename = normalize_path(
                            lecture.filename(resource.fmt, resource.title))
                        last_update = self._handle_resource(
                            resource.url, resource.fmt, lecture_filename,
                            self._download_completion_handler, last_update)

                # After fetching resources, create a playlist in M3U format with the
                # videos downloaded.
                if self._args.playlist:
                    create_m3u_playlist(section.dir)

                if self._args.hooks:
                    self._run_hooks(section, self._args.hooks)

            # if we haven't updated any files in 1 month, we're probably
            # done with this course
            completed = completed and is_course_complete(last_update)

        if completed:
            logging.info('COURSE PROBABLY COMPLETE: ' + self._class_name)

        # Wait for all downloads to complete
        self._downloader.join()
        return completed

    def _download_completion_handler(self, url, result):
        if isinstance(result, requests.exceptions.RequestException):
            logging.error('The following error has occurred while '
                          'downloading URL %s: %s', url, str(result))
            self.failed_urls.append(url)
        elif isinstance(result, Exception):
            logging.error('Unknown exception occurred: %s', result)
            self.failed_urls.append(url)

    def _handle_resource(self, url, fmt, lecture_filename, callback, last_update):
        """
        Handle resource. This function builds up resource file name and
        downloads it if necessary.

        @param url: URL of the resource.
        @type url: str

        @param fmt: Format of the resource (pdf, csv, etc)
        @type fmt: str

        @param lecture_filename: File name of the lecture.
        @type lecture_filename: str

        @param callback: Callback that will be called when file has been
            downloaded. It will be called even if exception occurred.
        @type callback: callable(url, result) where result may be Exception

        @param last_update: Timestamp of the newest file so far.
        @type last_update: int

        @return: Updated latest mtime.
        @rtype: int
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
            last_update = time.time()
        else:
            logging.info('%s already downloaded', lecture_filename)
            # if this file hasn't been modified in a long time,
            # record that time
            last_update = max(last_update,
                              os.path.getmtime(lecture_filename))
        return last_update

    def _run_hooks(self, section, hooks):
        original_dir = os.getcwd()
        for hook in hooks:
            logging.info('Running hook %s for section %s.',
                         hook, section.dir)
            os.chdir(section.dir)
            subprocess.call(hook)
        os.chdir(original_dir)
