#pragma once

#include "IDownloader.h"

namespace AutoUpdater {

/**
 * @brief Downloads a file over HTTP/HTTPS using Qt's networking stack with
 *        streaming and optional SHA-256 checksum verification.
 *
 * Mirrors the Python HttpDownloader class exactly.
 *
 * Internally uses QNetworkAccessManager with QEventLoop to expose a
 * synchronous API consistent with the Python implementation.
 *
 * @param timeoutMs  Connection/read timeout in milliseconds. Defaults to
 *                   30 000.
 */
class HttpDownloader : public IDownloader
{
public:
    explicit HttpDownloader(int timeoutMs = 30000);

    bool download(const QString   &url,
                  const QString   &destination,
                  const QString   &expectedChecksum = {},
                  ProgressCallback progressCallback  = nullptr) override;

private:
    int m_timeoutMs;

    static void cleanup(const QString &path);
};

} // namespace AutoUpdater
