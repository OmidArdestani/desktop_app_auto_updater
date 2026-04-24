#pragma once

#include "IInstaller.h"

#include <memory>

namespace AutoUpdater {

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
