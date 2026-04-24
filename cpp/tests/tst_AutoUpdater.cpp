/**
 * tst_AutoUpdater.cpp
 * -------------------
 * Qt Test suite for the AutoUpdater library.
 *
 * Uses lightweight mock implementations of IVersionChecker, IDownloader, and
 * IInstaller to test AutoUpdater::checkAndUpdate() in isolation — mirroring
 * exactly what the Python test_updater.py does with unittest.mock.
 */

#include <QtTest>
#include <QDir>

#include "auto_updater/AutoUpdater.h"
#include "auto_updater/IVersionChecker.h"
#include "auto_updater/IDownloader.h"
#include "auto_updater/IInstaller.h"
#include "auto_updater/UpdateInfo.h"
#include "auto_updater/UpdateStatus.h"

using namespace AutoUpdater;

// ---------------------------------------------------------------------------
// Mock implementations
// ---------------------------------------------------------------------------

class MockVersionChecker : public IVersionChecker
{
public:
    std::optional<UpdateInfo> result;

    std::optional<UpdateInfo> checkForUpdate(const QString &) override
    {
        return result;
    }
};

class MockDownloader : public IDownloader
{
public:
    bool result = true;

    bool download(const QString &, const QString &,
                  const QString &, ProgressCallback) override
    {
        return result;
    }
};

class MockInstaller : public IInstaller
{
public:
    bool result = true;

    bool install(const QString &) override
    {
        return result;
    }
};

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------

static UpdateInfo makeUpdateInfo()
{
    UpdateInfo info;
    info.version     = QStringLiteral("2.0.0");
    info.downloadUrl = QStringLiteral("https://example.com/app-2.0.0.exe");
    info.fileName    = QStringLiteral("app-2.0.0.exe");
    return info;
}

// ---------------------------------------------------------------------------
// Test class
// ---------------------------------------------------------------------------

class tst_AutoUpdater : public QObject
{
    Q_OBJECT

private:
    /**
     * Build an AutoUpdater that takes ownership of the provided mocks.
     * downloadDir is set to the system temp directory to avoid any real I/O.
     */
    AutoUpdater makeUpdater(MockVersionChecker *checker,
                            MockDownloader     *downloader,
                            MockInstaller      *installer)
    {
        return AutoUpdater(
            std::unique_ptr<IVersionChecker>(checker),
            std::unique_ptr<IDownloader>(downloader),
            std::unique_ptr<IInstaller>(installer),
            QDir::tempPath());
    }

private slots:

    // --- Mirrors Python TestAutoUpdater::test_returns_up_to_date_when_no_update ---
    void test_upToDate()
    {
        auto *checker = new MockVersionChecker();
        checker->result = std::nullopt;

        auto updater = makeUpdater(checker, new MockDownloader(), new MockInstaller());
        QCOMPARE(updater.checkAndUpdate(QStringLiteral("1.0.0")),
                 UpdateStatus::UpToDate);
    }

    // --- Mirrors Python TestAutoUpdater::test_returns_update_available_when_auto_install_disabled ---
    void test_updateAvailableWhenAutoInstallDisabled()
    {
        auto *checker = new MockVersionChecker();
        checker->result = makeUpdateInfo();

        auto updater = makeUpdater(checker, new MockDownloader(), new MockInstaller());
        QCOMPARE(updater.checkAndUpdate(QStringLiteral("1.0.0"), /*autoInstall=*/false),
                 UpdateStatus::UpdateAvailable);
    }

    // --- Mirrors Python TestAutoUpdater::test_returns_update_installed_on_success ---
    void test_updateInstalledOnSuccess()
    {
        auto *checker    = new MockVersionChecker();
        checker->result  = makeUpdateInfo();
        auto *downloader = new MockDownloader();
        auto *installer  = new MockInstaller();

        auto updater = makeUpdater(checker, downloader, installer);
        QCOMPARE(updater.checkAndUpdate(QStringLiteral("1.0.0")),
                 UpdateStatus::UpdateInstalled);
    }

    // --- Mirrors Python TestAutoUpdater::test_returns_download_failed_when_download_errors ---
    void test_downloadFailed()
    {
        auto *checker    = new MockVersionChecker();
        checker->result  = makeUpdateInfo();
        auto *downloader = new MockDownloader();
        downloader->result = false;

        auto updater = makeUpdater(checker, downloader, new MockInstaller());
        QCOMPARE(updater.checkAndUpdate(QStringLiteral("1.0.0")),
                 UpdateStatus::DownloadFailed);
    }

    // --- Mirrors Python TestAutoUpdater::test_returns_install_failed_when_installer_errors ---
    void test_installFailed()
    {
        auto *checker    = new MockVersionChecker();
        checker->result  = makeUpdateInfo();
        auto *installer  = new MockInstaller();
        installer->result = false;

        auto updater = makeUpdater(checker, new MockDownloader(), installer);
        QCOMPARE(updater.checkAndUpdate(QStringLiteral("1.0.0")),
                 UpdateStatus::InstallFailed);
    }

    // --- Mirrors Python TestAutoUpdater::test_checker_called_with_current_version ---
    void test_checkerCalledWithCurrentVersion()
    {
        QString capturedVersion;
        // Use a lambda-based mock via a thin subclass
        class CapturingChecker : public IVersionChecker {
        public:
            QString *captured;
            std::optional<UpdateInfo> checkForUpdate(const QString &v) override {
                *captured = v;
                return std::nullopt;
            }
        };

        auto *checker = new CapturingChecker();
        checker->captured = &capturedVersion;

        auto updater = makeUpdater(
            checker,
            new MockDownloader(),
            new MockInstaller());

        updater.checkAndUpdate(QStringLiteral("1.5.0"));
        QCOMPARE(capturedVersion, QStringLiteral("1.5.0"));
    }

    // --- Mirrors Python TestUpdateInfo::test_basic_creation ---
    void test_updateInfoDefaults()
    {
        UpdateInfo info;
        info.version     = QStringLiteral("2.0.0");
        info.downloadUrl = QStringLiteral("https://example.com/app-2.0.0.exe");

        QCOMPARE(info.version,     QStringLiteral("2.0.0"));
        QCOMPARE(info.checksum,    QString());
        QCOMPARE(info.releaseNotes, QString());
        QVERIFY(!info.mandatory);
    }
};

QTEST_GUILESS_MAIN(tst_AutoUpdater)
#include "tst_AutoUpdater.moc"
