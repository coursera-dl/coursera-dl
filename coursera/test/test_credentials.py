"""
Test retrieving the credentials.
"""

import os.path
import unittest

from coursera import credentials

NETRC = \
    os.path.join(os.path.dirname(__file__),
                 "fixtures", "netrc")

NOT_NETRC = \
    os.path.join(os.path.dirname(__file__),
                 "fixtures", "not_netrc")


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
