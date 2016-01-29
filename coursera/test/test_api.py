"""
Test APIs.
"""
import os
import json

import pytest
from mock import patch

from coursera import api


@pytest.fixture
def course():
    course = api.CourseraOnDemand(session=None, course_json={'id': 0})
    return course


def slurp_fixture(path):
    return open(os.path.join(os.path.dirname(__file__),
                             "fixtures", path)).read()


@patch('coursera.api.get_page')
def test_ondemand_programming_supplement_no_instructions(get_page, course):
    no_instructions = slurp_fixture('json/supplement-programming-no-instructions.json')
    get_page.return_value = no_instructions

    files = course.extract_files_from_programming('0')
    assert {} == files


@patch('coursera.api.get_page')
def test_ondemand_programming_supplement_empty_instructions(get_page, course):
    empty_instructions = slurp_fixture('json/supplement-programming-empty-instructions.json')
    get_page.return_value = empty_instructions

    files = course.extract_files_from_programming('0')
    assert {} == files


@patch('coursera.api.get_page')
def test_ondemand_programming_supplement_one_asset(get_page, course):
    one_asset_tag = slurp_fixture('json/supplement-programming-one-asset.json')
    one_asset_url = slurp_fixture('json/asset-urls-one.json')
    asset_json = json.loads(one_asset_url)
    get_page.side_effect = [one_asset_tag, one_asset_url]

    expected_files = {'pdf': [(asset_json['elements'][0]['url'],
                               'statement-pca')]}
    files = course.extract_files_from_programming('0')
    assert expected_files == files


@patch('coursera.api.get_page')
def test_ondemand_programming_supplement_three_assets(get_page, course):
    three_assets_tag = slurp_fixture('json/supplement-programming-three-assets.json')
    three_assets_url = slurp_fixture('json/asset-urls-three.json')
    asset_json = json.loads(three_assets_url)
    get_page.side_effect = [three_assets_tag, three_assets_url]

    expected_files = {
        'csv': [(asset_json['elements'][0]['url'], 'close_prices'),
                (asset_json['elements'][2]['url'], 'djia_index')],
        'pdf': [(asset_json['elements'][1]['url'], 'statement-pca')]
    }
    files = course.extract_files_from_programming('0')
    assert expected_files == files
