#include "auto_updater/Installer.h"

#include <QFileInfo>
#include <QLoggingCategory>
#include <QProcess>
#include <QStringList>

Q_LOGGING_CATEGORY(lcInstaller, "auto_updater.installer")

namespace AutoUpdater {

bool PlatformInstaller::install(const QString &installerPath)
{
    const QString ext = QFileInfo(installerPath).suffix().toLower();
    QString       program;
    QStringList   args;

#if defined(Q_OS_WIN)
    if (ext == QLatin1String("msi")) {
        program = QStringLiteral("msiexec");
        args << QStringLiteral("/i") << installerPath
             << QStringLiteral("/qb") << QStringLiteral("/norestart");
    } else {
        // NSIS / Inno Setup style silent install
        program = installerPath;
        args << QStringLiteral("/S");
    }

#elif defined(Q_OS_MACOS)
    if (ext == QLatin1String("pkg")) {
        program = QStringLiteral("sudo");
        args << QStringLiteral("installer")
             << QStringLiteral("-pkg") << installerPath
             << QStringLiteral("-target") << QStringLiteral("/");
    } else {
        qCWarning(lcInstaller) << "Unsupported macOS installer format:" << ext;
        return false;
    }

#else  // Linux
    if (ext == QLatin1String("deb")) {
        program = QStringLiteral("sudo");
        args << QStringLiteral("dpkg") << QStringLiteral("-i") << installerPath;
    } else if (ext == QLatin1String("rpm")) {
        program = QStringLiteral("sudo");
        args << QStringLiteral("rpm") << QStringLiteral("-Uvh") << installerPath;
    } else if (ext == QLatin1String("sh")) {
        program = QStringLiteral("bash");
        args << installerPath;
    } else {
        qCWarning(lcInstaller) << "Unsupported Linux installer format:" << ext;
        return false;
    }
#endif

    qCInfo(lcInstaller) << "Running installer:" << program << args;

    QProcess process;
    process.start(program, args);

    if (!process.waitForFinished(-1)) {
        qCWarning(lcInstaller) << "Installer process failed to finish:"
                               << process.errorString();
        return false;
    }

    const int exitCode = process.exitCode();
    if (exitCode != 0) {
        qCWarning(lcInstaller) << "Installer exited with code" << exitCode;
        return false;
    }

    return true;
}

std::unique_ptr<IInstaller> PlatformInstaller::create()
{
    return std::make_unique<PlatformInstaller>();
}

} // namespace AutoUpdater
