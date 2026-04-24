"""
auto_updater
============
Desktop application auto-updater library.

Public surface
--------------
>>> from auto_updater import AutoUpdater, create_default_updater, UpdateStatus
>>> from auto_updater import UpdateInfo
>>> from auto_updater import IVersionChecker, HttpVersionChecker
>>> from auto_updater import IDownloader, HttpDownloader
>>> from auto_updater import IInstaller, create_platform_installer
"""

from .update_info import UpdateInfo
from .version_checker import IVersionChecker, HttpVersionChecker
from .downloader import IDownloader, HttpDownloader
from .installer import IInstaller, create_platform_installer
from .updater import AutoUpdater, UpdateStatus, create_default_updater

__all__ = [
    "UpdateInfo",
    "IVersionChecker",
    "HttpVersionChecker",
    "IDownloader",
    "HttpDownloader",
    "IInstaller",
    "create_platform_installer",
    "AutoUpdater",
    "UpdateStatus",
    "create_default_updater",
]
