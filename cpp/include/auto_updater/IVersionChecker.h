#pragma once

#include "UpdateInfo.h"

#include <optional>
#include <QString>

namespace AutoUpdater {

/**
 * @brief Abstract interface for version-checking strategies.
 *
 * Mirrors the Python IVersionChecker ABC exactly.
 */
class IVersionChecker
{
public:
    virtual ~IVersionChecker() = default;

    /**
     * @brief Compare @p currentVersion against the latest available version.
     *
     * @param currentVersion  Version string of the currently installed app,
     *                        e.g. "1.0.0".
     * @return UpdateInfo     If a newer version is available.
     * @return std::nullopt   If the application is already up to date or the
     *                        check fails gracefully.
     */
    virtual std::optional<UpdateInfo> checkForUpdate(const QString &currentVersion) = 0;
};

} // namespace AutoUpdater
