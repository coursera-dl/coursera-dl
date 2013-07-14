# -*- coding: utf-8 -*-

"""
Manages the credential information (netrc, passwords, etc).
"""

import getpass
import logging
import netrc
import os
import platform


class CredentialsError(BaseException):
    """
    Class to be thrown if the credentials are not found.
    """

    pass


def _getenv_or_empty(s):
    """
    Helper function that converts None gotten from the environment to the
    empty string.
    """
    return os.getenv(s) or ""


def get_config_paths(config_name):
    """
    Returns a list of config files paths to try in order, given config file
    name and possibly a user-specified path.

    For Windows platforms, there are several paths that can be tried to
    retrieve the netrc file. There is, however, no "standard way" of doing
    things.

    A brief recap of the situation (all file paths are written in Unix
    convention):

    1. By default, Windows does not define a $HOME path. However, some
    people might define one manually, and many command-line tools imported
    from Unix will search the $HOME environment variable first. This
    includes MSYSGit tools (bash, ssh, ...) and Emacs.

    2. Windows defines two 'user paths': $USERPROFILE, and the
    concatenation of the two variables $HOMEDRIVE and $HOMEPATH. Both of
    these paths point by default to the same location, e.g.
    C:\\Users\\Username

    3. $USERPROFILE cannot be changed, however $HOMEDRIVE and $HOMEPATH
    can be changed. They are originally intended to be the equivalent of
    the $HOME path, but there are many known issues with them

    4. As for the name of the file itself, most of the tools ported from
    Unix will use the standard '.dotfile' scheme, but some of these will
    instead use "_dotfile". Of the latter, the two notable exceptions are
    vim, which will first try '_vimrc' before '.vimrc' (but it will try
    both) and git, which will require the user to name its netrc file
    '_netrc'.

    Relevant links :
    http://markmail.org/message/i33ldu4xl5aterrr
    http://markmail.org/message/wbzs4gmtvkbewgxi
    http://stackoverflow.com/questions/6031214/

    Because the whole thing is a mess, I suggest we tried various sensible
    defaults until we succeed or have depleted all possibilities.
    """

    if platform.system() != 'Windows':
        return [None]

    # Now, we only treat the case of Windows
    env_vars = [["HOME"],
                ["HOMEDRIVE", "HOMEPATH"],
                ["USERPROFILE"],
                ["SYSTEMDRIVE"]]

    env_dirs = []
    for var_list in env_vars:

        var_values = [_getenv_or_empty(var) for var in var_list]

        directory = ''.join(var_values)
        if not directory:
            logging.debug('Environment var(s) %s not defined, skipping',
                          var_list)
        else:
            env_dirs.append(directory)

    additional_dirs = ["C:", ""]

    all_dirs = env_dirs + additional_dirs

    leading_chars = [".", "_"]

    res = [''.join([directory, os.sep, lc, config_name])
           for directory in all_dirs
           for lc in leading_chars]

    return res


def authenticate_through_netrc(path=None):
    """
    Returns the tuple user / password given a path for the .netrc file.
    Raises CredentialsError if no valid netrc file is found.
    """
    errors = []
    paths = [path] if path else get_config_paths("netrc")
    for path in paths:
        try:
            logging.debug('Trying netrc file %s', path)
            auths = netrc.netrc(path).authenticators('coursera-dl')
            return (auths[0], auths[2])
        except (IOError, TypeError, netrc.NetrcParseError) as e:
            errors.append(e)

    error_messages = '\n'.join(str(e) for e in errors)
    raise CredentialsError(
        'Did not find valid netrc file:\n' + error_messages)


def get_credentials(username=None, password=None, netrc=None):
    """
    Returns valid username, password tuple.
    Raises CredentialsError if username or password is missing.
    """
    if netrc:
        path = None if netrc is True else netrc
        return authenticate_through_netrc(path)

    if not username:
        raise CredentialsError(
            'Please provide a username with the -u option, '
            'or a .netrc file with the -n option.')

    if not password:
        password = getpass.getpass(
            'Coursera password for {0}: '.format(username))

    return username, password
