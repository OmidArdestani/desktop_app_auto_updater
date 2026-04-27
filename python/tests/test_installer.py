import importlib.util
import pathlib
from unittest.mock import MagicMock, call, patch

import subprocess

INSTALLER_PATH = pathlib.Path(__file__).resolve().parents[1] / "auto_updater" / "installer.py"
INSTALLER_SPEC = importlib.util.spec_from_file_location("test_installer_module", INSTALLER_PATH)
installer_module = importlib.util.module_from_spec(INSTALLER_SPEC)
assert INSTALLER_SPEC.loader is not None
INSTALLER_SPEC.loader.exec_module(installer_module)

LinuxInstaller = installer_module.LinuxInstaller
MacOSInstaller = installer_module.MacOSInstaller
WindowsInstaller = installer_module.WindowsInstaller


def test_windows_installer_launches_exe_detached():
    with patch.object(installer_module.subprocess, "Popen") as popen:
        popen.return_value = MagicMock(pid=321)

        assert WindowsInstaller().install("/tmp/setup.exe") is True

        args, kwargs = popen.call_args
        assert args[0] == ["/tmp/setup.exe", "/S"]
        assert kwargs["close_fds"] is True

        expected_flags = getattr(subprocess, "DETACHED_PROCESS", 0)
        expected_flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        if expected_flags:
            assert kwargs["creationflags"] == expected_flags
        else:
            assert "creationflags" not in kwargs


def test_linux_shell_installer_starts_new_session():
    with patch.object(installer_module.subprocess, "Popen") as popen:
        popen.return_value = MagicMock(pid=654)

        assert LinuxInstaller().install("/tmp/install.sh") is True

        args, kwargs = popen.call_args
        assert args[0] == ["bash", "/tmp/install.sh"]
        assert kwargs["close_fds"] is True
        assert kwargs["start_new_session"] is True


def test_macos_dmg_copies_pkg_before_launching_installer():
    installer = MacOSInstaller()

    with (
        patch.object(installer_module.tempfile, "mkdtemp", side_effect=["/tmp/mount", "/tmp/pkgcopy"]),
        patch.object(installer_module.subprocess, "run") as run,
        patch.object(installer_module.os, "listdir", return_value=["App.pkg"]),
        patch.object(installer_module.os.path, "isdir", return_value=False),
        patch.object(installer_module.shutil, "copy2") as copy2,
        patch.object(MacOSInstaller, "_install_pkg", return_value=True) as install_pkg,
        patch.object(installer_module.shutil, "rmtree") as rmtree,
    ):
        assert installer.install("/tmp/update.dmg") is True

        copy2.assert_called_once_with("/tmp/mount/App.pkg", "/tmp/pkgcopy/App.pkg")
        install_pkg.assert_called_once_with("/tmp/pkgcopy/App.pkg")
        run.assert_has_calls(
            [
                call(
                    ["hdiutil", "attach", "/tmp/update.dmg", "-mountpoint", "/tmp/mount", "-nobrowse"],
                    check=True,
                ),
                call(["hdiutil", "detach", "/tmp/mount"], check=False),
            ]
        )
        rmtree.assert_called_once_with("/tmp/mount", ignore_errors=True)