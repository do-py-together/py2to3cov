import os


LINT_RESULTS_DIR_NAME = 'py2to3cov-reports'
ROOT = os.getcwd()
RESULTS_DIR = '{ROOT}/{LINT_FILE_DIR}'.format(ROOT=ROOT, LINT_FILE_DIR=LINT_RESULTS_DIR_NAME)
DIFF_DIR = '{RESULTS_DIR}/diff'.format(RESULTS_DIR=RESULTS_DIR)
