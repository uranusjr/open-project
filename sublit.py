"""Smart-open a thing in Sublime Text.
"""

import argparse
import os
import pathlib
import re
import subprocess

import fuzzywuzzy.fuzz


def parse_args(args):
    parser = argparse.ArgumentParser(prog='sublit')
    parser.add_argument(
        'name', help="File or directory to open",
    )
    parser.add_argument(
        '--background', '-b', dest='in_background', action='store_true',
        help="Don't activate the application",
    )
    if not args:    # Display help if no arguments are passed.
        parser.print_help()
        try:
            EX_USAGE = os.EX_USAGE
        except AttributeError:  # Windows.
            EX_USAGE = 1
        parser.exit(EX_USAGE)
    return parser.parse_args(args)


FUZZY_FIND_THREASHOLD = 0.75


def find_project_here(path):
    for p in path.glob('*.sublime-project'):
        if fuzzywuzzy.fuzz.ratio(path.name, p.stem) > FUZZY_FIND_THREASHOLD:
            return p


def find_project_in_parent(path):
    for p in path.parent.glob('*.sublime-project'):
        if fuzzywuzzy.fuzz.ratio(path.name, p.stem) > FUZZY_FIND_THREASHOLD:
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
    path = pathlib.Path(name)
    if path.is_dir():
        project = find_project_to_open(path)
        if project:
            args.extend(('--project', str(project)))
        else:
            args.extend(('--new-window', str(path)))
    else:
        args.extend(('--new-window', options.name))
    return args


def find_subl_in_path():
    directories = os.environ['PATH'].split(os.pathsep)
    for directory in directories:
        path = pathlib.Path(directory, 'subl')
        if path.if_file() and os.access(path, os.X_OK):
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


def main(argv):
    options = parse_args(argv[1:])
    os.execl(str(find_subl()), 'subl', *build_subl_args(options))


if __name__ == '__main__':
    import sys
    main(sys.argv)
