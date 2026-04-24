#include "auto_updater/Downloader.h"

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

// ---------------------------------------------------
// ---------------------HttpDownloader----------------
// ---------------------------------------------------
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

// ---------------------------------------------------
// -----------------LocalStorageDownloader------------
// ---------------------------------------------------
bool LocalStorageDownloader::download(const QString& source,
                                      const QString& destination,
                                      const QString& expectedChecksum,
                                      ProgressCallback progressCallback)
{
    QFile src(source);
    if (!src.open(QIODevice::ReadOnly)) {
        qCWarning(lcDownloader) << "Cannot open source:" << source;
        return false;
    }

    QFile dst(destination);
    if (!dst.open(QIODevice::WriteOnly)) {
        qCWarning(lcDownloader) << "Cannot open destination:" << destination;
        return false;
    }

    const qint64 totalSize = src.size();
    qint64 copied = 0;

    QCryptographicHash hash(QCryptographicHash::Sha256);

    const qint64 bufferSize = 1024 * 1024; // 1 MB chunks
    QByteArray buffer;
    buffer.resize(bufferSize);

    while (!src.atEnd()) {
        const qint64 read = src.read(buffer.data(), bufferSize);
        if (read <= 0)
            break;

        dst.write(buffer.constData(), read);
        hash.addData(buffer.constData(), read);

        copied += read;

        if (progressCallback)
            progressCallback(copied, totalSize);
    }

    src.close();
    dst.close();

    if (!expectedChecksum.isEmpty()) {
        const QString actual = QString::fromLatin1(hash.result().toHex());
        if (actual.compare(expectedChecksum, Qt::CaseInsensitive) != 0) {
            qCWarning(lcDownloader)
                << "Checksum mismatch: expected" << expectedChecksum << "got" << actual;
            cleanup(destination);
            return false;
        }
    }

    qCInfo(lcDownloader) << "Local copy complete:" << destination;
    return true;
}

void LocalStorageDownloader::cleanup(const QString &path)
{
    if (QFile::exists(path))
        QFile::remove(path);
}
} // namespace AutoUpdater
