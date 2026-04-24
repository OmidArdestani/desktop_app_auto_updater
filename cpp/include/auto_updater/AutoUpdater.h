#pragma once

#include "IVersionChecker.h"
#include "IDownloader.h"
#include "IInstaller.h"
#include "UpdateStatus.h"

#include <memory>
#include <QString>

namespace AutoUpdater {

/**
 * @brief Orchestrates the full update lifecycle.
 *
 * Mirrors the Python AutoUpdater class and create_default_updater()
 * factory function exactly.
 *
 * The three steps are:
 *  1. Ask the IVersionChecker whether a new version exists.
 *  2. Download the installer via IDownloader.
 *  3. Launch the installer via IInstaller.
 *
 * @param checker      Strategy used to detect available updates.
 * @param downloader   Strategy used to fetch the installer binary.
 * @param installer    Strategy used to execute the installer.
 * @param downloadDir  Directory where installers are saved.  Defaults to
 *                     QStandardPaths::TempLocation.
 */
class AutoUpdater
{
public:
    AutoUpdater(std::unique_ptr<IVersionChecker> checker,
                std::unique_ptr<IDownloader>     downloader,
                std::unique_ptr<IInstaller>      installer,
                const QString                   &downloadDir = {});

    /**
     * @brief Run the full update flow.
     *
     * @param currentVersion   Version string of the currently installed app.
     * @param autoInstall      When true (default), automatically download and
     *                         install if an update is found.  When false,
     *                         return UpdateStatus::UpdateAvailable without
     *                         downloading.
     * @param progressCallback Optional callback forwarded to the downloader,
     *                         receiving (bytesReceived, bytesTotal).
     * @return UpdateStatus    Describes the final outcome.
     */
    UpdateStatus checkAndUpdate(const QString   &currentVersion,
                                bool             autoInstall       = true,
                                ProgressCallback progressCallback  = nullptr);

    /**
     * @brief Build an AutoUpdater wired with platform-appropriate defaults.
     *
     * Mirrors the Python create_default_updater() factory function.
     *
     * @param manifestUrl  URL of the JSON version manifest.
     * @param downloadDir  Directory for downloaded installers.
     */
    static std::unique_ptr<AutoUpdater> createDefault(const QString &manifestUrl,
                                                      const QString &downloadDir = {});

private:
    UpdateStatus downloadAndInstall(const UpdateInfo &info,
                                    ProgressCallback  progressCallback);

    std::unique_ptr<IVersionChecker> m_checker;
    std::unique_ptr<IDownloader>     m_downloader;
    std::unique_ptr<IInstaller>      m_installer;
    QString                          m_downloadDir;
};

} // namespace AutoUpdater
