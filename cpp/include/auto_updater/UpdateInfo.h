#pragma once

#include <QString>

namespace AutoUpdater {

/**
 * @brief Holds the metadata describing a single available update.
 *
 * Mirrors the Python UpdateInfo dataclass exactly.
 *
 * Fields
 * ------
 * version        - Semantic version string of the new release, e.g. "2.1.0".
 * downloadUrl    - Full URL (HTTP/HTTPS) from which the installer can be fetched.
 * checksum       - Expected SHA-256 hex digest of the downloaded file.
 *                  An empty string disables the integrity check.
 * releaseNotes   - Human-readable description of changes in this release.
 * mandatory      - When true the update must be applied; users cannot skip it.
 * fileName       - Suggested local file name for the downloaded installer.
 *                  Derived from the last segment of downloadUrl if empty.
 */
struct UpdateInfo
{
    QString version;
    QString downloadUrl;
    QString checksum;
    QString releaseNotes;
    bool    mandatory = false;
    QString fileName;
};

} // namespace AutoUpdater
