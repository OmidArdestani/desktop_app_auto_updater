#include "../cpp/include/auto_updater/AutoUpdater.h"
#include "../cpp/include/auto_updater/Downloader.h"
#include "../cpp/include/auto_updater/Installer.h"
#include "../cpp/include/auto_updater/VersionChecker.h"

using VersionCheckerPtr = std::unique_ptr<AutoUpdater::IVersionChecker>;
using DownloaderPtr     = std::unique_ptr<AutoUpdater::IDownloader>;
using InstallerPtr      = std::unique_ptr<AutoUpdater::IInstaller>;

int main()
{
    auto ls_version_checker = AutoUpdater::LocalStorageVersionChecker("file://192.168.23.5/Pnw/2- Users/Omid/Test_Automation_Deploy/manifest.json");
    auto ls_downloader      = AutoUpdater::LocalStorageDownloader();
    auto installer          = AutoUpdater::PlatformInstaller();
    AutoUpdater::AutoUpdater updater((VersionCheckerPtr(&ls_version_checker)), DownloaderPtr(&ls_downloader), InstallerPtr(&installer));

    updater.checkAndUpdate("2.0.0");

    return 0;
}
