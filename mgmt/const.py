import os


LINT_RESULTS_DIR_NAME = 'py2to3cov'
KILI_ROOT = os.getenv('KILIMANJARO')
RESULTS_DIR = '{KILI_ROOT}/{LINT_FILE_DIR}'.format(KILI_ROOT=KILI_ROOT, LINT_FILE_DIR=LINT_RESULTS_DIR_NAME)
DIFF_DIR = '{RESULTS_DIR}/diff'.format(RESULTS_DIR=RESULTS_DIR)


class Repository(object):
    """
    Does not inherit from constants to remove any kili dependencies.
    """
    KILIMANJARO = 'kilimanjaro'
    allowed = [KILIMANJARO]
