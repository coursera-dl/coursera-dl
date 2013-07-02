"""
Test the downloaders.
"""

import unittest

from coursera import downloaders


class ExternalDownloaderTestCase(unittest.TestCase):

    def _get_session(self):
        import time
        import requests

        expires = int(time.time() + 60*60*24*365*50)

        s = requests.Session()
        s.cookies.set('csrf_token', 'csrfclass001',
                      domain="www.coursera.org", expires=expires)
        s.cookies.set('session', 'sessionclass1',
                      domain="www.coursera.org", expires=expires)
        s.cookies.set('k', 'v',
                      domain="www.example.org", expires=expires)

        return s

    def test_bin_not_specified(self):
        self.assertRaises(RuntimeError, downloaders.ExternalDownloader, None)

    def test_bin_not_found_raises_exception(self):
        d = downloaders.ExternalDownloader(None, bin='no_way_this_exists')
        d._prepare_cookies = lambda cmd, cv: None
        d._create_command = lambda x, y: ['no_way_this_exists']
        self.assertRaises(OSError, d._start_download, 'url', 'filename')

    def test_bin_is_set(self):
        d = downloaders.ExternalDownloader(None, bin='test')
        self.assertEquals(d.bin, 'test')

    def test_prepare_cookies(self):
        s = self._get_session()

        d = downloaders.ExternalDownloader(s, bin="test")

        def mock_add_cookies(cmd, cv):
            cmd.append(cv)

        d._add_cookies = mock_add_cookies
        command = []
        d._prepare_cookies(command, 'http://www.coursera.org')
        self.assertEquals(
            command, ['csrf_token=csrfclass001; session=sessionclass1'])

    def test_prepare_cookies_does_nothing(self):
        s = self._get_session()
        s.cookies.clear(domain="www.coursera.org")

        d = downloaders.ExternalDownloader(s, bin="test")
        command = []

        def mock_add_cookies(cmd, cookie_values):
            pass

        d._add_cookies = mock_add_cookies

        d._prepare_cookies(command, 'http://www.coursera.org')
        self.assertEquals(command, [])

    def test_start_command_raises_exception(self):
        d = downloaders.ExternalDownloader(None, bin='test')
        d._add_cookies = lambda cmd, cookie_values: None
        self.assertRaises(
            NotImplementedError,
            d._create_command, 'url', 'filename')

    def test_wget(self):
        s = self._get_session()

        d = downloaders.WgetDownloader(s)
        command = d._create_command('download_url', 'save_to')
        self.assertEquals(command[0], 'wget')
        self.assertTrue('download_url' in command)
        self.assertTrue('save_to' in command)

        d._prepare_cookies(command, 'http://www.coursera.org')
        cv = 'csrf_token=csrfclass001; session=sessionclass1'
        self.assertTrue("Cookie: " + cv in command)

    def test_curl(self):
        s = self._get_session()

        d = downloaders.CurlDownloader(s)
        command = d._create_command('download_url', 'save_to')
        self.assertEquals(command[0], 'curl')
        self.assertTrue('download_url' in command)
        self.assertTrue('save_to' in command)

        d._prepare_cookies(command, 'http://www.coursera.org')
        cv = 'csrf_token=csrfclass001; session=sessionclass1'
        self.assertTrue(cv in command)

    def test_arai2(self):
        s = self._get_session()

        d = downloaders.Aria2Downloader(s)
        command = d._create_command('download_url', 'save_to')
        self.assertEquals(command[0], 'aria2c')
        self.assertTrue('download_url' in command)
        self.assertTrue('save_to' in command)

        d._prepare_cookies(command, 'http://www.coursera.org')
        cv = 'csrf_token=csrfclass001; session=sessionclass1'
        self.assertTrue("Cookie: " + cv in command)

    def test_axel(self):
        s = self._get_session()

        d = downloaders.AxelDownloader(s)
        command = d._create_command('download_url', 'save_to')
        self.assertEquals(command[0], 'axel')
        self.assertTrue('download_url' in command)
        self.assertTrue('save_to' in command)

        d._prepare_cookies(command, 'http://www.coursera.org')
        cv = 'csrf_token=csrfclass001; session=sessionclass1'
        self.assertTrue("Cookie: " + cv in command)


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
