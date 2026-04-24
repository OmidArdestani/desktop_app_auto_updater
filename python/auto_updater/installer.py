"""
installer.py
------------
Abstractions and platform-specific implementations for launching an
installer executable and waiting for it to complete.

Supported platforms
~~~~~~~~~~~~~~~~~~~
* **Windows** – runs ``.exe`` / ``.msi`` installers via ``subprocess``.
* **macOS** – mounts ``.dmg`` images and runs ``installer`` for ``.pkg`` files.
* **Linux** – executes ``.sh`` scripts or invokes ``dpkg``/``rpm`` for
  package files.

The :func:`create_platform_installer` factory returns the correct
implementation for the current platform.
"""

import abc
import logging
import os
import platform
import subprocess
import sys
from typing import List

logger = logging.getLogger(__name__)


class IInstaller(abc.ABC):
    """Abstract base class for installer strategies."""

    @abc.abstractmethod
    def install(self, installer_path: str) -> bool:
        """Launch the installer at *installer_path* and wait for completion.

        Parameters
        ----------
        installer_path:
            Absolute path to the downloaded installer file.

        Returns
        -------
        bool
            *True* if the installer reported success (exit code 0), *False*
            otherwise.
        """


class WindowsInstaller(IInstaller):
    """Runs Windows installer packages (``.exe`` or ``.msi``)."""

    def install(self, installer_path: str) -> bool:
        ext = os.path.splitext(installer_path)[1].lower()
        if ext == ".msi":
            cmd: List[str] = ["msiexec", "/i", installer_path, "/qb", "/norestart"]
        else:
            # NSIS / Inno Setup style silent install
            cmd = [installer_path, "/S"]

        return self._run(cmd)

    @staticmethod
    def _run(cmd: List[str]) -> bool:
        logger.info("Running installer: %s", " ".join(cmd))
        try:
            result = subprocess.run(cmd, check=False)
            if result.returncode != 0:
                logger.error("Installer exited with code %d.", result.returncode)
                return False
            return True
        except OSError as exc:
            logger.error("Failed to launch installer: %s", exc)
            return False


class MacOSInstaller(IInstaller):
    """Installs macOS ``.pkg`` or ``.dmg`` packages."""

    def install(self, installer_path: str) -> bool:
        ext = os.path.splitext(installer_path)[1].lower()
        if ext == ".pkg":
            return self._install_pkg(installer_path)
        if ext == ".dmg":
            return self._install_dmg(installer_path)
        logger.error("Unsupported macOS installer format: %s", ext)
        return False

    def _install_pkg(self, pkg_path: str) -> bool:
        cmd = ["sudo", "installer", "-pkg", pkg_path, "-target", "/"]
        return self._run(cmd)

    def _install_dmg(self, dmg_path: str) -> bool:
        # Mount the image, find a .pkg inside, install, then unmount
        mount_point = "/Volumes/_auto_updater_mount"
        try:
            subprocess.run(
                ["hdiutil", "attach", dmg_path, "-mountpoint", mount_point, "-nobrowse"],
                check=True,
            )
            # Find the first .pkg in the volume
            for entry in os.listdir(mount_point):
                if entry.endswith(".pkg"):
                    pkg = os.path.join(mount_point, entry)
                    return self._install_pkg(pkg)
            logger.error("No .pkg found in DMG: %s", dmg_path)
            return False
        except subprocess.CalledProcessError as exc:
            logger.error("DMG mount/install failed: %s", exc)
            return False
        finally:
            subprocess.run(["hdiutil", "detach", mount_point], check=False)

    @staticmethod
    def _run(cmd: List[str]) -> bool:
        logger.info("Running installer: %s", " ".join(cmd))
        try:
            result = subprocess.run(cmd, check=False)
            return result.returncode == 0
        except OSError as exc:
            logger.error("Failed to launch installer: %s", exc)
            return False


class LinuxInstaller(IInstaller):
    """Installs Linux packages (``.deb``, ``.rpm``) or shell scripts."""

    def install(self, installer_path: str) -> bool:
        ext = os.path.splitext(installer_path)[1].lower()
        if ext == ".deb":
            cmd: List[str] = ["sudo", "dpkg", "-i", installer_path]
        elif ext == ".rpm":
            cmd = ["sudo", "rpm", "-Uvh", installer_path]
        elif ext == ".sh":
            cmd = ["bash", installer_path]
        else:
            logger.error("Unsupported Linux installer format: %s", ext)
            return False

        logger.info("Running installer: %s", " ".join(cmd))
        try:
            result = subprocess.run(cmd, check=False)
            return result.returncode == 0
        except OSError as exc:
            logger.error("Failed to launch installer: %s", exc)
            return False


def create_platform_installer() -> IInstaller:
    """Return the appropriate :class:`IInstaller` for the current OS.

    Raises
    ------
    RuntimeError
        If the current platform is not supported.
    """
    system = platform.system()
    if system == "Windows":
        return WindowsInstaller()
    if system == "Darwin":
        return MacOSInstaller()
    if system == "Linux":
        return LinuxInstaller()
    raise RuntimeError(f"Unsupported platform: {system}")
