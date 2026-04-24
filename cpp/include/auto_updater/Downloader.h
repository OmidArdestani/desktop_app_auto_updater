#pragma once

#include <functional>
#include <QString>
#include <QtGlobal>

namespace AutoUpdater {

/**
 * @brief Optional callback type forwarded to the downloader for progress
 *        reporting.
 *
 * Receives (bytesReceived, bytesTotal).  bytesTotal may be -1 when the
 * server does not advertise Content-Length.
 *
 * Mirrors the Python ProgressCallback type alias exactly.
 */
using ProgressCallback = std::function<void(qint64 bytesReceived, qint64 bytesTotal)>;

/**
 * @brief Abstract interface for download strategies.
 *
 * Mirrors the Python IDownloader ABC exactly.
 */
class IDownloader
{
public:
    virtual ~IDownloader() = default;

    /**
     * @brief Download @p url to @p destination.
     *
     * @param url               Remote resource to download.
     * @param destination       Absolute path where the file should be saved.
     * @param expectedChecksum  Optional SHA-256 hex digest.  When non-empty
     *                          the downloaded file is verified and the method
     *                          returns false on mismatch.
     * @param progressCallback  Optional callable forwarded with download
     *                          progress information.
     * @return true   on success.
     * @return false  on any failure (network, checksum, I/O).
     */
    virtual bool download(const QString        &url,
                          const QString        &destination,
                          const QString        &expectedChecksum  = {},
                          ProgressCallback      progressCallback  = nullptr) = 0;
};


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
