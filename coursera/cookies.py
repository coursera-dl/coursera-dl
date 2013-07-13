# -*- coding: utf-8 -*-

"""
Cookie handling module.
"""

import cookielib
import logging
import os
import StringIO

import requests

from .define import AUTH_URL, CLASS_URL, AUTH_REDIRECT_URL, PATH_COOKIES
from .utils import mkdir_p


# Monkey patch cookielib.Cookie.__init__.
# Reason: The expires value may be a decimal string,
# but the Cookie class uses int() ...
__orginal_init__ = cookielib.Cookie.__init__


def __fixed_init__(self, version, name, value,
                   port, port_specified,
                   domain, domain_specified, domain_initial_dot,
                   path, path_specified,
                   secure,
                   expires,
                   discard,
                   comment,
                   comment_url,
                   rest,
                   rfc2109=False,
                   ):
    if expires is not None:
        expires = float(expires)
    __orginal_init__(self, version, name, value,
                     port, port_specified,
                     domain, domain_specified, domain_initial_dot,
                     path, path_specified,
                     secure,
                     expires,
                     discard,
                     comment,
                     comment_url,
                     rest,
                     rfc2109=False,)

cookielib.Cookie.__init__ = __fixed_init__


class ClassNotFound(BaseException):
    """
    Raised if a course is not found in Coursera's site.
    """


class AuthenticationFailed(BaseException):
    """
    Raised if we cannot authenticate on Coursera's site.
    """


def login(session, class_name, username, password):
    """
    Login on www.coursera.org with the given credentials.
    This adds the following cookies to the session:
        sessionid, maestro_login, maestro_login_flag
    """

    try:
        session.cookies.clear('www.coursera.org')
    except KeyError:
        pass

    # Hit class url to obtain csrf_token
    class_url = CLASS_URL.format(class_name=class_name)
    r = requests.get(class_url, allow_redirects=False)

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error(e)
        raise ClassNotFound(class_name)

    csrftoken = r.cookies.get('csrf_token')

    if not csrftoken:
        raise AuthenticationFailed('Did not recieve csrf_token cookie.')

    # Now make a call to the authenticator url.
    headers = {
        'Cookie': 'csrftoken=' + csrftoken,
        'Referer': 'https://www.coursera.org',
        'X-CSRFToken': csrftoken,
    }

    data = {
        'email_address': username,
        'password': password
    }

    r = session.post(AUTH_URL, data=data,
                     headers=headers, allow_redirects=False)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        raise AuthenticationFailed('Cannot login on www.coursera.org.')

    logging.info('Logged in on www.coursera.org.')


def down_the_wabbit_hole(session, class_name):
    """
    Authenticate on class.coursera.org
    """

    auth_redirector_url = AUTH_REDIRECT_URL.format(class_name=class_name)
    r = session.get(auth_redirector_url)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        raise AuthenticationFailed('Cannot login on class.coursera.org.')


def _get_authentication_cookies(session, class_name,
                                username, password, retry=False):
    try:
        session.cookies.clear('class.coursera.org', '/' + class_name)
    except KeyError:
        pass

    down_the_wabbit_hole(session, class_name)

    enough = do_we_have_enough_cookies(session.cookies, class_name)

    if not enough:
        if retry:
            logging.info('Renew session on www.coursera.org.')
            login(session, class_name, username, password)
            _get_authentication_cookies(
                session, class_name, username, password, False)
        else:
            raise AuthenticationFailed('Did not find necessary cookies.')


def get_authentication_cookies(session, class_name, username, password):
    """
    Get the necessary cookies to authenticate on class.coursera.org.

    To access the class pages we need two cookies on class.coursera.org:
        csrf_token, session
    """

    # First, check if we already have the www.coursera.org cookies.
    if session.cookies.get('maestro_login', domain="www.coursera.org"):
        logged_in = True
        logging.debug('Already logged in on www.coursera.org.')
    else:
        logged_in = False
        login(session, class_name, username, password)

    # If logged_in, allow retry in case of stale sessions
    # (session time-out, ...)
    _get_authentication_cookies(
        session, class_name, username, password, logged_in)

    logging.info('Found authentication cookies.')


def do_we_have_enough_cookies(cj, class_name):
    """
    Checks whether we have all the required cookies
    to authenticate on class.coursera.org.
    """
    domain = 'class.coursera.org'
    path = "/" + class_name

    return cj.get('session', domain=domain, path=path) \
        and cj.get('csrf_token', domain=domain, path=path)


def do_we_have_valid_cookies(session, class_name):
    """
    Checks whether we have all the required cookies
    to authenticate on class.coursera.org, and if they are not yet stale.
    """
    if not do_we_have_enough_cookies(session.cookies, class_name):
        return False

    url = CLASS_URL.format(class_name=class_name) + '/class'
    r = session.head(url, allow_redirects=False)

    if r.status_code == 200:
        return True
    else:
        logging.debug('Stale session.')
        return False


def make_cookie_values(cj, class_name):
    """
    Makes a string of cookie keys and values.
    Can be used to set a Cookie header.
    """
    path = "/" + class_name

    cookies = [c.name + '=' + c.value
               for c in cj
               if c.domain == "class.coursera.org"
               and c.path == path]

    return '; '.join(cookies)


def find_cookies_for_class(cookies_file, class_name):
    """
    Return a RequestsCookieJar containing the cookies for
    www.coursera.org and class.coursera.org found in the given cookies_file.
    """

    path = "/" + class_name

    def cookies_filter(c):
        return c.domain == "www.coursera.org" \
            or (c.domain == "class.coursera.org" and c.path == path)

    cj = get_cookie_jar(cookies_file)
    cookies_list = filter(cookies_filter, cj)

    new_cj = requests.cookies.RequestsCookieJar()
    for c in cookies_list:
        new_cj.set_cookie(c)

    return new_cj


def load_cookies_file(cookies_file):
    """
    Loads the cookies file.

    We pre-pend the file with the special Netscape header because the cookie
    loader is very particular about this string.
    """

    cookies = StringIO.StringIO()
    cookies.write('# Netscape HTTP Cookie File')
    cookies.write(open(cookies_file, 'rU').read())
    cookies.flush()
    cookies.seek(0)
    return cookies


def get_cookie_jar(cookies_file):
    cj = cookielib.MozillaCookieJar()
    cookies = load_cookies_file(cookies_file)

    # nasty hack: cj.load() requires a filename not a file, but if I use
    # stringio, that file doesn't exist. I used NamedTemporaryFile before,
    # but encountered problems on Windows.
    cj._really_load(cookies, 'StringIO.cookies', False, False)

    return cj


def get_cookies_cache_path(username):
    return os.path.join(PATH_COOKIES, username + '.txt')


def get_cookies_from_cache(username):
    """
    Returns a RequestsCookieJar containing the cached cookies for the given
    user.
    """
    path = get_cookies_cache_path(username)
    cj = requests.cookies.RequestsCookieJar()
    try:
        cached_cj = get_cookie_jar(path)
        for cookie in cached_cj:
            cj.set_cookie(cookie)
        logging.debug(
            'Loaded cookies from %s', get_cookies_cache_path(username))
    except IOError:
        pass

    return cj


def write_cookies_to_cache(cj, username):
    """
    Saves the RequestsCookieJar to disk in the Mozilla cookies.txt file format.
    This prevents us from repeated authentications on the www.coursera.org and
    class.coursera.org/class_name sites.
    """
    mkdir_p(PATH_COOKIES)
    path = get_cookies_cache_path(username)
    cached_cj = cookielib.MozillaCookieJar()
    for cookie in cj:
        cached_cj.set_cookie(cookie)
    cached_cj.save(path)


def get_cookies_for_class(session, class_name,
                          cookies_file=None,
                          username=None,
                          password=None):
    """
    Get the cookies for the given class.
    We do not validate the cookies if they are loaded from a cookies file
    because this is intented for debugging purposes or if the coursera
    authentication process has changed.
    """
    if cookies_file:
        cookies = find_cookies_for_class(cookies_file, class_name)
        session.cookies.update(cookies)
        logging.info('Loaded cookies from %s', cookies_file)
    else:
        cookies = get_cookies_from_cache(username)
        session.cookies.update(cookies)
        if do_we_have_valid_cookies(session, class_name):
            logging.info('Already authenticated.')
        else:
            get_authentication_cookies(session, class_name, username, password)
            write_cookies_to_cache(session.cookies, username)
