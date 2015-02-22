# -*- coding: utf-8 -*-

"""
Test the utility functions.
"""
import datetime
import os
import random
import unittest
from time import time

import requests
import six

from mock import Mock
from coursera import utils
from coursera import coursera_dl


class UtilsTestCase(unittest.TestCase):

    def test_clean_filename(self):
        strings = {
            '(23:90)': '23-90',
            '(:': '-',
            'a téest &and a@noòtheèr': 'a_test_and_another',
            'Lecture 2.7 - Evaluation and Operators (16:25)':
            'Lecture_2.7_-_Evaluation_and_Operators_16-25',
            'Week 3: Data and Abstraction':
            'Week_3-_Data_and_Abstraction',
            '  (Week 1) BRANDING:  Marketing Strategy and Brand Positioning':
            'Week_1_BRANDING-__Marketing_Strategy_and_Brand_Positioning',
            'test &amp; &quot; adfas': 'test___adfas',
            '&nbsp;': ''
        }
        for k, v in six.iteritems(strings):
            actual_res = utils.clean_filename(k)
            self.assertEquals(actual_res, v, actual_res)

    def test_clean_filename_minimal_change(self):
        strings = {
            '(23:90)': '(23-90)',
            '(:': '(-',
            'a téest &and a@noòtheèr': 'a téest &and a@noòtheèr',
            'Lecture 2.7 - Evaluation and Operators (16:25)':
            'Lecture 2.7 - Evaluation and Operators (16-25)',
            'Week 3: Data and Abstraction':
            'Week 3- Data and Abstraction',
            '  (Week 1) BRANDING:  Marketing Strategy and Brand Positioning':
            '  (Week 1) BRANDING-  Marketing Strategy and Brand Positioning',
            'test &amp; &quot; adfas': 'test & " adfas',
            '&nbsp;': u'\xa0'
        }
        for k, v in six.iteritems(strings):
            actual_res = utils.clean_filename(k, minimal_change=True)
            self.assertEquals(actual_res, v, actual_res)

    def test_get_anchor_format(self):
        strings = {
            'https://class.coursera.org/sub?q=123_en&format=txt': 'txt',
            'https://class.coursera.org/sub?q=123_en&format=srt': 'srt',
            'https://d396qusza40orc.cloudfront.net/week7-4.pdf': 'pdf',
            'https://class.coursera.org/download.mp4?lecture_id=123': 'mp4'
        }
        for k, v in six.iteritems(strings):
            self.assertEquals(utils.get_anchor_format(k), v)

    def test_random_string(self):
        random.seed(0)  # set seed for reproducible tests

        res = utils.random_string(8)
        self.assertEqual(len(res), 8)

        # Python 2 and Python 3 use different strategies for generation of
        # PRNG, according to the documentation available at
        # https://docs.python.org/3.4/library/random.html#random.seed
        if six.PY2:
            self.assertEqual(res, '0UAqFzWs')
        else:
            self.assertEqual(res, '2yW4Acq9')


    def test_fix_url_ads_sheme(self):
        url = "www.coursera.org"
        self.assertEquals(utils.fix_url(url), 'http://www.coursera.org')

    def test_fix_url_removes_sheme(self):
        url = " www.coursera.org "
        self.assertEquals(utils.fix_url(url), 'http://www.coursera.org')

    def test_fix_url_doesnt_alters_empty_url(self):
        url = None
        self.assertEquals(utils.fix_url(url), None)

        url = ""
        self.assertEquals(utils.fix_url(url), "")

    def test_decode_input(self):
        encoded_inputs = [
            str("/home/user/темп"),
            str("22少女時代22")]

        for encoded_input in encoded_inputs:
            decoded_input = utils.decode_input(encoded_input)
            self.assertTrue(isinstance(decoded_input, six.text_type),
                            "Decoded input is not a text type.")

    def test_total_seconds(self):
        ts = coursera_dl.total_seconds(datetime.timedelta(days=30))
        self.assertEquals(ts, 2592000)

    def test_is_course_complete_should_give_false_if_there_was_recent_update(self):

        delta = datetime.timedelta(days=29).total_seconds()
        tm = time() - delta

        rv = coursera_dl.is_course_complete(tm)
        self.assertFalse(rv)

    def test_is_course_complete_should_give_true_if_there_was_no_recent_update(self):

        delta = datetime.timedelta(days=31).total_seconds()
        tm = time() - delta

        rv = coursera_dl.is_course_complete(tm)
        self.assertTrue(rv)


    def test_parse_args(self):
        args = coursera_dl.parseArgs(['-u', 'bob', '-p', 'bill', 'posa-001'])

        self.assertEquals(args.about, False)
        self.assertEquals(args.class_names, ['posa-001'])
        self.assertEquals(args.username, 'bob')
        self.assertEquals(args.password, 'bill')

    def get_mock_session(self, page_text):
        page_obj = Mock()
        page_obj.text = page_text
        page_obj.raise_for_status = Mock()
        session = requests.Session()
        session.get = Mock(return_value=page_obj)
        return page_obj, session

    def test_get_page(self):
        page_obj, session = self.get_mock_session('<page/>')

        p = coursera_dl.get_page(session, 'http://www.not.here')

        session.get.assert_called_once_with('http://www.not.here')
        page_obj.raise_for_status.assert_called_once()
        self.assertEquals(p, '<page/>')

    def test_grab_hidden_video_url(self):
        filename = os.path.join(
            os.path.dirname(__file__), "fixtures", "html",
            "hidden-videos_2.html")

        page_text = open(filename).read()
        page_obj, session = self.get_mock_session(page_text)
        p = coursera_dl.grab_hidden_video_url(session,
                                              'http://www.hidden.video')
        self.assertEquals('video1.mp4', p)
