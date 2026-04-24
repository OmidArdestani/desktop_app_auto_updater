#include "auto_updater/HttpDownloader.h"

#include <QCryptographicHash>
#include <QDir>
#include <QEventLoop>
#include <QFile>
#include <QFileInfo>
#include <QLoggingCategory>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QTimer>
#include <QUrl>

Q_LOGGING_CATEGORY(lcDownloader, "auto_updater.downloader")

namespace AutoUpdater {

HttpDownloader::HttpDownloader(int timeoutMs)
    : m_timeoutMs(timeoutMs)
{}

bool HttpDownloader::download(const QString   &url,
                              const QString   &destination,
                              const QString   &expectedChecksum,
                              ProgressCallback progressCallback)
{
    qCInfo(lcDownloader) << "Downloading" << url << "→" << destination;

    // Ensure destination directory exists
    const QFileInfo destInfo(destination);
    QDir().mkpath(destInfo.absolutePath());

    QFile file(destination);
    if (!file.open(QIODevice::WriteOnly)) {
        qCWarning(lcDownloader) << "Cannot open file for writing:" << destination;
        return false;
    }

    QNetworkAccessManager manager;
    QNetworkReply *reply = manager.get(QNetworkRequest{QUrl(url)});

    QCryptographicHash hash(QCryptographicHash::Sha256);

    // Stream data as it arrives to avoid buffering the entire file in memory
    QObject::connect(reply, &QNetworkReply::readyRead, [&]() {
        const QByteArray chunk = reply->readAll();
        file.write(chunk);
        hash.addData(chunk);
    });

    if (progressCallback) {
        QObject::connect(reply, &QNetworkReply::downloadProgress,
                         [&progressCallback](qint64 received, qint64 total) {
                             progressCallback(received, total);
                         });
    }

    QEventLoop loop;
    QTimer timer;
    timer.setSingleShot(true);
    timer.setInterval(m_timeoutMs);

    QObject::connect(reply,  &QNetworkReply::finished, &loop, &QEventLoop::quit);
    QObject::connect(&timer, &QTimer::timeout,         &loop, &QEventLoop::quit);
    timer.start();
    loop.exec();

    file.close();

    const bool timedOut = !timer.isActive();
    timer.stop();

    if (timedOut) {
        qCWarning(lcDownloader) << "Download timed out.";
        reply->deleteLater();
        cleanup(destination);
        return false;
    }

    if (reply->error() != QNetworkReply::NoError) {
        qCWarning(lcDownloader) << "Download failed:" << reply->errorString();
        reply->deleteLater();
        cleanup(destination);
        return false;
    }
    reply->deleteLater();

    if (!expectedChecksum.isEmpty()) {
        const QString actual = QString::fromLatin1(hash.result().toHex());
        if (actual.compare(expectedChecksum, Qt::CaseInsensitive) != 0) {
            qCWarning(lcDownloader)
                << "Checksum mismatch: expected" << expectedChecksum << "got" << actual;
            cleanup(destination);
            return false;
        }
        qCDebug(lcDownloader) << "Checksum verified:" << actual;
    }

    qCInfo(lcDownloader) << "Download complete:" << destination;
    return true;
}

void HttpDownloader::cleanup(const QString &path)
{
    if (QFile::exists(path))
        QFile::remove(path);
}

} // namespace AutoUpdater
