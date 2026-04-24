"""
Tests for auto_updater.downloader — mirrors tst_AutoUpdater.cpp downloader
related tests.
"""

import hashlib
import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

from auto_updater.downloader import HttpDownloader


def _make_mock_response(content: bytes = b"installer_data") -> MagicMock:
    """Return a fake streaming requests.Response."""
    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.raise_for_status.return_value = None
    mock_response.headers = {"Content-Length": str(len(content))}
    mock_response.iter_content.return_value = [content]
    return mock_response


class TestHttpDownloader:
    @patch("auto_updater.downloader.requests.get")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_download_success(self, mock_makedirs, mock_file, mock_get):
        mock_get.return_value = _make_mock_response()
        result = HttpDownloader().download("https://example.com/app.exe", "/tmp/app.exe")
        assert result is True

    @patch("auto_updater.downloader.requests.get")
    def test_download_failure_on_exception(self, mock_get):
        mock_get.side_effect = Exception("Connection refused")
        result = HttpDownloader().download("https://example.com/app.exe", "/tmp/app.exe")
        assert result is False

    @patch("auto_updater.downloader.requests.get")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_valid_checksum_returns_true(self, mock_makedirs, mock_file, mock_get):
        content = b"installer_data"
        checksum = hashlib.sha256(content).hexdigest()
        mock_get.return_value = _make_mock_response(content=content)
        result = HttpDownloader().download(
            "https://example.com/app.exe", "/tmp/app.exe",
            expected_checksum=checksum,
        )
        assert result is True

    @patch("auto_updater.downloader.requests.get")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    @patch("os.path.exists", return_value=True)
    @patch("os.remove")
    def test_invalid_checksum_returns_false(
        self, mock_remove, mock_exists, mock_makedirs, mock_file, mock_get
    ):
        mock_get.return_value = _make_mock_response()
        result = HttpDownloader().download(
            "https://example.com/app.exe", "/tmp/app.exe",
            expected_checksum="000000deadbeef",
        )
        assert result is False

    @patch("auto_updater.downloader.requests.get")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_progress_callback_is_called(self, mock_makedirs, mock_file, mock_get):
        mock_get.return_value = _make_mock_response()
        calls = []
        HttpDownloader().download(
            "https://example.com/app.exe", "/tmp/app.exe",
            progress_callback=lambda recv, total: calls.append((recv, total)),
        )
        assert len(calls) > 0

    @patch("auto_updater.downloader.requests.get")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_no_checksum_skips_verification(self, mock_makedirs, mock_file, mock_get):
        """When expected_checksum is empty, the download succeeds without checking."""
        mock_get.return_value = _make_mock_response()
        result = HttpDownloader().download(
            "https://example.com/app.exe", "/tmp/app.exe",
            expected_checksum="",
        )
        assert result is True
