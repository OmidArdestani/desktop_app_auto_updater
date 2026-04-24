"""
downloader.py
-------------
Abstractions and implementations for downloading an installer from a URL to a
local file, with optional SHA-256 checksum verification and progress reporting.
"""

import abc
import hashlib
import logging
import os
from typing import Callable, Optional

import requests

logger = logging.getLogger(__name__)

# Type alias for an optional progress callback.
# Receives (bytes_downloaded, total_bytes) where total_bytes may be -1 when
# the server does not advertise Content-Length.
ProgressCallback = Callable[[int, int], None]


class IDownloader(abc.ABC):
    """Abstract base class for download strategies."""

    @abc.abstractmethod
    def download(
        self,
        url: str,
        destination: str,
        expected_checksum: str = "",
        progress_callback: Optional[ProgressCallback] = None,
    ) -> bool:
        """Download *url* to *destination*.

        Parameters
        ----------
        url:
            Remote resource to download.
        destination:
            Absolute path where the file should be saved.
        expected_checksum:
            Optional SHA-256 hex digest.  When non-empty the downloaded file
            is verified against this value and the method returns *False* on
            mismatch.
        progress_callback:
            Optional callable receiving ``(bytes_downloaded, total_bytes)``.

        Returns
        -------
        bool
            *True* on success, *False* on any failure.
        """


class HttpDownloader(IDownloader):
    """Downloads a file over HTTP/HTTPS using *requests* with streaming.

    Parameters
    ----------
    chunk_size:
        Number of bytes per streaming chunk.  Defaults to 8 KiB.
    timeout:
        Connection / read timeout in seconds.  Defaults to ``30``.
    """

    def __init__(self, chunk_size: int = 8192, timeout: int = 30) -> None:
        self._chunk_size = chunk_size
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def download(
        self,
        url: str,
        destination: str,
        expected_checksum: str = "",
        progress_callback: Optional[ProgressCallback] = None,
    ) -> bool:
        logger.info("Downloading %s → %s", url, destination)
        try:
            return self._stream_to_file(url, destination, expected_checksum, progress_callback)
        except Exception as exc:
            logger.error("Download failed: %s", exc)
            self._cleanup(destination)
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _stream_to_file(
        self,
        url: str,
        destination: str,
        expected_checksum: str,
        progress_callback: Optional[ProgressCallback],
    ) -> bool:
        os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)

        with requests.get(url, stream=True, timeout=self._timeout) as response:
            response.raise_for_status()
            total = int(response.headers.get("Content-Length", -1))
            downloaded = 0
            sha256 = hashlib.sha256()

            with open(destination, "wb") as fh:
                for chunk in response.iter_content(chunk_size=self._chunk_size):
                    if not chunk:
                        continue
                    fh.write(chunk)
                    sha256.update(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total)

        if expected_checksum:
            actual = sha256.hexdigest()
            if actual != expected_checksum.lower():
                logger.error(
                    "Checksum mismatch: expected %s, got %s",
                    expected_checksum,
                    actual,
                )
                self._cleanup(destination)
                return False
            logger.debug("Checksum verified: %s", actual)

        logger.info("Download complete: %s", destination)
        return True

    @staticmethod
    def _cleanup(path: str) -> None:
        """Remove a partially-downloaded file, ignoring errors."""
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass
