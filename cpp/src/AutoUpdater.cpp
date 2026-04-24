#include "auto_updater/AutoUpdater.h"
#include "auto_updater/VersionChecker.h"
#include "auto_updater/Downloader.h"
#include "auto_updater/Installer.h"

#include <QDir>
#include <QLoggingCategory>
#include <QStandardPaths>

Q_LOGGING_CATEGORY(lcAutoUpdater, "auto_updater")

namespace AutoUpdater {

AutoUpdater::AutoUpdater(std::unique_ptr<IVersionChecker> checker,
                         std::unique_ptr<IDownloader>     downloader,
                         std::unique_ptr<IInstaller>      installer,
                         const QString                   &downloadDir)
    : m_checker(std::move(checker))
    , m_downloader(std::move(downloader))
    , m_installer(std::move(installer))
    , m_downloadDir(downloadDir.isEmpty()
                        ? QStandardPaths::writableLocation(QStandardPaths::TempLocation)
                        : downloadDir)
{}

UpdateStatus AutoUpdater::checkAndUpdate(const QString   &currentVersion,
                                         bool             autoInstall,
                                         ProgressCallback progressCallback)
{
    qCInfo(lcAutoUpdater)
        << "Checking for updates (current version:" << currentVersion << ")…";

    const auto updateInfo = m_checker->checkForUpdate(currentVersion);
    if (!updateInfo.has_value() || updateInfo->version == currentVersion)
        return UpdateStatus::UpToDate;

    if (!autoInstall) {
        qCInfo(lcAutoUpdater)
            << "Update available:" << updateInfo->version << "(auto-install disabled).";
        return UpdateStatus::UpdateAvailable;
    }

    return downloadAndInstall(*updateInfo, progressCallback);
}

UpdateStatus AutoUpdater::downloadAndInstall(const UpdateInfo &info,
                                             ProgressCallback  progressCallback)
{
    const QString destination = QDir(m_downloadDir).filePath(info.fileName);

    qCInfo(lcAutoUpdater) << "Downloading update" << info.version << "…";
    const bool downloaded = m_downloader->download(
        info.downloadUrl, destination, info.checksum, progressCallback);
    if (!downloaded)
        return UpdateStatus::DownloadFailed;

    qCInfo(lcAutoUpdater) << "Installing update" << info.version << "…";
    if (!m_installer->install(destination))
        return UpdateStatus::InstallFailed;

    qCInfo(lcAutoUpdater) << "Update" << info.version << "installed successfully.";
    return UpdateStatus::UpdateInstalled;
}

std::unique_ptr<AutoUpdater> AutoUpdater::createDefault(const QString &manifestUrl,
                                                        const QString &downloadDir)
{
    return std::make_unique<AutoUpdater>(
        std::make_unique<HttpVersionChecker>(manifestUrl),
        std::make_unique<HttpDownloader>(),
        PlatformInstaller::create(),
        downloadDir);
}

} // namespace AutoUpdater
