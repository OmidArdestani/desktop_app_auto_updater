#pragma once

namespace AutoUpdater {

/**
 * @brief High-level outcome of a single AutoUpdater::checkAndUpdate() call.
 *
 * Mirrors the Python UpdateStatus enum exactly.
 */
enum class UpdateStatus
{
    UpToDate,        ///< The installed version is already the latest.
    UpdateAvailable, ///< A newer version was found but installation was not attempted.
    UpdateInstalled, ///< The update was downloaded and successfully installed.
    CheckFailed,     ///< The version manifest could not be fetched or parsed.
    DownloadFailed,  ///< The installer could not be downloaded.
    InstallFailed    ///< The installer was downloaded but exited with an error.
};

} // namespace AutoUpdater
