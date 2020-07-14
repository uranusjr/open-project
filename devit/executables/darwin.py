import os
import pathlib
import subprocess


def _find_with_mdfind(tool):
    mdfind = pathlib.Path("/usr/bin/mdfind")
    if not mdfind.is_file():
        return None
    app = subprocess.check_output(
        [os.fspath(mdfind), f"kMDItemCFBundleIdentifier={tool.md_identifier}"],
        encoding="utf-8",
    ).strip()
    if not app:
        return None
    cmd = tool.find_cmd(tool.get_bin_mac(pathlib.Path(app)))
    if cmd.is_file():
        return cmd
    return None


def find(tool):
    return _find_with_mdfind(tool)
