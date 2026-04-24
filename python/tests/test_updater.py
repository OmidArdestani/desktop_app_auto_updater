"""
Tests for auto_updater.updater — directly mirrors tst_AutoUpdater.cpp
AutoUpdater test slots.
"""

from unittest.mock import MagicMock

import pytest

from auto_updater.update_info import UpdateInfo
from auto_updater.updater import AutoUpdater, UpdateStatus


def _make_update_info() -> UpdateInfo:
    return UpdateInfo(version="2.0.0", download_url="https://example.com/app.exe")


def _make_updater(
    checker,
    downloader: MagicMock = None,
    installer: MagicMock = None,
) -> AutoUpdater:
    if downloader is None:
        downloader = MagicMock()
        downloader.download.return_value = True
    if installer is None:
        installer = MagicMock()
        installer.install.return_value = True
    return AutoUpdater(checker, downloader, installer, download_dir="/tmp")


class TestAutoUpdater:

    # --- Mirrors C++ test_upToDate ---
    def test_returns_up_to_date_when_no_update(self):
        checker = MagicMock()
        checker.check_for_update.return_value = None
        assert _make_updater(checker).check_and_update("1.0.0") == UpdateStatus.UP_TO_DATE

    # --- Mirrors C++ test_updateAvailableWhenAutoInstallDisabled ---
    def test_returns_update_available_when_auto_install_disabled(self):
        checker = MagicMock()
        checker.check_for_update.return_value = _make_update_info()
        result = _make_updater(checker).check_and_update("1.0.0", auto_install=False)
        assert result == UpdateStatus.UPDATE_AVAILABLE

    # --- Mirrors C++ test_updateInstalledOnSuccess ---
    def test_returns_update_installed_on_success(self):
        checker = MagicMock()
        checker.check_for_update.return_value = _make_update_info()
        downloader = MagicMock()
        downloader.download.return_value = True
        installer = MagicMock()
        installer.install.return_value = True
        result = _make_updater(checker, downloader, installer).check_and_update("1.0.0")
        assert result == UpdateStatus.UPDATE_INSTALLED

    # --- Mirrors C++ test_downloadFailed ---
    def test_returns_download_failed_when_download_errors(self):
        checker = MagicMock()
        checker.check_for_update.return_value = _make_update_info()
        downloader = MagicMock()
        downloader.download.return_value = False
        assert _make_updater(checker, downloader).check_and_update("1.0.0") == UpdateStatus.DOWNLOAD_FAILED

    # --- Mirrors C++ test_installFailed ---
    def test_returns_install_failed_when_installer_errors(self):
        checker = MagicMock()
        checker.check_for_update.return_value = _make_update_info()
        installer = MagicMock()
        installer.install.return_value = False
        assert _make_updater(checker, installer=installer).check_and_update("1.0.0") == UpdateStatus.INSTALL_FAILED

    # --- Mirrors C++ test_checkerCalledWithCurrentVersion ---
    def test_checker_called_with_current_version(self):
        checker = MagicMock()
        checker.check_for_update.return_value = None
        _make_updater(checker).check_and_update("1.5.0")
        checker.check_for_update.assert_called_once_with("1.5.0")

    # --- Mirrors C++ test_updateAvailableWhenAutoInstallDisabled (downloader not called) ---
    def test_downloader_not_called_when_auto_install_disabled(self):
        checker = MagicMock()
        checker.check_for_update.return_value = _make_update_info()
        downloader = MagicMock()
        _make_updater(checker, downloader).check_and_update("1.0.0", auto_install=False)
        downloader.download.assert_not_called()

    def test_progress_callback_forwarded_to_downloader(self):
        checker = MagicMock()
        checker.check_for_update.return_value = _make_update_info()
        downloader = MagicMock()
        downloader.download.return_value = True
        installer = MagicMock()
        installer.install.return_value = True
        callback = MagicMock()
        _make_updater(checker, downloader, installer).check_and_update(
            "1.0.0", progress_callback=callback
        )
        # Verify download was called; callback is passed as kwarg
        assert downloader.download.call_count == 1
        _, kwargs = downloader.download.call_args
        assert kwargs.get("progress_callback") is callback
