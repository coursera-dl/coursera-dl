import logging
import os
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

    :param cookies_dict: Python dict of name-value pairs of cookies.
    :param url: External downloader binary.
    """

    # External downloader binary
    bin = None

    def __init__(self, cookies_dict=None, bin=None):
        self.cookies_dict = cookies_dict or {}
        self.bin = bin or self.__class__.bin

        if not self.bin:
            raise RuntimeError("No bin specified")

    def cookie_values(self):
        """
        Makes a string of cookie keys and values.
        Can be used to set a Cookie header.
        """

        return '; '.join(k + '=' + v for (k, v) in self.cookies_dict.items())

    def _create_command(self, url, filename):
        """
        Create command to execute in a subprocess.
        """
        raise NotImplementedError("Subclasses should implement this")

    def _start_download(self, url, filename):
        command = self._create_command(url, filename)
        logging.debug('Executing %s: %s', self.bin, command)
        subprocess.call(command)


class WgetDownloader(ExternalDownloader):
    """
    Uses wget, which is robust and gives nice visual feedback.
    """

    bin = 'wget'

    def _create_command(self, url, filename):
        return [self.bin, url, '-O', filename, '--no-cookies', '--header',
                "Cookie: " + self.cookie_values(),
                '--no-check-certificate']


class CurlDownloader(ExternalDownloader):
    """
    Uses curl, which is robust and gives nice visual feedback.
    """

    bin = 'curl'

    def _create_command(self, url, filename):
        return [self.bin, url, '-k', '-#', '-L', '-o', filename,
                '--cookie', self.cookie_values()]


class Aria2Downloader(ExternalDownloader):
    """
    Uses aria2. Unfortunately, it does not give a nice
    visual feedback, bug gets the job done much faster than the
    alternatives.
    """

    bin = 'aria2'

    def _create_command(self, url, filename):
        return [self.bin, url, '-o', filename, '--header',
                "Cookie: " + self.cookie_values(),
                '--check-certificate=false', '--log-level=notice',
                '--max-connection-per-server=4', '--min-split-size=1M']


class AxelDownloader(ExternalDownloader):
    """
    Uses axel, which is robust and it both gives nice
    visual feedback and get the job done fast.
    """

    bin = 'axel'

    def _create_command(self, url, filename):
        return [self.bin, '-H', "Cookie: " + self.cookie_values(),
                '-o', filename, '-n', '4', '-a', url]


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
        while (attempts_count < 5):
            r = self.session.get(url, stream=True)

            if (r.status_code is not 200):
                logging.warn(
                    'Probably the file is missing from the AWS repository...'
                    ' waiting.')

                if r.reason:
                    error_msg = r.reason + ' ' + str(r.status_code)
                else:
                    error_msg = 'HTTP Error ' + str(r.status_code)

                wait_interval = 2 ** (attempts_count + 1)
                msg = 'Error to downloading, will retry in {0} seconds ...'
                print msg.format(wait_interval)
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
                        print '.'
                        break
                    bw.received(len(data))
                    f.write(data)
                    bytesread += len(data)
                    print '\r%d bytes read%s' % (bytesread, bw),
                    sys.stdout.flush()
            r.close()
            return True

        if attempts_count == 5:
            logging.warn('Skipping, can\'t download file ...')
            logging.error(error_msg)
            return False
