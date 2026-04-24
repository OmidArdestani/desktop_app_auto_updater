# Desktop App Auto Updater

A cross-platform library that checks a URL (HTTP/HTTPS or local-network storage)
for a newer version of a desktop application, downloads the installer, verifies
its integrity, and runs it — fully automatically.

The library is available in **two languages** that share an **identical
architecture**: Python and C++ (Qt framework).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Descriptions](#component-descriptions)
3. [Sequence Diagram](#sequence-diagram)
4. [Version Manifest Format](#version-manifest-format)
5. [Project Structure](#project-structure)
6. [Python Implementation](#python-implementation)
7. [C++ / Qt Implementation](#c--qt-implementation)

---

## Architecture Overview

Both implementations follow the same layered design:

```
┌─────────────────────────────────────────────────────────┐
│                      AutoUpdater                        │
│  (Orchestrator — coordinates the three steps below)     │
└────────────┬──────────────┬──────────────┬──────────────┘
             │              │              │
             ▼              ▼              ▼
   IVersionChecker     IDownloader     IInstaller
         │                  │               │
         ▼                  ▼               ▼
 HttpVersionChecker   HttpDownloader  PlatformInstaller
```

Each layer is defined as an **interface** (Python ABC / C++ pure-virtual class),
making every component independently replaceable for testing or extension.

### Component Responsibilities

| Component | Responsibility |
|---|---|
| `UpdateInfo` | Immutable data object — carries version, URL, checksum, and metadata for one update |
| `UpdateStatus` | Enum describing the final outcome of an update attempt |
| `IVersionChecker` | Interface: "Is there a newer version available?" |
| `HttpVersionChecker` | Fetches a JSON manifest over HTTP/HTTPS and compares versions |
| `IDownloader` | Interface: "Download the installer to a local file" |
| `HttpDownloader` | Streams the file with progress reporting and SHA-256 verification |
| `IInstaller` | Interface: "Run the installer and wait for it to finish" |
| `PlatformInstaller` | Detects the OS and runs the appropriate install command |
| `AutoUpdater` | Façade that wires the three interfaces together into a single call |

---

## Component Descriptions

### UpdateInfo

A pure data structure (Python `dataclass` / C++ `struct`).  Created by
`IVersionChecker` and consumed by `IDownloader` and `IInstaller`.

| Field | Type | Description |
|---|---|---|
| `version` | string | New version, e.g. `"2.1.0"` |
| `downloadUrl` | string | Full URL of the installer |
| `checksum` | string | SHA-256 hex digest (empty = skip verification) |
| `releaseNotes` | string | Human-readable change description |
| `mandatory` | bool | Whether the update is required |
| `fileName` | string | Suggested local file name (derived from URL if omitted) |

### UpdateStatus

Enum returned by `AutoUpdater.checkAndUpdate()`:

| Value | Meaning |
|---|---|
| `UpToDate` | Installed version is already current |
| `UpdateAvailable` | Newer version found, `autoInstall=false` |
| `UpdateInstalled` | Update downloaded and installed successfully |
| `CheckFailed` | Could not fetch / parse the version manifest |
| `DownloadFailed` | Network error or checksum mismatch |
| `InstallFailed` | Installer process returned a non-zero exit code |

### IVersionChecker / HttpVersionChecker

`HttpVersionChecker` fetches a JSON manifest from the configured URL and
compares the `"version"` field to the currently installed version using
semantic-version comparison (`packaging.version.Version` in Python;
`QVersionNumber` in C++).  Returns an `UpdateInfo` when the remote version
is strictly newer, otherwise `None` / `std::nullopt`.

### IDownloader / HttpDownloader

`HttpDownloader` streams the installer file in chunks, writing directly to
disk to keep memory usage flat regardless of installer size.  A
`ProgressCallback` (called with `(bytesReceived, bytesTotal)`) lets callers
show a progress bar.  After the transfer, the file's SHA-256 digest is
compared to `UpdateInfo.checksum`; the file is deleted and `false` returned
on mismatch.

### IInstaller / PlatformInstaller

`PlatformInstaller` detects the host OS and installer format, then launches
the appropriate tool via `subprocess.run` (Python) / `QProcess` (C++):

| OS | Format | Command |
|---|---|---|
| Windows | `.exe` | `<installer>.exe /S` (silent NSIS/Inno Setup) |
| Windows | `.msi` | `msiexec /i <installer> /qb /norestart` |
| macOS | `.pkg` | `sudo installer -pkg <installer> -target /` |
| Linux | `.deb` | `sudo dpkg -i <installer>` |
| Linux | `.rpm` | `sudo rpm -Uvh <installer>` |
| Linux | `.sh` | `bash <installer>` |

### AutoUpdater

The public façade.  Accepts constructor-injected strategy objects and
provides a single `checkAndUpdate(currentVersion)` method.  A static
`createDefault(manifestUrl)` factory wires up sensible defaults for the
current platform.

---

## Sequence Diagram

```
Application          AutoUpdater        IVersionChecker     IDownloader     IInstaller
     │                    │                    │                  │               │
     │  checkAndUpdate()  │                    │                  │               │
     │───────────────────>│                    │                  │               │
     │                    │  checkForUpdate()  │                  │               │
     │                    │───────────────────>│                  │               │
     │                    │  UpdateInfo / null │                  │               │
     │                    │<───────────────────│                  │               │
     │                    │                    │                  │               │
     │                    │         [update available]            │               │
     │                    │                    │  download()      │               │
     │                    │───────────────────────────────────── >│               │
     │                    │                    │  true / false    │               │
     │                    │<──────────────────────────────────────│               │
     │                    │                    │                  │               │
     │                    │                    │                  │  install()    │
     │                    │──────────────────────────────────────────────────────>│
     │                    │                    │                  │  true / false │
     │                    │<──────────────────────────────────────────────────────│
     │  UpdateStatus      │                    │                  │               │
     │<───────────────────│                    │                  │               │
```

---

## Version Manifest Format

The manifest is a JSON file hosted at any URL reachable from the client
machine (public web, private network share, `file://`, etc.).

```json
{
    "version":       "2.1.0",
    "download_url":  "https://example.com/releases/MyApp-2.1.0-setup.exe",
    "checksum":      "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "release_notes": "Bug fixes and performance improvements.",
    "mandatory":     false,
    "file_name":     "MyApp-2.1.0-setup.exe"
}
```

Only `version` and `download_url` are required.

---

## Project Structure

```
desktop_app_auto_updater/
│
├── python/                         # Python library
│   ├── auto_updater/
│   │   ├── __init__.py             # Public API surface
│   │   ├── update_info.py          # UpdateInfo dataclass
│   │   ├── version_checker.py      # IVersionChecker, HttpVersionChecker
│   │   ├── downloader.py           # IDownloader, HttpDownloader
│   │   ├── installer.py            # IInstaller, PlatformInstaller
│   │   └── updater.py              # AutoUpdater, UpdateStatus, create_default_updater
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_update_info.py
│   │   ├── test_version_checker.py
│   │   ├── test_downloader.py
│   │   └── test_updater.py
│   ├── requirements.txt
│   └── setup.py
│
└── cpp/                            # C++ / Qt library
    ├── include/
    │   └── auto_updater/
    │       ├── UpdateInfo.h        # UpdateInfo struct
    │       ├── UpdateStatus.h      # UpdateStatus enum class
    │       ├── IVersionChecker.h   # Pure-virtual interface
    │       ├── HttpVersionChecker.h
    │       ├── IDownloader.h       # Pure-virtual interface + ProgressCallback
    │       ├── HttpDownloader.h
    │       ├── IInstaller.h        # Pure-virtual interface
    │       ├── PlatformInstaller.h
    │       └── AutoUpdater.h
    ├── src/
    │   ├── HttpVersionChecker.cpp  # QNetworkAccessManager + QEventLoop
    │   ├── HttpDownloader.cpp      # Streaming + QCryptographicHash
    │   ├── PlatformInstaller.cpp   # QProcess + platform macros
    │   └── AutoUpdater.cpp
    ├── tests/
    │   ├── CMakeLists.txt
    │   └── tst_AutoUpdater.cpp     # Qt Test with mock objects
    └── CMakeLists.txt
```

---

## Python Implementation

### Requirements

- Python ≥ 3.8
- `requests` ≥ 2.28
- `packaging` ≥ 23.0

```bash
cd python
pip install -r requirements.txt
```

### Running Tests

```bash
cd python
pip install pytest
pytest tests/ -v
```

### Usage

```python
from auto_updater import create_default_updater, UpdateStatus

updater = create_default_updater("https://example.com/version.json")
status = updater.check_and_update("1.0.0")

if status == UpdateStatus.UPDATE_INSTALLED:
    print("Update installed — please restart the application.")
elif status == UpdateStatus.UP_TO_DATE:
    print("Already up to date.")
```

#### Custom components (dependency injection)

```python
from auto_updater import AutoUpdater, HttpVersionChecker, HttpDownloader
from auto_updater import create_platform_installer

updater = AutoUpdater(
    version_checker = HttpVersionChecker("https://example.com/version.json"),
    downloader      = HttpDownloader(),
    installer       = create_platform_installer(),
    download_dir    = "/tmp/my_app_updates",
)
status = updater.check_and_update(
    "1.0.0",
    auto_install      = True,
    progress_callback = lambda recv, total: print(f"{recv}/{total} bytes"),
)
```

---

## C++ / Qt Implementation

### Requirements

- Qt 5.6+ **or** Qt 6 (modules: `Core`, `Network`, `Test`)
- CMake ≥ 3.16
- C++17

### Building

```bash
cd cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

### Running Tests

```bash
cd build
ctest --output-on-failure
```

### Usage

```cpp
#include "auto_updater/AutoUpdater.h"
using namespace AutoUpdater;

// One-liner factory
auto updater = AutoUpdater::createDefault("https://example.com/version.json");
UpdateStatus status = updater->checkAndUpdate("1.0.0");

switch (status) {
case UpdateStatus::UpdateInstalled:
    qInfo() << "Update installed — please restart.";
    break;
case UpdateStatus::UpToDate:
    qInfo() << "Already up to date.";
    break;
default:
    break;
}
```

#### Custom components (dependency injection)

```cpp
#include "auto_updater/AutoUpdater.h"
#include "auto_updater/HttpVersionChecker.h"
#include "auto_updater/HttpDownloader.h"
#include "auto_updater/PlatformInstaller.h"
using namespace AutoUpdater;

auto updater = std::make_unique<AutoUpdater>(
    std::make_unique<HttpVersionChecker>("https://example.com/version.json"),
    std::make_unique<HttpDownloader>(),
    PlatformInstaller::create(),
    QDir::tempPath()
);

UpdateStatus status = updater->checkAndUpdate(
    "1.0.0",
    /*autoInstall=*/true,
    [](qint64 recv, qint64 total) {
        qDebug() << recv << "/" << total << "bytes";
    }
);
```

### Qt Module Usage Summary

| Qt Module | Used By | Purpose |
|---|---|---|
| `QtNetwork` | `HttpVersionChecker`, `HttpDownloader` | `QNetworkAccessManager`, `QNetworkReply` |
| `QtCore` | All | `QString`, `QVersionNumber`, `QJsonDocument`, `QCryptographicHash`, `QProcess`, `QEventLoop`, `QTimer`, `QStandardPaths` |
| `QtTest` | `tst_AutoUpdater` | Unit test framework |
