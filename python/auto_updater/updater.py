"""
updater.py
----------
The :class:`AutoUpdater` class is the public façade that orchestrates the
full update lifecycle:

1. Ask the :class:`~auto_updater.version_checker.IVersionChecker` whether a
   new version exists.
2. Download the installer via :class:`~auto_updater.downloader.IDownloader`.
3. Launch the installer via :class:`~auto_updater.installer.IInstaller`.

The caller is responsible for wiring up concrete implementations or can use
the high-level :func:`create_default_updater` factory, which selects sensible
defaults for the current platform.
"""

import logging
import os
import tempfile
from enum import Enum, auto
from typing import Callable, Optional

from .downloader import HttpDownloader, IDownloader
from .installer import IInstaller, create_platform_installer
from .update_info import UpdateInfo
from .version_checker import HttpVersionChecker, IVersionChecker

logger = logging.getLogger(__name__)


class UpdateStatus(Enum):
    """High-level outcome of a single :meth:`AutoUpdater.check_and_update` call."""

    UP_TO_DATE = auto()
    """The installed version is already the latest."""

    UPDATE_AVAILABLE = auto()
    """A newer version was found but installation was not attempted
    (e.g. ``auto_install=False``)."""

    UPDATE_INSTALLED = auto()
    """The update was downloaded and successfully installed."""

    CHECK_FAILED = auto()
    """The version manifest could not be fetched or parsed."""

    DOWNLOAD_FAILED = auto()
    """The installer could not be downloaded."""

    INSTALL_FAILED = auto()
    """The installer was downloaded but exited with an error."""


class AutoUpdater:
    """Orchestrates version checking, downloading, and installing updates.

    Parameters
    ----------
    version_checker:
        Strategy used to detect available updates.
    downloader:
        Strategy used to fetch the installer binary.
    installer:
        Strategy used to execute the installer.
    download_dir:
        Directory where installers are saved.  Defaults to the system's
        temporary directory.
    """

    def __init__(
        self,
        version_checker: IVersionChecker,
        downloader: IDownloader,
        installer: IInstaller,
        download_dir: Optional[str] = None,
    ) -> None:
        self._checker = version_checker
        self._downloader = downloader
        self._installer = installer
        self._download_dir = download_dir or tempfile.gettempdir()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_and_update(
        self,
        current_version: str,
        auto_install: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> UpdateStatus:
        """Run the full update flow.

        Parameters
        ----------
        current_version:
            Version string of the currently installed application.
        auto_install:
            When *True* (default), automatically download and install if an
            update is found.  When *False*, return
            :attr:`UpdateStatus.UPDATE_AVAILABLE` without downloading.
        progress_callback:
            Optional callable forwarded to the downloader, receiving
            ``(bytes_downloaded, total_bytes)``.

        Returns
        -------
        UpdateStatus
            Describes the final outcome of the update attempt.
        """
        logger.info("Checking for updates (current version: %s) …", current_version)

        update_info = self._checker.check_for_update(current_version)
        if update_info is None or update_info.version == current_version:
            return UpdateStatus.CHECK_FAILED if self._check_was_error() else UpdateStatus.UP_TO_DATE

        if not auto_install:
            logger.info("Update available: %s (auto-install disabled).", update_info.version)
            return UpdateStatus.UPDATE_AVAILABLE

        return self._download_and_install(update_info, progress_callback)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _check_was_error(self) -> bool:
        # The checker already logged the reason; we rely on its return value.
        return False

    def _download_and_install(
        self,
        update_info: UpdateInfo,
        progress_callback: Optional[Callable[[int, int], None]],
    ) -> UpdateStatus:
        destination = os.path.join(self._download_dir, update_info.file_name)

        logger.info("Downloading update %s …", update_info.version)
        success = self._downloader.download(
            url=update_info.download_url,
            destination=destination,
            expected_checksum=update_info.checksum,
            progress_callback=progress_callback,
        )
        if not success:
            return UpdateStatus.DOWNLOAD_FAILED

        logger.info("Installing update %s …", update_info.version)
        if not self._installer.install(destination):
            return UpdateStatus.INSTALL_FAILED

        logger.info("Update %s installed successfully.", update_info.version)
        return UpdateStatus.UPDATE_INSTALLED


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def create_default_updater(
    manifest_url: str,
    download_dir: Optional[str] = None,
) -> AutoUpdater:
    """Build an :class:`AutoUpdater` wired with platform-appropriate defaults.

    Parameters
    ----------
    manifest_url:
        URL of the JSON version manifest.
    download_dir:
        Directory for downloaded installers.  Defaults to the system's
        temporary directory.

    Returns
    -------
    AutoUpdater
        Ready-to-use updater instance.
    """
    return AutoUpdater(
        version_checker=HttpVersionChecker(manifest_url),
        downloader=HttpDownloader(),
        installer=create_platform_installer(),
        download_dir=download_dir,
    )
