import os
import pathlib
import re
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
        for p in path.glob(self.project_pattern):
            if fuzzywuzzy.fuzz.ratio(path.name, p.stem) > FUZZY_FIND_THRESHOLD:
                return p

    def _find_project_in_parent(self, path):
        for p in path.parent.glob(self.project_pattern):
            if fuzzywuzzy.fuzz.ratio(path.name, p.stem) > FUZZY_FIND_THRESHOLD:
                return p

    def _find_project(self, path):
        for find in [self._find_project_here, self._find_project_in_parent]:
            found = find(path)
            if found:
                return found


class VisualStudioCode(_Tool):
    publisher = "Microsoft Corporation"
    display_prefix = "Microsoft Visual Studio Code"
    md_identifier = "com.microsoft.VSCode"
    cmd_stem = "code"
    cmd_exts = ["", ".cmd"]
    project_pattern = "*.code-workspace"

    def __str__(self):
        return "Visual Studio Code"

    def get_bin_in_app(self, app):
        return app.joinpath("Contents", "Resources", "app", "bin")

    def iter_args(self, name, background):
        assert not background, "VS Code does not support background launch"
        path = pathlib.Path(name).resolve()
        if not path.is_dir():
            print(f"Opening {path} with {self}", file=sys.stderr)
            yield "--new-window"
            yield os.fspath(path)
            return
        project = self._find_project(path)
        if project:
            print(f"Opening {project} with {self}", file=sys.stderr)
            yield "--new-window"
            yield os.fspath(project)
        else:
            print(f"Opening {path} with {self}", file=sys.stderr)
            yield "--new-window"
            yield os.fspath(path)


SUBL_NAME_PATTERN = re.compile(
    r"""
    ^
    ([^:]+)         # File/directory name.
    (?:
        :\d+        # Line number.
        (?::\d+)?   # Column number.
    )?
    $
    """,
    re.VERBOSE,
)


class SublimeText3(_Tool):
    publisher = None
    display_prefix = None
    md_identifier = "com.sublimetext.3"
    cmd_stem = "subl"
    cmd_exts = [""]
    project_pattern = "*.sublime-project"

    def __str__(self):
        return "Sublime Text 3"

    def get_bin_in_app(self, app):
        return app.joinpath("Contents", "SharedSupport", "bin")

    def iter_args(self, name, background):
        if background:
            yield "--background"
        match = SUBL_NAME_PATTERN.match(name)
        if match:
            path = pathlib.Path(match.group(1))
        else:
            path = pathlib.Path(name)
        path = path.resolve()
        if not path.is_dir():
            print(f"Opening {name} with {self}", file=sys.stderr)
            yield "--new-window"
            yield name
            return
        project = self._find_project(path)
        if project:
            print(f"Opening {project} with {self}", file=sys.stderr)
            yield "--project"
            yield os.fspath(project)
        else:
            print(f"Opening {path} with {self}", file=sys.stderr)
            yield "--new-window"
            yield os.fspath(path)
