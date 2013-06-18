"""
Test the downloaders.
"""

import unittest

from coursera import downloaders


class ExternalDownloaderTestCase(unittest.TestCase):

    def test_bin_not_specified(self):
        self.assertRaises(RuntimeError, downloaders.ExternalDownloader)

    def test_bin_not_found_raises_exception(self):
        d = downloaders.ExternalDownloader(bin='no_way_this_exists')
        d._create_command = lambda x, y: ['no_way_this_exists']
        self.assertRaises(OSError, d._start_download, 'url', 'filename')

    def test_bin_is_set(self):
        d = downloaders.ExternalDownloader(bin='test')
        self.assertEquals(d.bin, 'test')

    def test_cookie_values(self):
        cookies_dict = {
            'csrf_token': 'csrfclass001',
            'session': 'sessionclass1'
        }
        d = downloaders.ExternalDownloader(
            cookies_dict=cookies_dict, bin="test")
        values = 'csrf_token=csrfclass001; session=sessionclass1'
        self.assertEquals(d.cookie_values(), values)

    def test_cookie_values_is_empty(self):
        d = downloaders.ExternalDownloader(bin="test")
        self.assertEquals(d.cookie_values(), "")

    def test_start_command_raises_exception(self):
        d = downloaders.ExternalDownloader(bin='test')
        self.assertRaises(
            NotImplementedError,
            d._create_command, 'url', 'filename')

    def test_wget(self):
        d = downloaders.WgetDownloader(cookies_dict={'key': 'value'})
        command = d._create_command('download_url', 'save_to')
        self.assertEquals(command[0], 'wget')
        self.assertTrue('download_url' in command)
        self.assertTrue('save_to' in command)
        self.assertTrue("Cookie: " + d.cookie_values() in command)

    def test_curl(self):
        d = downloaders.CurlDownloader(cookies_dict={'key': 'value'})
        command = d._create_command('download_url', 'save_to')
        self.assertEquals(command[0], 'curl')
        self.assertTrue('download_url' in command)
        self.assertTrue('save_to' in command)
        self.assertTrue(d.cookie_values() in command)

    def test_arai2(self):
        d = downloaders.Aria2Downloader(cookies_dict={'key': 'value'})
        command = d._create_command('download_url', 'save_to')
        self.assertEquals(command[0], 'aria2')
        self.assertTrue('download_url' in command)
        self.assertTrue('save_to' in command)
        self.assertTrue("Cookie: " + d.cookie_values() in command)

    def test_axel(self):
        d = downloaders.AxelDownloader(cookies_dict={'key': 'value'})
        command = d._create_command('download_url', 'save_to')
        self.assertEquals(command[0], 'axel')
        self.assertTrue('download_url' in command)
        self.assertTrue('save_to' in command)
        self.assertTrue("Cookie: " + d.cookie_values() in command)


class NativeDownloaderTestCase(unittest.TestCase):

    def test_all_attempts_have_failed(self):
        import time

        class IObject(object):
            pass

        class MockSession:

            def get(self, url, stream=True):
                object_ = IObject()
                object_.status_code = 400
                object_.reason = None
                return object_

        _sleep = time.sleep
        time.sleep = lambda interval: 0

        session = MockSession()
        d = downloaders.NativeDownloader(session)
        self.assertFalse(d._start_download('download_url', 'save_to'))

        time.sleep = _sleep
