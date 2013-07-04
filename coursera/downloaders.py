from __future__ import print_function

import logging
import os
import requests
import subprocess
import sys
import time


class Downloader(object):
    """
    Base downloader class.

    Every subclass should implement the _start_download method.

    Usage::

      >>> import downloaders
      >>> d = downloaders.SubclassFromDownloader()
      >>> d.download('http://example.com', 'save/to/this/file')
    """

    def _start_download(self, url, filename):
        """
        Actual method to download the given url to the given file.
        This method should be implemented by the subclass.
        """
        raise NotImplementedError("Subclasses should implement this")

    def download(self, url, filename):
        """
        Download the given url to the given file. When the download
        is aborted by the user, the partially downloaded file is also removed.
        """

        try:
            self._start_download(url, filename)
        except KeyboardInterrupt as e:
            logging.info(
                'Keyboard Interrupt -- Removing partial file: %s', filename)
            try:
                os.remove(filename)
            except OSError:
                pass
            raise e


class ExternalDownloader(Downloader):
    """
    Downloads files with an extrnal downloader.

    We could possibly use python to stream files to disk,
    but this is slow compared to these external downloaders.

    :param session: Requests session.
    :param bin: External downloader binary.
    """

    # External downloader binary
    bin = None

    def __init__(self, session, bin=None):
        self.session = session
        self.bin = bin or self.__class__.bin

        if not self.bin:
            raise RuntimeError("No bin specified")

    def _prepare_cookies(self, command, url):
        """
        Extract cookies from the requests session and add them to the command
        """

        req = requests.models.Request()
        req.method = 'GET'
        req.url = url

        cookie_values = requests.cookies.get_cookie_header(
            self.session.cookies, req)

        if cookie_values:
            self._add_cookies(command, cookie_values)

    def _add_cookies(self, command, cookie_values):
        """
        Add the given cookie values to the command
        """

        raise RuntimeError("Subclasses should implement this")

    def _create_command(self, url, filename):
        """
        Create command to execute in a subprocess.
        """
        raise NotImplementedError("Subclasses should implement this")

    def _start_download(self, url, filename):
        command = self._create_command(url, filename)
        self._prepare_cookies(command, url)
        logging.debug('Executing %s: %s', self.bin, command)
        try:
            subprocess.call(command)
        except OSError as e:
            msg = "{0}. Are you sure that '{1}' is the right bin?".format(
                e, self.bin)
            raise OSError(msg)


class WgetDownloader(ExternalDownloader):
    """
    Uses wget, which is robust and gives nice visual feedback.
    """

    bin = 'wget'

    def _add_cookies(self, command, cookie_values):
        command.extend(['--header', "Cookie: " + cookie_values])

    def _create_command(self, url, filename):
        return [self.bin, url, '-O', filename, '--no-cookies',
                '--no-check-certificate']


class CurlDownloader(ExternalDownloader):
    """
    Uses curl, which is robust and gives nice visual feedback.
    """

    bin = 'curl'

    def _add_cookies(self, command, cookie_values):
        command.extend(['--cookie', cookie_values])

    def _create_command(self, url, filename):
        return [self.bin, url, '-k', '-#', '-L', '-o', filename]


class Aria2Downloader(ExternalDownloader):
    """
    Uses aria2. Unfortunately, it does not give a nice visual feedback, but
    gets the job done much faster than the alternatives.
    """

    bin = 'aria2c'

    def _add_cookies(self, command, cookie_values):
        command.extend(['--header', "Cookie: " + cookie_values])

    def _create_command(self, url, filename):
        return [self.bin, url, '-o', filename,
                '--check-certificate=false', '--log-level=notice',
                '--max-connection-per-server=4', '--min-split-size=1M']


class AxelDownloader(ExternalDownloader):
    """
    Uses axel, which is robust and it both gives nice
    visual feedback and get the job done fast.
    """

    bin = 'axel'

    def _add_cookies(self, command, cookie_values):
        command.extend(['-H', "Cookie: " + cookie_values])

    def _create_command(self, url, filename):
        return [self.bin, '-o', filename, '-n', '4', '-a', url]


class BandwidthCalc(object):
    """
    Class for calculation of bandwidth for the "native" downloader.
    """

    def __init__(self):
        self.nbytes = 0
        self.prev_time = time.time()
        self.prev_bw = 0
        self.prev_bw_length = 0

    def received(self, data_length):
        now = time.time()
        self.nbytes += data_length
        time_delta = now - self.prev_time

        if time_delta > 1:  # average over 1+ second
            bw = float(self.nbytes) / time_delta
            self.prev_bw = (self.prev_bw + 2 * bw) / 3
            self.nbytes = 0
            self.prev_time = now

    def __str__(self):
        if self.prev_bw == 0:
            bw = ''
        elif self.prev_bw < 1000:
            bw = ' (%dB/s)' % self.prev_bw
        elif self.prev_bw < 1000000:
            bw = ' (%.2fKB/s)' % (self.prev_bw / 1000)
        elif self.prev_bw < 1000000000:
            bw = ' (%.2fMB/s)' % (self.prev_bw / 1000000)
        else:
            bw = ' (%.2fGB/s)' % (self.prev_bw / 1000000000)

        length_diff = self.prev_bw_length - len(bw)
        self.prev_bw_length = len(bw)

        if length_diff > 0:
            return '%s%s' % (bw, length_diff * ' ')
        else:
            return bw


class NativeDownloader(Downloader):
    """
    'Native' python downloader -- slower than the external downloaders.

    :param session: Requests session.
    """

    def __init__(self, session):
        self.session = session

    def _start_download(self, url, filename):
        logging.info('Downloading %s -> %s', url, filename)

        attempts_count = 0
        error_msg = ''
        while attempts_count < 5:
            r = self.session.get(url, stream=True)

            if r.status_code is not 200:
                logging.warn(
                    'Probably the file is missing from the AWS repository...'
                    ' waiting.')

                if r.reason:
                    error_msg = r.reason + ' ' + str(r.status_code)
                else:
                    error_msg = 'HTTP Error ' + str(r.status_code)

                wait_interval = 2 ** (attempts_count + 1)
                msg = 'Error downloading, will retry in {0} seconds ...'
                print(msg.format(wait_interval))
                time.sleep(wait_interval)
                attempts_count += 1
                continue

            bw = BandwidthCalc()
            chunk_sz = 1048576
            bytesread = 0
            with open(filename, 'wb') as f:
                while True:
                    data = r.raw.read(chunk_sz)
                    if not data:
                        print('.')
                        break
                    bw.received(len(data))
                    f.write(data)
                    bytesread += len(data)
                    print('\r%d bytes read%s' % (bytesread, bw), end=' ')
                    sys.stdout.flush()
            r.close()
            return True

        if attempts_count == 5:
            logging.warn('Skipping, can\'t download file ...')
            logging.error(error_msg)
            return False


def get_downloader(session, class_name, args):
    """
    Decides which downloader to use.
    """

    external = {
        'wget': WgetDownloader,
        'curl': CurlDownloader,
        'aria2': Aria2Downloader,
        'axel': AxelDownloader,
    }

    for bin, class_ in list(external.items()):
        if getattr(args, bin):
            return class_(session, bin=getattr(args, bin))

    return NativeDownloader(session)
