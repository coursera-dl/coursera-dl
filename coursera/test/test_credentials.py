# -*- coding: utf-8 -*-

"""
Test retrieving the credentials.
"""

import os.path
import pytest

from coursera import credentials
from .test_utils import assertEquals, assertTrue, assertFalse, assertRaises

NETRC = \
    os.path.join(os.path.dirname(__file__),
                 "fixtures", "auth", "netrc")

NOT_NETRC = \
    os.path.join(os.path.dirname(__file__),
                 "fixtures", "auth", "not_netrc")


def test_authenticate_through_netrc_with_given_path():
    username, password = credentials.authenticate_through_netrc(NETRC)
    assert username == 'user@mail.com'
    assert password == 'secret'


def test_authenticate_through_netrc_raises_exception():
    assertRaises(
        credentials.CredentialsError,
        credentials.authenticate_through_netrc,
        NOT_NETRC)


def test_get_credentials_with_netrc():
    username, password = credentials.get_credentials(netrc=NETRC)
    assert username == 'user@mail.com'
    assert password == 'secret'


def test_get_credentials_with_invalid_netrc_raises_exception():
    assertRaises(
        credentials.CredentialsError,
        credentials.get_credentials,
        netrc=NOT_NETRC)


def test_get_credentials_with_username_and_password_given():
    username, password = credentials.get_credentials(
        username='user', password='pass')
    assert username == 'user'
    assert password == 'pass'


def test_get_credentials_with_username_given():
    import getpass
    _getpass = getpass.getpass
    getpass.getpass = lambda x: 'pass'

    username, password = credentials.get_credentials(
        username='user')
    assert username == 'user'
    assert password == 'pass'

    getpass.getpass = _getpass


def test_get_credentials_without_username_given_raises_exception():
    assertRaises(
        credentials.CredentialsError,
        credentials.get_credentials)
