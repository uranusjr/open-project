"""Smart-open a thing in Visual Studio Code.

This only works on Windows because I use Visual Studio Code on Windows.
"""

import argparse
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


# From https://github.com/Microsoft/vscode/issues/37807#issuecomment-343493092.
CODE_INSTALLER_IDS = [
    '1287CAD5-7C8D-410D-88B9-0D1EE4A83FF2',     # 64bit insider.
    'EA457B21-F73E-494C-ACAB-524FDE069978',     # 64bit stable.
    'C26E74D1-022E-4238-8B9D-1E7564A36CC9',     # 32bit insider.
    'F8A2A208-72B3-4D61-95FC-8A65D340689B',     # 32bit stable.
]


def find_code_in_registry():
    code = None
    for hkey in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
        for iid in CODE_INSTALLER_IDS:
            path = '\\'.join([
                'Software', 'Microsoft', 'Windows', 'CurrentVersion',
                'Uninstall', '{{{}}}_is1'.format(iid),
            ])
            try:
                key = winreg.OpenKey(hkey, path)
            except FileNotFoundError:
                continue
            try:
                value, t = winreg.QueryValueEx(key, 'InstallLocation')
            except FileNotFoundError:
                pass
            else:
                if t == 1:
                    executable = find_code_cmd(pathlib.Path(value, 'bin'))
                    if executable:
                        code = executable
            winreg.CloseKey(key)
            if code:
                return code
    return code


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
