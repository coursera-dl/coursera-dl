from os.path import normpath
import pytest
import requests
from requests.exceptions import RequestException

from coursera.workflow import CourseraDownloader, _iter_modules, _walk_modules
from coursera.commandline import parse_args
from coursera.parallel import ConsecutiveDownloader, ParallelDownloader
from coursera.downloaders import Downloader


class MockedCommandLineArgs(object):
    """
    This mock uses default arguments from parse_args and allows to overwrite
    them in constructor.
    """
    def __init__(self, **kwargs):
        args = parse_args('-u username -p password test_class'.split())
        self.__dict__.update(args.__dict__)
        self.__dict__.update(kwargs)

    def __repr__(self):
        return self.__dict__.__repr__()


class MockedFailingDownloader(Downloader):
    """
    This mock will raise whatever exception you pass to it in constructor
    in _start_download method. Pass None to prevent any exception.
    """
    def __init__(self, exception_to_throw):
        self._exception_to_throw = exception_to_throw

    def _start_download(self, *args, **kwargs):
        if self._exception_to_throw is None:
            return
        raise self._exception_to_throw


TEST_URL = "https://www.coursera.org/api/test-url"


def make_test_modules():
    modules = [
        ["section1",
         [
             ["module1",
              [
                  ["lecture1",
                   {"en.txt": [
                       [TEST_URL,
                        "title"
                       ]
                   ]
                   }
                  ]
              ]
             ]
         ]
        ]
    ]
    return modules


@pytest.mark.parametrize(
    'expected_failed_urls,exception_to_throw,downloader_wrapper_class', [
        ([], None, ConsecutiveDownloader),
        ([], None, ParallelDownloader),
        ([TEST_URL], RequestException('Test exception'), ConsecutiveDownloader),
        ([TEST_URL], RequestException('Test exception'), ParallelDownloader),
        ([TEST_URL], Exception('Test exception'), ConsecutiveDownloader),
        ([TEST_URL], Exception('Test exception'), ParallelDownloader),
        ([TEST_URL], ValueError('Test exception'), ConsecutiveDownloader),
        ([TEST_URL], ValueError('Test exception'), ParallelDownloader),
        ([TEST_URL], AttributeError('Test exception'), ConsecutiveDownloader),
        ([TEST_URL], AttributeError('Test exception'), ParallelDownloader),
    ]
)
def test_failed_urls_are_collected(expected_failed_urls,
                                   exception_to_throw,
                                   downloader_wrapper_class):
    """
    This test makes sure that if there was an exception in the file downloader,
    downloader wrapper will intercept it and course downloader will record
    the problematic URL.
    """
    file_downloader = MockedFailingDownloader(exception_to_throw)
    course_downloader = CourseraDownloader(
        downloader=downloader_wrapper_class(file_downloader),
        commandline_args=MockedCommandLineArgs(overwrite=True),
        class_name='test_class',
        path='',
        ignored_formats=None,
        disable_url_skipping=False)
    modules = make_test_modules()

    course_downloader.download_modules(modules)
    assert expected_failed_urls == course_downloader.failed_urls


def test_iter_modules():
    """
    Test that all modules are iterated and intermediate values are formatted
    correctly. Filtering is not tested at the moment.
    """
    modules = make_test_modules()
    args = MockedCommandLineArgs()

    expected_output = [
        (0, '01_section1'),
        (0, normpath('test_class/01_section1/01_module1')),
        (0, 'lecture1', 'en.txt', 'title'),
        ('en.txt', 'https://www.coursera.org/api/test-url', 'title')
    ]
    collected_output = []

    for module in _iter_modules(modules=modules, class_name='test_class',
                                path='', ignored_formats=None, args=args):
        collected_output.append((module.index, module.name))
        for section in module.sections:
            collected_output.append((section.index, section.dir))
            for lecture in section.lectures:
                for resource in lecture.resources:
                    collected_output.append((lecture.index, lecture.name,
                                             resource.fmt, resource.title))
                    collected_output.append((resource.fmt, resource.url, resource.title))

    assert expected_output == collected_output

def test_walk_modules():
    """
    Test _walk_modules, a flattened version of _iter_modules.
    """
    modules = make_test_modules()
    args = MockedCommandLineArgs()

    expected_output = [
        (0, '01_section1',
         0, normpath('test_class/01_section1/01_module1'),
         0, 'lecture1', normpath('test_class/01_section1/01_module1/01_lecture1_title.en.txt'),
         'https://www.coursera.org/api/test-url')]
    collected_output = []

    for module, section, lecture, resource in _walk_modules(
            modules=modules, class_name='test_class',
            path='', ignored_formats=None, args=args):

        collected_output.append(
            (module.index, module.name,
             section.index, section.dir,
             lecture.index, lecture.name, lecture.filename(resource.fmt, resource.title),
             resource.url)
        )

    assert expected_output == collected_output
