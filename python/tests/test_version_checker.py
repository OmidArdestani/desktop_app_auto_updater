"""
Tests for auto_updater.version_checker — mirrors tst_AutoUpdater.cpp
HttpVersionChecker tests.
"""

from unittest.mock import MagicMock, patch

import pytest

from auto_updater.version_checker import HttpVersionChecker


def _mock_response(data: dict) -> MagicMock:
    """Build a fake requests.Response whose .json() returns *data*."""
    resp = MagicMock()
    resp.json.return_value = data
    resp.raise_for_status.return_value = None
    return resp


class TestHttpVersionChecker:
    """Mirrors C++ tst_AutoUpdater version-checker related tests."""

    @patch("auto_updater.version_checker.requests.get")
    def test_returns_update_when_newer_version(self, mock_get):
        mock_get.return_value = _mock_response({
            "version": "2.0.0",
            "download_url": "https://example.com/app-2.0.0.exe",
        })
        checker = HttpVersionChecker("https://example.com/version.json")
        result = checker.check_for_update("1.0.0")
        assert result is not None
        assert result.version == "2.0.0"
        assert result.download_url == "https://example.com/app-2.0.0.exe"

    @patch("auto_updater.version_checker.requests.get")
    def test_returns_none_when_up_to_date(self, mock_get):
        mock_get.return_value = _mock_response({
            "version": "1.0.0",
            "download_url": "https://example.com/app-1.0.0.exe",
        })
        checker = HttpVersionChecker("https://example.com/version.json")
        result = checker.check_for_update("1.0.0")
        assert result is None

    @patch("auto_updater.version_checker.requests.get")
    def test_returns_none_when_older_than_current(self, mock_get):
        mock_get.return_value = _mock_response({
            "version": "0.9.0",
            "download_url": "https://example.com/app-0.9.0.exe",
        })
        checker = HttpVersionChecker("https://example.com/version.json")
        result = checker.check_for_update("1.0.0")
        assert result is None

    @patch("auto_updater.version_checker.requests.get")
    def test_returns_none_on_network_error(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        checker = HttpVersionChecker("https://example.com/version.json")
        result = checker.check_for_update("1.0.0")
        assert result is None

    @patch("auto_updater.version_checker.requests.get")
    def test_optional_fields_have_defaults(self, mock_get):
        mock_get.return_value = _mock_response({
            "version": "2.0.0",
            "download_url": "https://example.com/app-2.0.0.exe",
        })
        checker = HttpVersionChecker("https://example.com/version.json")
        result = checker.check_for_update("1.0.0")
        assert result is not None
        assert result.checksum == ""
        assert result.release_notes == ""
        assert result.mandatory is False

    @patch("auto_updater.version_checker.requests.get")
    def test_all_manifest_fields_populated(self, mock_get):
        mock_get.return_value = _mock_response({
            "version": "3.0.0",
            "download_url": "https://example.com/app-3.0.0.exe",
            "checksum": "abc123",
            "release_notes": "New features",
            "mandatory": True,
            "file_name": "app-3.0.0.exe",
        })
        checker = HttpVersionChecker("https://example.com/version.json")
        result = checker.check_for_update("1.0.0")
        assert result is not None
        assert result.checksum == "abc123"
        assert result.release_notes == "New features"
        assert result.mandatory is True
        assert result.file_name == "app-3.0.0.exe"

    @patch("auto_updater.version_checker.requests.get")
    def test_returns_none_when_manifest_missing_version(self, mock_get):
        mock_get.return_value = _mock_response({
            "download_url": "https://example.com/app.exe",
        })
        checker = HttpVersionChecker("https://example.com/version.json")
        result = checker.check_for_update("1.0.0")
        assert result is None

    @patch("auto_updater.version_checker.requests.get")
    def test_returns_none_when_manifest_missing_download_url(self, mock_get):
        mock_get.return_value = _mock_response({"version": "2.0.0"})
        checker = HttpVersionChecker("https://example.com/version.json")
        result = checker.check_for_update("1.0.0")
        assert result is None

    @patch("auto_updater.version_checker.requests.get")
    def test_file_name_derived_from_url_when_not_in_manifest(self, mock_get):
        mock_get.return_value = _mock_response({
            "version": "2.0.0",
            "download_url": "https://example.com/releases/app-2.0.0.exe",
        })
        checker = HttpVersionChecker("https://example.com/version.json")
        result = checker.check_for_update("1.0.0")
        assert result is not None
        assert result.file_name == "app-2.0.0.exe"
