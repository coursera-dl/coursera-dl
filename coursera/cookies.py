# -*- coding: utf-8 -*-

"""
Cookie handling module.
"""

import logging
import os
import ssl

import requests
from requests.adapters import HTTPAdapter

try:  # Workaround for broken Debian/Ubuntu packages? (See issue #331)
    from requests.packages.urllib3.poolmanager import PoolManager
except ImportError:
    from urllib3.poolmanager import PoolManager


from six.moves import StringIO
from six.moves import http_cookiejar as cookielib
from .define import CLASS_URL, AUTH_REDIRECT_URL, PATH_COOKIES, AUTH_URL_V3
from .utils import mkdir_p, random_string

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
                   rfc2109=False):
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
                     rfc2109=False)


cookielib.Cookie.__init__ = __fixed_init__


class ClassNotFound(BaseException):
    """
    Raised if a course is not found in Coursera's site.
    """


class AuthenticationFailed(BaseException):
    """
    Raised if we cannot authenticate on Coursera's site.
    """


def prepare_auth_headers(session, include_cauth=False):
    """
    This function prepares headers with CSRF/CAUTH tokens that can
    be used in POST requests such as login/get_quiz.

    @param session: Requests session.
    @type session: requests.Session

    @param include_cauth: Flag that indicates whether CAUTH cookies should be
        included as well.
    @type include_cauth: bool

    @return: Dictionary of headers.
    @rtype: dict
    """

    # csrftoken is simply a 20 char random string.
    csrftoken = random_string(20)

    # Now make a call to the authenticator url.
    csrf2cookie = 'csrf2_token_%s' % random_string(8)
    csrf2token = random_string(24)
    cookie = "csrftoken=%s; %s=%s" % (csrftoken, csrf2cookie, csrf2token)

    if include_cauth:
        CAUTH = session.cookies.get('CAUTH')
        cookie = "CAUTH=%s; %s" % (CAUTH, cookie)

    logging.debug('Forging cookie header: %s.', cookie)
    headers = {
        'Cookie': cookie,
        'X-CSRFToken': csrftoken,
        'X-CSRF2-Cookie': csrf2cookie,
        'X-CSRF2-Token': csrf2token
    }

    return headers


def login(session, username, password, class_name=None):
    """
    Login on coursera.org with the given credentials.

    This adds the following cookies to the session:
        sessionid, maestro_login, maestro_login_flag
    """

    logging.debug('Initiating login.')
    try:
        session.cookies.clear('.coursera.org')
        logging.debug('Cleared .coursera.org cookies.')
    except KeyError:
        logging.debug('There were no .coursera.org cookies to be cleared.')

    # Hit class url
    if class_name is not None:
        class_url = CLASS_URL.format(class_name=class_name)
        r = requests.get(class_url, allow_redirects=False)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(e)
            raise ClassNotFound(class_name)

    headers = prepare_auth_headers(session, include_cauth=False)

    data = {
        'email': username,
        'password': password,
        'webrequest': 'true'
    }

    # Auth API V3
    r = session.post(AUTH_URL_V3, data=data,
                     headers=headers, allow_redirects=False)
    try:
        r.raise_for_status()

        # Some how the order of cookies parameters are important
        # for coursera!!!
        v = session.cookies.pop('CAUTH')
        session.cookies.set('CAUTH', v)
    except requests.exceptions.HTTPError as e:
        raise AuthenticationFailed('Cannot login on coursera.org: %s' % e)

    logging.info('Logged in on coursera.org.')


def down_the_wabbit_hole(session, class_name):
    """
    Authenticate on class.coursera.org
    """

    auth_redirector_url = AUTH_REDIRECT_URL.format(class_name=class_name)
    r = session.get(auth_redirector_url)

    logging.debug('Following %s to authenticate on class.coursera.org.',
                  auth_redirector_url)

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise AuthenticationFailed(
            'Cannot login on class.coursera.org: %s' % e)

    logging.debug('Exiting "deep" authentication.')


def get_authentication_cookies(session, class_name, username, password):
    """
    Get the necessary cookies to authenticate on class.coursera.org.

    To access the class pages we need two cookies on class.coursera.org:
        csrf_token, session
    """

    # First, check if we already have the .coursera.org cookies.
    if session.cookies.get('CAUTH', domain=".coursera.org"):
        logging.debug('Already logged in on accounts.coursera.org.')
    else:
        login(session, username, password, class_name=class_name)

    try:
        session.cookies.clear('class.coursera.org', '/' + class_name)
    except KeyError:
        pass

    down_the_wabbit_hole(session, class_name)

    enough = do_we_have_enough_cookies(session.cookies, class_name)

    if not enough:
        raise AuthenticationFailed('Did not find necessary cookies.')

    logging.info('Found authentication cookies.')


def do_we_have_enough_cookies(cj, class_name):
    """
    Check whether we have all the required cookies
    to authenticate on class.coursera.org.
    """
    domain = 'class.coursera.org'
    path = "/" + class_name

    return cj.get('csrf_token', domain=domain, path=path) is not None


def validate_cookies(session, class_name):
    """
    Checks whether we have all the required cookies
    to authenticate on class.coursera.org. Also check for and remove
    stale session.
    """
    if not do_we_have_enough_cookies(session.cookies, class_name):
        return False

    url = CLASS_URL.format(class_name=class_name) + '/class'
    r = session.head(url, allow_redirects=False)

    if r.status_code == 200:
        return True
    else:
        logging.debug('Stale session.')
        try:
            session.cookies.clear('.coursera.org')
        except KeyError:
            pass
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
    .coursera.org and class.coursera.org found in the given cookies_file.
    """

    path = "/" + class_name

    def cookies_filter(c):
        return c.domain == ".coursera.org" \
            or (c.domain == "class.coursera.org" and c.path == path)

    cj = get_cookie_jar(cookies_file)

    new_cj = requests.cookies.RequestsCookieJar()
    for c in filter(cookies_filter, cj):
        new_cj.set_cookie(c)

    return new_cj


def load_cookies_file(cookies_file):
    """
    Load cookies file.

    We pre-pend the file with the special Netscape header because the cookie
    loader is very particular about this string.
    """

    logging.debug('Loading cookie file %s into memory.', cookies_file)

    cookies = StringIO()
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

    logging.debug('Trying to get cookies from the cache.')

    path = get_cookies_cache_path(username)
    cj = requests.cookies.RequestsCookieJar()
    try:
        cached_cj = get_cookie_jar(path)
        for cookie in cached_cj:
            cj.set_cookie(cookie)
        logging.debug(
            'Loaded cookies from %s', get_cookies_cache_path(username))
    except IOError:
        logging.debug('Could not load cookies from the cache.')

    return cj


def write_cookies_to_cache(cj, username):
    """
    Save RequestsCookieJar to disk in Mozilla's cookies.txt file format.

    This prevents us from repeated authentications on the
    accounts.coursera.org and class.coursera.org/class_name sites.
    """
    mkdir_p(PATH_COOKIES, 0o700)
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
    because this is intended for debugging purposes or if the coursera
    authentication process has changed.
    """
    if cookies_file:
        cookies = find_cookies_for_class(cookies_file, class_name)
        session.cookies.update(cookies)
        logging.info('Loaded cookies from %s', cookies_file)
    else:
        cookies = get_cookies_from_cache(username)
        session.cookies.update(cookies)
        if validate_cookies(session, class_name):
            logging.info('Already authenticated.')
        else:
            get_authentication_cookies(session, class_name, username, password)
            write_cookies_to_cache(session.cookies, username)


class TLSAdapter(HTTPAdapter):
    """
    A customized HTTP Adapter which uses TLS v1.2 for encrypted
    connections.
    """

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1_2)
