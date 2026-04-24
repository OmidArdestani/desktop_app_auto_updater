cmake_minimum_required(VERSION 3.16)
project(DesktopAppAutoUpdater VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Qt MOC / UIC / RCC automation
set(CMAKE_AUTOMOC ON)

# Support both Qt 6 (preferred) and Qt 5
find_package(QT NAMES Qt6 Qt5 REQUIRED COMPONENTS Core Network)
find_package(Qt${QT_VERSION_MAJOR} REQUIRED COMPONENTS Core Network)

# ---------------------------------------------------------------------------
# Library target
# ---------------------------------------------------------------------------
add_library(auto_updater
    src/HttpVersionChecker.cpp
    src/HttpDownloader.cpp
    src/PlatformInstaller.cpp
    src/AutoUpdater.cpp
)

target_include_directories(auto_updater
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

target_link_libraries(auto_updater
    PUBLIC
        Qt${QT_VERSION_MAJOR}::Core
        Qt${QT_VERSION_MAJOR}::Network
)

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
enable_testing()
add_subdirectory(tests)
