"""
Test retrieving the credentials.
"""

import os.path
import unittest

from coursera import credentials

NETRC = \
    os.path.join(os.path.dirname(__file__),
                 "fixtures", "auth", "netrc")

NOT_NETRC = \
    os.path.join(os.path.dirname(__file__),
                 "fixtures", "auth", "not_netrc")


class CredentialsTestCase(unittest.TestCase):

    def test_authenticate_through_netrc_with_given_path(self):
        username, password = credentials.authenticate_through_netrc(NETRC)
        self.assertEquals(username, 'user@mail.com')
        self.assertEquals(password, 'secret')

    def test_authenticate_through_netrc_raises_exception(self):
        self.assertRaises(
            credentials.CredentialsError,
            credentials.authenticate_through_netrc,
            NOT_NETRC)

    def test_get_credentials_with_netrc(self):
        username, password = credentials.get_credentials(netrc=NETRC)
        self.assertEquals(username, 'user@mail.com')
        self.assertEquals(password, 'secret')

    def test_get_credentials_with_invalid_netrc_raises_exception(self):
        self.assertRaises(
            credentials.CredentialsError,
            credentials.get_credentials,
            netrc=NOT_NETRC)

    def test_get_credentials_with_username_and_password_given(self):
        username, password = credentials.get_credentials(
            username='user', password='pass')
        self.assertEquals(username, 'user')
        self.assertEquals(password, 'pass')

    def test_get_credentials_with_username_given(self):
        import getpass
        _getpass = getpass.getpass
        getpass.getpass = lambda x: 'pass'

        username, password = credentials.get_credentials(
            username='user')
        self.assertEquals(username, 'user')
        self.assertEquals(password, 'pass')

        getpass.getpass = _getpass

    def test_get_credentials_without_username_given_raises_exception(self):
        self.assertRaises(
            credentials.CredentialsError,
            credentials.get_credentials)
