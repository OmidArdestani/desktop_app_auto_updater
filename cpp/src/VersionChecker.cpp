#include "auto_updater/VersionChecker.h"

#include <QEventLoop>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLoggingCategory>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QTimer>
#include <QUrl>
#include <QVersionNumber>

Q_LOGGING_CATEGORY(lcVersionChecker, "auto_updater.version_checker")

namespace AutoUpdater {

HttpVersionChecker::HttpVersionChecker(const QString &manifestUrl, int timeoutMs)
    : m_manifestUrl(manifestUrl)
    , m_timeoutMs(timeoutMs)
{}

std::optional<UpdateInfo> HttpVersionChecker::checkForUpdate(const QString &currentVersion)
{
    QNetworkAccessManager manager;
    QNetworkRequest request{QUrl(m_manifestUrl)};

    QEventLoop loop;
    QTimer timer;
    timer.setSingleShot(true);
    timer.setInterval(m_timeoutMs);

    QNetworkReply *reply = manager.get(request);
    QObject::connect(reply,   &QNetworkReply::finished, &loop, &QEventLoop::quit);
    QObject::connect(&timer,  &QTimer::timeout,         &loop, &QEventLoop::quit);
    timer.start();
    loop.exec();

    // Did we time out before the reply finished?
    if (!timer.isActive()) {
        qCWarning(lcVersionChecker) << "Version manifest request timed out.";
        reply->deleteLater();
        return std::nullopt;
    }
    timer.stop();

    if (reply->error() != QNetworkReply::NoError) {
        qCWarning(lcVersionChecker) << "Failed to fetch version manifest:"
                                    << reply->errorString();
        reply->deleteLater();
        return std::nullopt;
    }

    const QByteArray data = reply->readAll();
    reply->deleteLater();

    QJsonParseError parseError;
    const QJsonDocument doc = QJsonDocument::fromJson(data, &parseError);
    if (parseError.error != QJsonParseError::NoError) {
        qCWarning(lcVersionChecker) << "Failed to parse version manifest:"
                                    << parseError.errorString();
        return std::nullopt;
    }

    const QJsonObject obj = doc.object();
    const QString latestVersion = obj.value(QStringLiteral("version")).toString();
    const QString downloadUrl   = obj.value(QStringLiteral("download_url")).toString();

    if (latestVersion.isEmpty() || downloadUrl.isEmpty()) {
        qCWarning(lcVersionChecker)
            << "Manifest is missing required fields 'version' or 'download_url'.";
        return std::nullopt;
    }

    const QVersionNumber current = QVersionNumber::fromString(currentVersion);
    const QVersionNumber latest  = QVersionNumber::fromString(latestVersion);

    if (latest <= current) {
        qCInfo(lcVersionChecker)
            << "Application is up to date (current=" << currentVersion
            << ", latest=" << latestVersion << ").";
        return std::nullopt;
    }

    qCInfo(lcVersionChecker) << "Update available:" << currentVersion << "→" << latestVersion;

    UpdateInfo info;
    info.version      = latestVersion;
    info.downloadUrl  = downloadUrl;
    info.checksum     = obj.value(QStringLiteral("checksum")).toString();
    info.releaseNotes = obj.value(QStringLiteral("release_notes")).toString();
    info.mandatory    = obj.value(QStringLiteral("mandatory")).toBool(false);
    info.fileName     = obj.value(QStringLiteral("file_name")).toString();

    if (info.fileName.isEmpty()) {
        info.fileName = QUrl(downloadUrl).fileName();
        if (info.fileName.isEmpty())
            info.fileName = QStringLiteral("installer");
    }

    return info;
}

} // namespace AutoUpdater
