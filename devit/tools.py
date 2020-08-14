import os
import pathlib
import subprocess
import sys

import fuzzywuzzy.fuzz


FUZZY_FIND_THRESHOLD = 75


class _Tool:
    def find_cmd(self, directory):
        if sys.platform == "win32":
            cmd_exts = self.cmd_exts
        else:
            cmd_exts = [""]
        for ext in cmd_exts:
            path = pathlib.Path(directory, f"{self.cmd_stem}{ext}")
            if path.is_file() and os.access(path, os.X_OK):
                return path
        return None

    def _find_project_here(self, path):
        for p in path.iterdir():
            if p.suffix != self.project_suffix:
                continue
            if fuzzywuzzy.fuzz.ratio(path.name, p.stem) > FUZZY_FIND_THRESHOLD:
                return p

    def _find_project_in_parent(self, path):
        for p in path.parent.iterdir():
            if p.suffix != self.project_suffix:
                continue
            if fuzzywuzzy.fuzz.ratio(path.name, p.stem) > FUZZY_FIND_THRESHOLD:
                return p

    def find_project(self, path):
        if not path.is_dir():
            return None
        for find in [self._find_project_here, self._find_project_in_parent]:
            found = find(path)
            if found:
                return found
        return None


class _DoesNotSupportBackground(ValueError):
    pass


class VisualStudioCode(_Tool):
    publisher = "Microsoft Corporation"
    display_prefix = "Microsoft Visual Studio Code"
    md_identifier = "com.microsoft.VSCode"
    cmd_stem = "code"
    cmd_exts = ["", ".cmd"]
    project_suffix = ".code-workspace"

    def __str__(self):
        return "Visual Studio Code"

    def get_bin_mac(self, app):
        return app.joinpath("Contents", "Resources", "app", "bin")

    def get_bin_win(self, root):
        return root.joinpath("bin")

    def iter_args(self, path, background):
        if background:
            raise _DoesNotSupportBackground()
        yield "--new-window"
        yield os.fspath(path)

    def run(self, command):
        # code and code.cmd on WIndows are not actual executables, but a batch
        # script. We need the shell to run it.
        return subprocess.call(command, shell=(sys.platform == "win32"))


class SublimeText3(_Tool):
    publisher = None
    display_prefix = None
    md_identifier = "com.sublimetext.3"
    cmd_stem = "subl"
    cmd_exts = [""]
    project_suffix = ".sublime-project"

    def __str__(self):
        return "Sublime Text 3"

    def get_bin_mac(self, app):
        return app.joinpath("Contents", "SharedSupport", "bin")

    def get_bin_win(self, root):
        return root  # TODO: Inspect Sublime Text to find where subl.exe is.

    def iter_args(self, path, background):
        if background:
            yield "--background"
        if path.suffix == self.project_suffix:
            yield "--project"
        else:
            yield "--new-window"
        yield os.fspath(path)

    def run(self, command):
        return subprocess.call(command)
