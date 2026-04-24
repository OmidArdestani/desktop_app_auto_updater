"""
version_checker.py
------------------
Abstractions and implementations for querying a remote (or local-network)
version manifest to determine whether an update is available.

Expected JSON manifest format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: json

    {
        "version": "2.1.0",
        "download_url": "https://example.com/releases/app-2.1.0-setup.exe",
        "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "release_notes": "Bug fixes and performance improvements.",
        "mandatory": false,
        "file_name": "app-2.1.0-setup.exe"
    }

Only ``version`` and ``download_url`` are required; all other fields are
optional and fall back to sensible defaults.
"""

import abc
import logging
from typing import Optional

import requests
from packaging.version import Version

from .update_info import UpdateInfo

from PyQt5.QtCore import QUrl

logger = logging.getLogger(__name__)


class IVersionChecker(abc.ABC):
    """Abstract base class for version-checking strategies."""

    @abc.abstractmethod
    def check_for_update(self, current_version: str) -> Optional[UpdateInfo]:
        """Compare *current_version* against the latest available version.

        Parameters
        ----------
        current_version:
            The version string of the currently installed application,
            e.g. ``"1.0.0"``.

        Returns
        -------
        UpdateInfo
            If a newer version is available.
        None
            If the application is already up to date or the check fails
            gracefully.
        """

# ---------------------------------------------------
# -----------------HttpVersionChecker----------------
# ---------------------------------------------------
class HttpVersionChecker(IVersionChecker):
    """Fetches a JSON version manifest from an HTTP/HTTPS or file URL.

    Parameters
    ----------
    manifest_url:
        URL of the JSON manifest file, e.g.
        ``"https://example.com/version.json"`` or
        ``"http://192.168.1.100/updates/version.json"``.
    timeout:
        Request timeout in seconds.  Defaults to ``10``.
    """

    def __init__(self, manifest_url: str, timeout: int = 10) -> None:
        self._manifest_url = manifest_url
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_for_update(self, current_version: str) -> Optional[UpdateInfo]:
        """Fetch the manifest and return an :class:`UpdateInfo` when a newer
        version is available, otherwise return *None*."""
        try:
            manifest = self._fetch_manifest()
        except Exception as exc:
            logger.error("Failed to fetch version manifest: %s", exc)
            return None

        latest_version = manifest.get("version")
        download_url = manifest.get("download_url")

        if not latest_version or not download_url:
            logger.error("Manifest is missing required fields 'version' or 'download_url'.")
            return None

        if Version(latest_version) <= Version(current_version):
            logger.info(
                "Application is up to date (current=%s, latest=%s).",
                current_version,
                latest_version,
            )
            return None

        logger.info(
            "Update available: %s → %s",
            current_version,
            latest_version,
        )
        return UpdateInfo(
            version=latest_version,
            download_url=download_url,
            checksum=manifest.get("checksum", ""),
            release_notes=manifest.get("release_notes", ""),
            mandatory=manifest.get("mandatory", False),
            file_name=manifest.get("file_name", ""),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_manifest(self) -> dict:
        response = requests.get(self._manifest_url, timeout=self._timeout)
        response.raise_for_status()
        return response.json()


# ---------------------------------------------------
# -------------LocalStorageVersionChecker------------
# ---------------------------------------------------
class LocalStorageVersionChecker(IVersionChecker):
    """Reads a JSON version manifest from a local file path.

    Parameters
    ----------
    manifest_path:
        Path to the JSON manifest file, e.g. ``"/path/to/version.json"``.
    """

    def __init__(self, manifest_path: str) -> None:
        self._manifest_path = manifest_path

    def check_for_update(self, current_version: str) -> Optional[UpdateInfo]:
        """Read the manifest and return an :class:`UpdateInfo` when a newer
        version is available, otherwise return *None*."""
        try:
            local_path = self._manifest_path
            if self._manifest_path.startswith("file://"):
                local_path = QUrl(self._manifest_path).toLocalFile()

            with open(local_path, "r", encoding="utf-8") as fh:
                manifest = fh.read()

                return UpdateInfo(manifest)

        except Exception as exc:
            logger.error("Failed to read version manifest: %s", exc)
            return None