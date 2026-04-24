"""
Tests for auto_updater.update_info
"""

import pytest
from auto_updater.update_info import UpdateInfo


class TestUpdateInfo:
    def test_basic_creation(self):
        info = UpdateInfo(version="2.0.0", download_url="https://example.com/app-2.0.0.exe")
        assert info.version == "2.0.0"
        assert info.download_url == "https://example.com/app-2.0.0.exe"
        assert info.checksum == ""
        assert info.release_notes == ""
        assert info.mandatory is False

    def test_file_name_derived_from_url(self):
        info = UpdateInfo(version="2.0.0", download_url="https://example.com/releases/app-2.0.0.exe")
        assert info.file_name == "app-2.0.0.exe"

    def test_file_name_explicit(self):
        info = UpdateInfo(
            version="2.0.0",
            download_url="https://example.com/releases/app-2.0.0.exe",
            file_name="custom-name.exe",
        )
        assert info.file_name == "custom-name.exe"

    def test_file_name_url_with_query(self):
        # Query parameters are ignored; filename is taken from the URL path segment
        info = UpdateInfo(version="1.0.0", download_url="https://example.com/dl?file=app.exe")
        assert info.file_name == "dl"

    def test_file_name_bare_url_fallback(self):
        info = UpdateInfo(version="1.0.0", download_url="https://example.com/")
        assert info.file_name == "installer"

    def test_full_creation(self):
        info = UpdateInfo(
            version="3.0.0",
            download_url="https://example.com/app-3.0.0.exe",
            checksum="abc123",
            release_notes="New feature",
            mandatory=True,
            file_name="app-3.0.0.exe",
        )
        assert info.mandatory is True
        assert info.checksum == "abc123"
        assert info.release_notes == "New feature"
