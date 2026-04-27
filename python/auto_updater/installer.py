"""
installer.py
------------
Abstractions and platform-specific implementations for launching an
installer executable so it can continue running after the current app exits.

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
import shutil
import subprocess
import tempfile
from typing import List

logger = logging.getLogger(__name__)


class IInstaller(abc.ABC):
    """Abstract base class for installer strategies."""

    @abc.abstractmethod
    def install(self, installer_path: str) -> bool:
        """Launch the installer at *installer_path* independently.

        Parameters
        ----------
        installer_path:
            Absolute path to the downloaded installer file.

        Returns
        -------
        bool
            *True* if the installer process was started successfully,
            *False* otherwise.
        """


def _launch_detached(cmd: List[str], *, windows: bool = False) -> bool:
    logger.info("Starting installer independently: %s", " ".join(cmd))

    try:
        kwargs = {"close_fds": True}
        if windows:
            creationflags  = getattr(subprocess, "DETACHED_PROCESS", 0)
            creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            if creationflags:
                kwargs["creationflags"] = creationflags
        else:
            kwargs["start_new_session"] = True

        process = subprocess.Popen(cmd, **kwargs)
        logger.info("Installer launched with pid %s.", process.pid)
        return True
    except OSError as exc:
        logger.error("Failed to launch installer: %s", exc)
        return False


class WindowsInstaller(IInstaller):
    """Runs Windows installer packages (``.exe`` or ``.msi``)."""

    def install(self, installer_path: str) -> bool:
        ext = os.path.splitext(installer_path)[1].lower()
        if ext == ".msi":
            cmd: List[str] = ["msiexec", "/i", installer_path, "/qb", "/norestart"]
        else:
            # NSIS / Inno Setup style silent install
            cmd = [installer_path, "/S"]

        return _launch_detached(cmd, windows=True)

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
        return _launch_detached(cmd)

    def _install_dmg(self, dmg_path: str) -> bool:
        # Mount the image, copy the first .pkg outside the volume, install it,
        # then unmount the image so the installer can keep running standalone.
        mount_point = tempfile.mkdtemp(prefix="auto_updater_mount_")
        try:
            subprocess.run(
                ["hdiutil", "attach", dmg_path, "-mountpoint", mount_point, "-nobrowse"],
                check=True,
            )
            # Find the first .pkg in the volume
            for entry in os.listdir(mount_point):
                if entry.endswith(".pkg"):
                    pkg = os.path.join(mount_point, entry)
                    detached_pkg = self._copy_pkg_to_temp(pkg)
                    return self._install_pkg(detached_pkg)
            logger.error("No .pkg found in DMG: %s", dmg_path)
            return False
        except subprocess.CalledProcessError as exc:
            logger.error("DMG mount/install failed: %s", exc)
            return False
        finally:
            subprocess.run(["hdiutil", "detach", mount_point], check=False)
            shutil.rmtree(mount_point, ignore_errors=True)

    @staticmethod
    def _copy_pkg_to_temp(pkg_path: str) -> str:
        """
        Copy a package file or directory to a temporary location.
        
        This method creates a temporary directory and copies the provided package
        (file or directory) into it, preserving the original filename/dirname.
        
        Args:
            pkg_path (str): The path to the package file or directory to be copied.
        
        Returns:
            str: The full path to the copied package in the temporary directory.
        
        Note:
            Cleanup of the temporary directory is the caller's responsibility.
            Consider implementing a cleanup mechanism (e.g., using context managers
            or atexit handlers) to ensure temporary resources are properly removed.
        """
        temp_dir = tempfile.mkdtemp(prefix="auto_updater_pkg_")
        destination = os.path.join(temp_dir, os.path.basename(pkg_path))

        if os.path.isdir(pkg_path):
            shutil.copytree(pkg_path, destination)
        else:
            shutil.copy2(pkg_path, destination)

        return destination

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

        return _launch_detached(cmd)

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
