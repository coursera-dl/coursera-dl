import logging
import os
import subprocess


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

