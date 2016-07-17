import abc
import logging
import traceback
from multiprocessing.dummy import Pool


class AbstractDownloader(object):
    """
    Base class for download wrappers. Two methods should be implemented:
    `download` and `join`.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, file_downloader):
        super(AbstractDownloader, self).__init__()
        self._file_downloader = file_downloader

    @abc.abstractmethod
    def download(self, *args, **kwargs):
        raise NotImplementedError()

    @abc.abstractmethod
    def join(self):
        raise NotImplementedError()

    def _download_wrapper(self, url, *args, **kwargs):
        """
        Actual download call. Calls the underlying file downloader,
        catches all exceptions and returns the result.
        """
        try:
            return url, self._file_downloader.download(url, *args, **kwargs)
        except Exception as e:
            logging.error("AbstractDownloader: %s", traceback.format_exc())
            return url, e


class ConsecutiveDownloader(AbstractDownloader):
    """
    This class calls underlying file downloader in a sequential order
    in the same thread where it was created.
    """
    def download(self, callback, url, *args, **kwargs):
        _, result = self._download_wrapper(url, *args, **kwargs)
        callback(url, result)
        return result

    def join(self):
        pass


class ParallelDownloader(AbstractDownloader):
    """
    This class uses threading.Pool to run download requests in parallel.
    """
    def __init__(self, file_downloader, processes=1):
        super(ParallelDownloader, self).__init__(file_downloader)
        self._pool = Pool(processes=processes)

    def download(self, callback, url, *args, **kwargs):
        callback_wrapper = lambda payload: callback(*payload)
        return self._pool.apply_async(
            self._download_wrapper, (url,) + args, kwargs,
            callback=callback_wrapper)

    def join(self):
        self._pool.close()
        self._pool.join()
