"""Smart-open a thing in Sublime Text.

This only works on macOS because I use Sublime Text on macOS.
"""

import argparse
import os
import pathlib
import re
import subprocess
import sys

import fuzzywuzzy.fuzz


def parse_args(args):
    parser = argparse.ArgumentParser(prog='sublit')
    parser.add_argument(
        'name', nargs='?', default='.',
        help="File or directory to open (default is the current directory)",
    )
    parser.add_argument(
        '--background', '-b', dest='in_background', action='store_true',
        help="Don't activate the application",
    )
    return parser.parse_args(args)


FUZZY_FIND_THRESHOLD = 75


def find_project_here(path):
    for p in path.glob('*.sublime-project'):
        if fuzzywuzzy.fuzz.ratio(path.name, p.stem) > FUZZY_FIND_THRESHOLD:
            return p


def find_project_in_parent(path):
    for p in path.parent.glob('*.sublime-project'):
        if fuzzywuzzy.fuzz.ratio(path.name, p.stem) > FUZZY_FIND_THRESHOLD:
            return p


FIND_FUNCTIONS = [
    find_project_here,
    find_project_in_parent,
]


def find_project_to_open(path):
    for find in FIND_FUNCTIONS:
        found = find(path)
        if found:
            return found


OPEN_NAME_PATTNER = re.compile(
    r'''
    ^
    ([^:]+)         # File/directory name.
    (?:
        :\d+        # Line number.
        (?::\d+)?   # Column number.
    )?
    $
    ''',
    re.VERBOSE,
)


def build_subl_args(options):
    args = []
    if options.in_background:
        args.append('--background')
    match = OPEN_NAME_PATTNER.match(options.name)
    if not match:
        name = options.name
    else:
        name = match.group(1)
    path = pathlib.Path(name).resolve()
    if path.is_dir():
        project = find_project_to_open(path)
        if project:
            print(f'Opening {project}', file=sys.stderr)
            args.extend(('--project', str(project)))
        else:
            print(f'Opening {path}', file=sys.stderr)
            args.extend(('--new-window', str(path)))
    else:
        print(f'Opening {options.name}', file=sys.stderr)
        args.extend(('--new-window', options.name))
    return args


def find_subl_in_path():
    directories = os.environ['PATH'].split(os.pathsep)
    for directory in directories:
        path = pathlib.Path(directory, 'subl')
        if path.is_file() and os.access(path, os.X_OK):
            return path.resolve()
    return None


def find_subl_with_mdfind():
    app = subprocess.check_output(
        ['/usr/bin/mdfind', 'kMDItemCFBundleIdentifier=com.sublimetext.3'],
        encoding='utf-8',
    ).strip()
    if not app:
        return None
    path = pathlib.Path(app, 'Contents', 'SharedSupport', 'bin', 'subl')
    return path.resolve()


def find_subl():
    subl = find_subl_in_path() or find_subl_with_mdfind()
    if not subl:
        raise ValueError('subl for Sublime Text 3 not found on this system')
    return subl


def main(args=None):
    options = parse_args(args)
    os.execl(str(find_subl()), 'subl', *build_subl_args(options))


if __name__ == '__main__':
    main()
