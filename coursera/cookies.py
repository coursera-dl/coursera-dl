# -*- coding: utf-8 -*-

"""
Cookie handling module.
"""

import cookielib
import logging
import os
import StringIO

import requests

from define import AUTH_URL, CLASS_URL, AUTH_REDIRECT_URL

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
    """

    # Hit class url to obtain csrf_token
    class_url = CLASS_URL.format(class_name=class_name)
    r = requests.get(class_url, allow_redirects=False)

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
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


def get_authentication_cookies(session, class_name):
    """
    Get the necessary cookies to authenticate on class.coursera.org.

    At this moment we should have the following cookies on www.coursera.org:
        maestro_login_flag, sessionid, maestro_login
    To access the class pages we need two cookies on class.coursera.org:
        csrf_token, session
    """

    # First, check if we already have the class.coursera.org cookies.
    enough = do_we_have_enough_cookies(session.cookies, class_name)

    if not enough:
        # Get the class.coursera.org cookies. Remember that we need
        # the cookies from www.coursera.org!
        down_the_wabbit_hole(session, class_name)

        enough = do_we_have_enough_cookies(session.cookies, class_name)

        if not enough:
            raise AuthenticationFailed('Did not find necessary cookies.')

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
