"""
Primary entry point.

TODO:
  1) Get output of files that need to be transformed.
  2) Give a number, number of lines, packages, etc.
  3) Git hook that won't allow non python 2/3 code to be pushed.
"""
import argparse
import os
import subprocess

import sys

from futurizer import futurize_code


def get_diff_python_files(root, compare_branch='origin/master'):
    """
    :type root: str
    :type compare_branch: str
    :rtype: list of str
    """
    output = subprocess.check_output(['git', 'diff', '--name-only', compare_branch], cwd=root)
    files = output.strip().split('\n')
    return [os.path.join(root, f) for f in files if f.endswith('.py')]


def get_all_python_files(root):
    """
    :type root: str
    :rtype: list of str
    """
    python_files = []
    for sub_directory in [root]:
        for subdir, _, files in os.walk(os.path.join(root, sub_directory)):
            for file_name in files:
                if file_name.endswith('.py'):
                    python_files.append(os.path.join(subdir, file_name))
    return python_files


def get_python_files(diff=False):
    """
    :type diff: bool
    :rtype: list of str
    """
    if diff:
        python_files = get_diff_python_files(os.getcwd())
        if not python_files:
            print('No python files in diff.')
            sys.exit(0)
    else:
        python_files = get_all_python_files(os.getcwd())
    return python_files


def python3_lint(diff=False):
    """
    :type diff: bool
    """
    python_files = get_python_files(diff=diff)
    # Rules I probably want: fix_xrange
    # Rules I want to avoid: list(Dict.items())
    # `dict`: We want to avoid using this initially because it makes us do things like list(keys()), but without it
    # there is no diff for `iteritems` usages.
    # arguments = ['-0', '-x', 'absolute_import', '-n', '-o', '/tmp/linted', '-w'] + python_files
    arguments = ['-0', '-x', 'absolute_import', '-x', 'dict', '-n', '-o', '/tmp/linted', '-w'] + python_files
    result = futurize_code(arguments)
    if diff:
        # This is generally used in .githook; We need to exit with failure code if there are changes required.
        sys.exit(result)
    else:
        # This is generally used in CI implementations; We don't want to exit with a failure code if we
        # successfully linted.
        sys.exit(0)


def main():
    """
    Main entry point for package.
    """
    parser = argparse.ArgumentParser(description='Run the Py 2/3 coverage report.')
    parser.add_argument('--diff', action='store_true', default=False, help='Run report on the diff only.')
    args = parser.parse_args()
    python3_lint(diff=args.diff)


if __name__ == '__main__':
    main()
