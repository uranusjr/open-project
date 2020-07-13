import os
import pathlib
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
        for find in [self._find_project_here, self._find_project_in_parent]:
            found = find(path)
            if found:
                return found


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

    def get_bin_in_app(self, app):
        return app.joinpath("Contents", "Resources", "app", "bin")

    def iter_args(self, path, background):
        if background:
            raise _DoesNotSupportBackground()
        yield "--new-window"
        yield os.fspath(path)


class SublimeText3(_Tool):
    publisher = None
    display_prefix = None
    md_identifier = "com.sublimetext.3"
    cmd_stem = "subl"
    cmd_exts = [""]
    project_suffix = ".sublime-project"

    def __str__(self):
        return "Sublime Text 3"

    def get_bin_in_app(self, app):
        return app.joinpath("Contents", "SharedSupport", "bin")

    def iter_args(self, path, background):
        if background:
            yield "--background"
        if path.suffix == self.project_suffix:
            yield "--project"
        else:
            yield "--new-window"
        yield os.fspath(path)
