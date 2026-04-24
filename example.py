from python.auto_updater.downloader import LocalStorageDownloader
from python.auto_updater.installer import WindowsInstaller
from python.auto_updater.updater import AutoUpdater
from python.auto_updater.version_checker import LocalStorageVersionChecker

def main():
    updater = AutoUpdater(
            version_checker=LocalStorageVersionChecker("/Users/omid.a/Downloads/manifest.json"),
            downloader=LocalStorageDownloader(),
            installer=WindowsInstaller()
        )

    result = updater.check_and_update("1.2.3")

    print(f"Update installed successfully.{result}")

if __name__ == "__main__":
    main()