import argparse
import enum
import os
import subprocess

from . import executables, tools


class _ToolChoice(enum.Enum):
    code = tools.VisualStudioCode()
    subl = tools.SublimeText3()


_DEFAULT_TOOL = os.environ.get("OPEN_PROJECT_DEFAULT_TOOL") or "code"


def _parse_args(args):
    parser = argparse.ArgumentParser(prog="devit")
    parser.add_argument(
        "name",
        nargs="?",
        default=".",
        help="Target to open (default: current directory)",
    )
    parser.add_argument(
        "--background",
        "-b",
        dest="in_background",
        action="store_true",
        help="Don't activate the application (only works with subl)",
    )

    parser.set_defaults(tool=_DEFAULT_TOOL)
    tool = parser.add_mutually_exclusive_group()
    for item in _ToolChoice:
        help_text = f"Launch {item.value}"
        if item.name == _DEFAULT_TOOL:
            help_text += " (default)"
        tool.add_argument(
            f"--{item.name}",
            action="store_const",
            dest="tool",
            const=item.name,
            help=help_text,
        )

    return parser.parse_args(args)


def main(argv=None):
    options = _parse_args(argv)
    if options.tool != "subl" and options.in_background:
        raise argparse.ArgumentError(
            "only Sublime Text supports launching in background",
        )
    tool = _ToolChoice[options.tool].value
    command = [
        os.fspath(executables.find(tool)),
        *tool.iter_args(options.name, options.in_background),
    ]
    subprocess.call(command)
