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

    qCInfo(lcInstaller) << "Launching installer in detached mode:" << program << args;

    qint64 processId = 0;
    const bool started = QProcess::startDetached(program, args, QString(), &processId);
    if (!started) {
        qCWarning(lcInstaller) << "Failed to launch detached installer process."
                       << "Program:" << program
                       << "Args:" << args
                       << "Possible causes: file not found, insufficient permissions, or invalid path.";
        return false;
    }

    qCInfo(lcInstaller) << "Installer launched with PID:" << processId;
    return true;
}

std::unique_ptr<IInstaller> PlatformInstaller::create()
{
    return std::make_unique<PlatformInstaller>();
}

} // namespace AutoUpdater
