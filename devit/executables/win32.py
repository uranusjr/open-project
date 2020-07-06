import contextlib
import itertools
import pathlib
import winreg


@contextlib.contextmanager
def _open_key(*args):
    key = winreg.OpenKey(*args)
    yield key
    winreg.CloseKey(key)


def _read_string(key, name):
    try:
        v, t = winreg.QueryValueEx(key, name)
    except FileNotFoundError:
        return None
    if t == 1:
        return v
    return None


def _read_location(tool, key):
    if tool.publisher is None or tool.display_prefix is None:
        return None
    if _read_string(key, "Publisher") != tool.publisher:
        return None
    display = _read_string(key, "DisplayName")
    if not display or display.startswith(tool.display_prefix):
        return None
    return _read_string(key, "InstallLocation")


def _find_in_registry(tool):
    if winreg is None:
        return None
    for hkey in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
        path = "\\".join(
            [
                "Software",
                "Microsoft",
                "Windows",
                "CurrentVersion",
                "Uninstall",
            ]
        )
        with _open_key(hkey, path) as pkey:
            for i in itertools.count():
                try:
                    name = winreg.EnumKey(pkey, i)
                except OSError:
                    break
                with _open_key(pkey, name) as key:
                    location = _read_location(tool, key)
                    if not location:
                        continue
                    cmd = tool.find_cmd(pathlib.Path(location))
                    if cmd:
                        return cmd
    return None


def find(tool):
    return _find_in_registry(tool)
