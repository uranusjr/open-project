import argparse
import enum
import os
import pathlib
import subprocess
import sys

from . import executables, tools


class _ToolChoice(enum.Enum):
    code = tools.VisualStudioCode()
    subl = tools.SublimeText3()


_DEFAULT_TOOL = os.environ.get("OPEN_PROJECT_DEFAULT_TOOL") or "code"


def _resolved_path(value):
    return pathlib.Path(value).resolve()


def _parse_args(args):
    parser = argparse.ArgumentParser(prog="devit")
    parser.add_argument(
        "name",
        nargs="?",
        default=".",
        type=_resolved_path,
        help="Target to open (default: current directory)",
    )
    parser.add_argument(
        "--background",
        "-b",
        dest="in_background",
        action="store_true",
        help="Don't activate the application (only works with subl)",
    )

    parser.set_defaults(default_tool=None)
    tool = parser.add_mutually_exclusive_group()
    for item in _ToolChoice:
        tool.add_argument(
            f"--{item.name}",
            action="store_const",
            dest="tool",
            const=item.value,
            help=f"Launch {item.value}",
        )

    return parser.parse_args(args)


def _detect_open_target(path):
    if not path.is_dir():
        return None, path
    for choice in _ToolChoice:
        project = choice.value.find_project(path)
        if project:
            return choice.value, project
    return None, path


def main(argv=None):
    options = _parse_args(argv)

    if options.tool is None:
        tool, path = _detect_open_target(options.name)
        tool = tool or _ToolChoice[_DEFAULT_TOOL].value
    else:
        tool = options.tool
        path = tool.find_project(options.name) or options.name

    try:
        command = [
            os.fspath(executables.find(tool)),
            *tool.iter_args(path, options.in_background),
        ]
    except tools._DoesNotSupportBackground:
        print(f"{tool} does not support --background", file=sys.stderr)
        return -1

    print(f"Opening {path} with {tool}", file=sys.stdout)
    return tool.run(command)
