"""
update_info.py
--------------
Data class that holds the metadata describing a single available update.
This object is produced by a version-checker and consumed by the downloader
and the orchestrating AutoUpdater.
"""

from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse
import json


@dataclass
class UpdateInfo:
    """Describes an available application update.

    Attributes
    ----------
    version : str
        Semantic version string of the new release, e.g. ``"2.1.0"``.
    download_url : str
        Full URL (HTTP/HTTPS or ``file://`` path) from which the installer
        can be fetched.
    checksum : str
        Expected SHA-256 hex digest of the downloaded file, used for
        integrity verification.  An empty string disables the check.
    release_notes : str
        Human-readable description of what changed in this release.
    mandatory : bool
        When *True* the update must be applied; the application should not
        allow users to skip or postpone it.
    file_name : str
        Suggested local file name for the downloaded installer.  Defaults to
        the last segment of *download_url* when not explicitly provided.
    """

    version: str
    download_url: str
    checksum: str = ""
    release_notes: str = ""
    mandatory: bool = False
    file_name: str = field(default="")

    def __init__(self, content):
        json_content = json.loads(content) if isinstance(content, str) else content

        self.version       = json_content.get("version", "")
        self.download_url  = json_content.get("download_url", "")
        self.checksum      = json_content.get("checksum", "")
        self.release_notes = json_content.get("release_notes", "")
        self.mandatory     = json_content.get("mandatory", False)
        self.file_name     = json_content.get("file_name", "")

    def __post_init__(self) -> None:
        if not self.file_name:
            # Use urlparse for correct path/query separation
            path = urlparse(self.download_url).path.rstrip("/")
            name = path.split("/")[-1] if path else ""
            self.file_name = name or "installer"
