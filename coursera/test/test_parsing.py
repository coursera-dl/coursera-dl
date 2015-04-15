#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test functionality of coursera module.
"""
import json
import os.path
import pytest

from six import iteritems
from mock import patch, Mock, mock_open

from coursera import coursera_dl
from .test_utils import assertEqual, assertEquals, assertTrue, assertFalse, assertRaises


# JSon Handling

@pytest.fixture
def get_page(monkeypatch):
    monkeypatch.setattr(coursera_dl, 'get_page', Mock())

@pytest.fixture
def json_path():
    return os.path.join(os.path.dirname(__file__), "fixtures", "json")


def test_that_should_not_dl_if_file_exist(get_page, json_path):
    coursera_dl.get_page = Mock()
    coursera_dl.download_about(object(), "matrix-002", json_path)
    assertFalse(coursera_dl.get_page.called)

def test_that_we_parse_and_write_json_correctly(get_page, json_path):

    raw_data = open(os.path.join(os.path.dirname(__file__), "fixtures", "json", "unprocessed.json")).read()
    coursera_dl.get_page = lambda x, y: raw_data
    open_mock = mock_open()

    with patch('coursera.coursera_dl.open', open_mock, create=True):

        coursera_dl.download_about(object(), "networksonline-002", json_path)

    open_mock.assert_called_once_with(os.path.join(json_path, 'networksonline-002-about.json'), 'w')

    data = json.loads(open_mock().write.call_args[0][0])

    assertEqual(data['id'], 394)
    assertEqual(data['shortName'], 'networksonline')


# Test Syllabus Parsing

@pytest.fixture
def get_video(monkeypatch):
    """
    mock some methods that would, otherwise, create
    repeateadly many web requests.

    More specifically, we mock:

    * the search for hidden videos
    * the actual download of videos
    """

    # Mock coursera_dl.grab_hidden_video_url
    monkeypatch.setattr(coursera_dl, 'grab_hidden_video_url',
                        lambda session, href: None)

    # Mock coursera_dl.get_video
    monkeypatch.setattr(coursera_dl, 'get_video',
                        lambda session, href: None)


def _assert_parse(filename, num_sections, num_lectures,
                    num_resources, num_videos):
    filename = os.path.join(
        os.path.dirname(__file__), "fixtures", "html",
        filename)

    with open(filename) as syllabus:
        syllabus_page = syllabus.read()

        sections = coursera_dl.parse_syllabus(None, syllabus_page, None)

        # section count
        assertEqual(len(sections), num_sections)

        # lecture count
        lectures = [lec for sec in sections for lec in sec[1]]
        assertEqual(len(lectures), num_lectures)

        # resource count
        resources = [(res[0], len(res[1]))
                        for lec in lectures for res in iteritems(lec[1])]
        assertEqual(sum(r for f, r in resources), num_resources)

        # mp4 count
        assertEqual(
            sum(r for f, r in resources if f == "mp4"),
            num_videos)

def test_parse(get_video):
    _assert_parse(
        "regular-syllabus.html",
        num_sections=23,
        num_lectures=102,
        num_resources=502,
        num_videos=102)

def test_links_to_wikipedia(get_video):
    _assert_parse(
        "links-to-wikipedia.html",
        num_sections=5,
        num_lectures=37,
        num_resources=158,
        num_videos=36)

def test_parse_preview(get_video):
    _assert_parse(
        "preview.html",
        num_sections=20,
        num_lectures=106,
        num_resources=106,
        num_videos=106)

def test_sections_missed(get_video):
    _assert_parse(
        "sections-not-to-be-missed.html",
        num_sections=9,
        num_lectures=61,
        num_resources=224,
        num_videos=61)

def test_sections_missed2(get_video):
    _assert_parse(
        "sections-not-to-be-missed-2.html",
        num_sections=20,
        num_lectures=121,
        num_resources=397,
        num_videos=121)

def test_parse_classes_with_bs4(get_video):
    classes = {
        'datasci-001': (10, 97, 358, 97),  # issue 134
        'startup-001': (4, 44, 136, 44),   # issue 137
        'wealthofnations-001': (8, 74, 296, 74),  # issue 131
        'malsoftware-001': (3, 18, 56, 16)  # issue 148
    }

    for class_, counts in iteritems(classes):
        filename = "parsing-{0}-with-bs4.html".format(class_)
        _assert_parse(
            filename,
            num_sections=counts[0],
            num_lectures=counts[1],
            num_resources=counts[2],
            num_videos=counts[3])

def test_multiple_resources_with_the_same_format(get_video):
    _assert_parse(
        "multiple-resources-with-the-same-format.html",
        num_sections=18,
        num_lectures=97,
        num_resources=478,
        num_videos=97)


