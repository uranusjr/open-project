"""Smart-open a thing in Visual Studio Code.

This only works on Windows because I use Visual Studio Code on Windows.
"""

import argparse
import contextlib
import itertools
import os
import pathlib
import subprocess
import sys
import winreg

import fuzzywuzzy.fuzz


def parse_args(args):
    parser = argparse.ArgumentParser(prog='codeit')
    parser.add_argument(
        'name', nargs='?', default='.',
        help="File or directory to open (default is the current directory)",
    )
    return parser.parse_args(args)


FUZZY_FIND_THRESHOLD = 75


def find_workspace_here(path):
    for p in path.glob('*.code-workspace'):
        if fuzzywuzzy.fuzz.ratio(path.name, p.stem) > FUZZY_FIND_THRESHOLD:
            return p


def find_workspace_in_parent(path):
    for p in path.parent.glob('*.code-workspace'):
        if fuzzywuzzy.fuzz.ratio(path.name, p.stem) > FUZZY_FIND_THRESHOLD:
            return p


FIND_FUNCTIONS = [
    find_workspace_here,
    find_workspace_in_parent,
]


def find_workspace_to_open(path):
    for find in FIND_FUNCTIONS:
        found = find(path)
        if found:
            return found


def build_code_args(options):
    args = []
    path = pathlib.Path(options.name).resolve()
    if path.is_dir():
        workspace = find_workspace_to_open(path)
        if workspace:
            print(f'Opening {workspace}', file=sys.stderr)
            args.extend(('--new-window', str(workspace)))
        else:
            print(f'Opening {path}', file=sys.stderr)
            args.extend(('--new-window', str(path)))
    else:
        print(f'Opening {options.name}', file=sys.stderr)
        args.extend(('--new-window', options.name))
    return args


def find_code_cmd(directory):
    path = pathlib.Path(directory, 'code.cmd')
    if path.is_file() and os.access(path, os.X_OK):
        return path.resolve()
    return None


def find_code_in_path():
    directories = os.environ['PATH'].split(os.pathsep)
    for directory in directories:
        executable = find_code_cmd(directory)
        if executable:
            return executable
    return None


@contextlib.contextmanager
def open_key(*args):
    key = winreg.OpenKey(*args)
    yield key
    winreg.CloseKey(key)


def read_string(key, name):
    try:
        v, t = winreg.QueryValueEx(key, name)
    except FileNotFoundError:
        return None
    if t == 1:
        return v
    return None


def read_vscode_location(key):
    if read_string(key, 'Publisher') != 'Microsoft Corporation':
        return None
    display = read_string(key, 'DisplayName')
    if not display or not display.startswith('Microsoft Visual Studio Code'):
        return None
    return read_string(key, 'InstallLocation')


def find_code_in_registry():
    for hkey in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
        path = '\\'.join([
            'Software', 'Microsoft', 'Windows', 'CurrentVersion', 'Uninstall',
        ])
        with open_key(hkey, path) as pkey:
            for i in itertools.count():
                try:
                    name = winreg.EnumKey(pkey, i)
                except OSError:
                    break
                with open_key(pkey, name) as key:
                    location = read_vscode_location(key)
                    if not location:
                        continue
                    executable = find_code_cmd(pathlib.Path(location, 'bin'))
                    if executable:
                        return executable
    return None


def find_code():
    code = find_code_in_path() or find_code_in_registry()
    if not code:
        raise ValueError('code for VS Code not found on this system')
    return code


def main(args=None):
    options = parse_args(args)
    sys.exit(subprocess.call([
        os.environ['COMSPEC'],
        '/c',
        str(find_code()),
        *build_code_args(options),
    ]))


if __name__ == '__main__':
    main()
