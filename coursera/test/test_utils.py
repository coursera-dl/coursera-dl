# -*- coding: utf-8 -*-

"""
Test the utility functions.
"""

import unittest
import six

from coursera import utils


class UtilsTestCase(unittest.TestCase):

    def test_clean_filename(self):
        strings = {
            '(23:90)': '',
            '(:': '',
            'a téest &and a@noòtheèr': 'a_test_and_another',
            'Lecture 2.7 - Evaluation and Operators (16:25)':
            'Lecture_2.7_-_Evaluation_and_Operators',
            'Week 3: Data and Abstraction':
            'Week_3-_Data_and_Abstraction'
        }
        for k, v in six.iteritems(strings):
            self.assertEquals(utils.clean_filename(k), v)

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
            '  (Week 1) BRANDING-  Marketing Strategy and Brand Positioning'
        }
        for k, v in six.iteritems(strings):
            self.assertEquals(utils.clean_filename(k, minimal_change=True), v)

    def test_get_anchor_format(self):
        strings = {
            'https://class.coursera.org/sub?q=123_en&format=txt': 'txt',
            'https://class.coursera.org/sub?q=123_en&format=srt': 'srt',
            'https://d396qusza40orc.cloudfront.net/week7-4.pdf': 'pdf',
            'https://class.coursera.org/download.mp4?lecture_id=123': 'mp4'
        }
        for k, v in six.iteritems(strings):
            self.assertEquals(utils.get_anchor_format(k), v)

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
