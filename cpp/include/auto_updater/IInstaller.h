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

} // namespace AutoUpdater
