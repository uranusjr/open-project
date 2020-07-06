import os
import sys


def _find_in_path(tool):
    directories = os.environ["PATH"].split(os.pathsep)
    for directory in directories:
        cmd = tool.find_cmd(directory)
        if cmd:
            return cmd
    return None


def _find_on_platform(tool):
    if sys.platform == "win32":
        from . import win32
        return win32.find(tool)
    elif sys.platform == "darwin":
        from . import darwin
        return darwin.find(tool)
    return None


def find(tool):
    cmd = _find_in_path(tool) or _find_on_platform(tool)
    if not cmd:
        raise ValueError(f"{tool.cmd_stem} for {tool} not found")
    return cmd
