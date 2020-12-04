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
from mgmt.const import KILI_ROOT, Repository


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
    python_files = [os.path.join(root, 'kilimanjaro.py')]
    # for sub_directory in ['kilimanjaro_src', 'testing', 'assets']:
    for sub_directory in []:
        for subdir, _, files in os.walk(os.path.join(root, sub_directory)):
            for file_name in files:
                if file_name.endswith('.py'):
                    python_files.append(os.path.join(subdir, file_name))
    return python_files


def python3_lint(diff=False, repository=Repository.KILIMANJARO):
    """
    :type diff: bool
    :type repository: str
    """
    assert repository in Repository.allowed, 'Invalid repository. %s is not supported by py2to3cov.' % repository
    if diff:
        python_files = get_diff_python_files(KILI_ROOT)
        if not python_files:
            print('No python files in diff.')
            sys.exit(0)
    else:
        python_files = get_all_python_files(KILI_ROOT)

    # Rules I probably want: fix_xrange
    # Rules I want to avoid: list(Dict.items())
    # `dict`: We want to avoid using this initially because it makes us do things like list(keys()), but without it
    # there is no diff for `iteritems` usages.
    # arguments = ['-0', '-x', 'absolute_import', '-n', '-o', '/tmp/linted', '-w'] + python_files
    arguments = ['-0', '-x', 'absolute_import', '-x', 'dict', '-n', '-o', '/tmp/linted', '-w'] + python_files
    result = futurize_code(arguments)
    sys.exit(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the Py 2/3 coverage report.')
    parser.add_argument('--diff', action='store_true', default=False, help='Run report on the diff only.')
    parser.add_argument('--repo',
                        default=Repository.KILIMANJARO,
                        help='What repo to run the report for.')
    args = parser.parse_args()
    python3_lint(diff=args.diff, repository=args.repo)
