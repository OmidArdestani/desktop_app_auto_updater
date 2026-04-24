#pragma once

#include <QString>

namespace AutoUpdater {

/**
 * @brief Abstract interface for installer strategies.
 *
 * Mirrors the Python IInstaller ABC exactly.
 */
class IInstaller
{
public:
    virtual ~IInstaller() = default;

    /**
     * @brief Launch the installer at @p installerPath and wait for it to
     *        complete.
     *
     * @param installerPath  Absolute path to the downloaded installer file.
     * @return true   if the installer reported success (exit code 0).
     * @return false  otherwise.
     */
    virtual bool install(const QString &installerPath) = 0;
};


/**
 * @brief Platform-specific installer implementation.
 *
 * Mirrors the Python PlatformInstaller / create_platform_installer() pair.
 *
 * Supported platforms
 * -------------------
 * - Windows  – runs .exe (NSIS/Inno Setup silent) or .msi via msiexec.
 * - macOS    – runs .pkg via the system `installer` command.
 * - Linux    – runs .deb via dpkg, .rpm via rpm, or .sh via bash.
 *
 * Uses QProcess to launch the installer process and wait for it to finish,
 * mirroring the Python subprocess.run() calls.
 */
class PlatformInstaller : public IInstaller
{
public:
    bool install(const QString &installerPath) override;

    /**
     * @brief Factory that returns the correct IInstaller for the current OS.
     *
     * Mirrors the Python create_platform_installer() factory function.
     */
    static std::unique_ptr<IInstaller> create();
};

} // namespace AutoUpdater
