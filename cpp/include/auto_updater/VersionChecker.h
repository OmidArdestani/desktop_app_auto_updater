#pragma once

#include "UpdateInfo.h"

#include <optional>
#include <QString>

namespace AutoUpdater {

/**
 * @brief Abstract interface for version-checking strategies.
 *
 * Mirrors the Python IVersionChecker ABC exactly.
 */
class IVersionChecker
{
public:
    virtual ~IVersionChecker() = default;

    /**
     * @brief Compare @p currentVersion against the latest available version.
     *
     * @param currentVersion  Version string of the currently installed app,
     *                        e.g. "1.0.0".
     * @return UpdateInfo     If a newer version is available.
     * @return std::nullopt   If the application is already up to date or the
     *                        check fails gracefully.
     */
    virtual std::optional<UpdateInfo> checkForUpdate(const QString &currentVersion) = 0;
};


/**
 * @brief Fetches a JSON version manifest from an HTTP/HTTPS URL and checks
 *        whether a newer version is available.
 *
 * Mirrors the Python HttpVersionChecker class exactly.
 *
 * Expected JSON manifest format:
 * @code{.json}
 * {
 *   "version":       "2.1.0",
 *   "download_url":  "https://example.com/releases/app-2.1.0-setup.exe",
 *   "checksum":      "e3b0c44298fc1c149afbf4c8996fb924...",
 *   "release_notes": "Bug fixes and performance improvements.",
 *   "mandatory":     false,
 *   "file_name":     "app-2.1.0-setup.exe"
 * }
 * @endcode
 *
 * Only "version" and "download_url" are required; all other fields are
 * optional and fall back to sensible defaults.
 *
 * Internally uses QNetworkAccessManager with a QEventLoop to provide a
 * synchronous API consistent with the Python implementation.
 *
 * @param manifestUrl  URL of the JSON manifest file.
 * @param timeoutMs    Request timeout in milliseconds. Defaults to 10 000.
 */
class HttpVersionChecker : public IVersionChecker
{
public:
    explicit HttpVersionChecker(const QString &manifestUrl, int timeoutMs = 10000);

    std::optional<UpdateInfo> checkForUpdate(const QString &currentVersion) override;

private:
    QString m_manifestUrl;
    int     m_timeoutMs;
};

} // namespace AutoUpdater
