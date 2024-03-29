"""
See: `libfuturize.main`
"""
from __future__ import (absolute_import, print_function, unicode_literals)

import json
import logging
import optparse
import os
import shutil
import sys
from lib2to3 import refactor
from lib2to3.main import warn

import future.utils
from do_py import DataObject, R
from do_py.common.managed_list import ManagedList
from dominate import document
from dominate.tags import a, b, h1, p, table, tbody, td, th, thead, tr
from future import __version__
from libfuturize.fixes import (lib2to3_fix_names_stage1,
                               lib2to3_fix_names_stage2,
                               libfuturize_fix_names_stage1,
                               libfuturize_fix_names_stage2)

from py2to3cov.data_model.diff_summary import DiffSummary
from py2to3cov.futurizer.refactoring_tool import FileRefactoringTool
from py2to3cov.mgmt.const import DIFF_DIR, RESULTS_DIR


fixer_pkg = 'libfuturize.fixes'


class TestFailure(DataObject):
    _restrictions = {
        'type': R.STR,
        'message': R.STR,
        }


class TestCase(DataObject):
    _restrictions = {
        'file': R.STR,
        'failure': R(TestFailure, type(None))
        }


class TestReport(DataObject):
    _restrictions = {
        'testsuite': ManagedList(TestCase)
        }

    def to_xml(self):
        """
        :rtype: str
        """
        return '<testsuite>%s</testsuite>' % ''.join(test_case.to_xml() for test_case in self.testsuite)


def futurize_code(args=None):
    """Main program.

    Args:
        fixer_pkg: the name of a package where the fixers are located.
        args: optional; a list of command line arguments. If omitted,
              sys.argv[1:] is used.

    Returns a suggested exit status (0, 1, 2).
    """

    # Set up option parser
    parser = optparse.OptionParser(usage="futurize [options] file|dir ...")
    parser.add_option("-V", "--version", action="store_true",
                      help="Report the version number of futurize")
    parser.add_option("-a", "--all-imports", action="store_true",
                      help="Add all __future__ and future imports to each module")
    parser.add_option("-1", "--stage1", action="store_true",
                      help="Modernize Python 2 code only; no compatibility with Python 3 (or dependency on ``future``)")
    parser.add_option("-2", "--stage2", action="store_true",
                      help="Take modernized (stage1) code and add a dependency on ``future`` to provide Py3 compatibility.")
    parser.add_option("-0", "--both-stages", action="store_true",
                      help="Apply both stages 1 and 2")
    parser.add_option("-u", "--unicode-literals", action="store_true",
                      help="Add ``from __future__ import unicode_literals`` to implicitly convert all unadorned string literals '' into unicode strings")
    parser.add_option("-f", "--fix", action="append", default=[],
                      help="Each FIX specifies a transformation; default: all.\nEither use '-f division -f metaclass' etc. or use the fully-qualified module name: '-f lib2to3.fixes.fix_types -f libfuturize.fixes.fix_unicode_keep_u'")
    parser.add_option("-j", "--processes", action="store", default=1,
                      type="int", help="Run 2to3 concurrently")
    parser.add_option("-x", "--nofix", action="append", default=[],
                      help="Prevent a fixer from being run.")
    parser.add_option("-l", "--list-fixes", action="store_true",
                      help="List available transformations")
    parser.add_option("-p", "--print-function", action="store_true",
                      help="Modify the grammar so that print() is a function")
    parser.add_option("-v", "--verbose", action="store_true",
                      help="More verbose logging")
    parser.add_option("--no-diffs", action="store_true",
                      help="Don't show diffs of the refactoring")
    parser.add_option("-w", "--write", action="store_true",
                      help="Write back modified files")
    parser.add_option("-n", "--nobackups", action="store_true", default=False,
                      help="Don't write backups for modified files.")
    parser.add_option("-o", "--output-dir", action="store", type="str",
                      default="", help="Put output files in this directory "
                                       "instead of overwriting the input files.  Requires -n. "
                                       "For Python >= 2.7 only.")
    parser.add_option("-W", "--write-unchanged-files", action="store_true",
                      help="Also write files even if no changes were required"
                           " (useful with --output-dir); implies -w.")
    parser.add_option("--add-suffix", action="store", type="str", default="",
                      help="Append this string to all output filenames."
                           " Requires -n if non-empty. For Python >= 2.7 only."
                           "ex: --add-suffix='3' will generate .py3 files.")

    # Parse command line arguments
    flags = {}
    refactor_stdin = False
    options, args = parser.parse_args(args)

    if options.write_unchanged_files:
        flags["write_unchanged_files"] = True
        if not options.write:
            warn("--write-unchanged-files/-W implies -w.")
        options.write = True
    # If we allowed these, the original files would be renamed to backup names
    # but not replaced.
    if options.output_dir and not options.nobackups:
        parser.error("Can't use --output-dir/-o without -n.")
    if options.add_suffix and not options.nobackups:
        parser.error("Can't use --add-suffix without -n.")

    if not options.write and options.no_diffs:
        warn("not writing files and not printing diffs; that's not very useful")
    if not options.write and options.nobackups:
        parser.error("Can't use -n without -w")
    if "-" in args:
        refactor_stdin = True
        if options.write:
            print("Can't write to stdin.", file=sys.stderr)
            return 2
    # Is this ever necessary?
    if options.print_function:
        flags["print_function"] = True

    # Set up logging handler
    level = logging.DEBUG if options.verbose else logging.INFO
    logging.basicConfig(format='%(name)s: %(message)s', level=level)
    logger = logging.getLogger('libfuturize.main')

    if options.stage1 or options.stage2:
        assert options.both_stages is None
        options.both_stages = False
    else:
        options.both_stages = True

    avail_fixes = set()

    if options.stage1 or options.both_stages:
        avail_fixes.update(lib2to3_fix_names_stage1)
        avail_fixes.update(libfuturize_fix_names_stage1)
    if options.stage2 or options.both_stages:
        avail_fixes.update(lib2to3_fix_names_stage2)
        avail_fixes.update(libfuturize_fix_names_stage2)

    if options.unicode_literals:
        avail_fixes.add('libfuturize.fixes.fix_unicode_literals_import')

    if options.version:
        print(__version__)
        return 0
    if options.list_fixes:
        print("Available transformations for the -f/--fix option:")
        # for fixname in sorted(refactor.get_all_fix_names(fixer_pkg)):
        for fixname in sorted(avail_fixes):
            print(fixname)
        if not args:
            return 0
    if not args:
        print("At least one file or directory argument required.",
              file=sys.stderr)
        print("Use --help to show usage.", file=sys.stderr)
        return 2

    unwanted_fixes = set()
    for fix in options.nofix:
        if ".fix_" in fix:
            unwanted_fixes.add(fix)
        else:
            # Infer the full module name for the fixer.
            # First ensure that no names clash (e.g.
            # lib2to3.fixes.fix_blah and libfuturize.fixes.fix_blah):
            found = [f for f in avail_fixes
                     if f.endswith('fix_{0}'.format(fix))]
            if len(found) > 1:
                print("Ambiguous fixer name. Choose a fully qualified "
                      "module name instead from these:\n" +
                      "\n".join("  " + myf for myf in found),
                      file=sys.stderr)
                return 2
            elif len(found) == 0:
                print("Unknown fixer. Use --list-fixes or -l for a list.",
                      file=sys.stderr)
                return 2
            unwanted_fixes.add(found[0])

    extra_fixes = set()
    if options.all_imports:
        if options.stage1:
            prefix = 'libfuturize.fixes.'
            extra_fixes.add(prefix +
                            'fix_add__future__imports_except_unicode_literals')
        else:
            # In case the user hasn't run stage1 for some reason:
            prefix = 'libpasteurize.fixes.'
            extra_fixes.add(prefix + 'fix_add_all__future__imports')
            extra_fixes.add(prefix + 'fix_add_future_standard_library_import')
            extra_fixes.add(prefix + 'fix_add_all_future_builtins')
    explicit = set()
    if options.fix:
        all_present = False
        for fix in options.fix:
            if fix == 'all':
                all_present = True
            else:
                if ".fix_" in fix:
                    explicit.add(fix)
                else:
                    # Infer the full module name for the fixer.
                    # First ensure that no names clash (e.g.
                    # lib2to3.fixes.fix_blah and libfuturize.fixes.fix_blah):
                    found = [f for f in avail_fixes
                             if f.endswith('fix_{0}'.format(fix))]
                    if len(found) > 1:
                        print("Ambiguous fixer name. Choose a fully qualified "
                              "module name instead from these:\n" +
                              "\n".join("  " + myf for myf in found),
                              file=sys.stderr)
                        return 2
                    elif len(found) == 0:
                        print("Unknown fixer. Use --list-fixes or -l for a list.",
                              file=sys.stderr)
                        return 2
                    explicit.add(found[0])
        if len(explicit & unwanted_fixes) > 0:
            print("Conflicting usage: the following fixers have been "
                  "simultaneously requested and disallowed:\n" +
                  "\n".join("  " + myf for myf in (explicit & unwanted_fixes)),
                  file=sys.stderr)
            return 2
        requested = avail_fixes.union(explicit) if all_present else explicit
    else:
        requested = avail_fixes.union(explicit)
    fixer_names = (requested | extra_fixes) - unwanted_fixes

    input_base_dir = os.path.commonprefix(args)
    if (input_base_dir and not input_base_dir.endswith(os.sep)
            and not os.path.isdir(input_base_dir)):
        # One or more similar names were passed, their directory is the base.
        # os.path.commonprefix() is ignorant of path elements, this corrects
        # for that weird API.
        input_base_dir = os.path.dirname(input_base_dir)
    # if options.output_dir:
    #     input_base_dir = input_base_dir.rstrip(os.sep)
    #     logger.info('Output in %r will mirror the input directory %r layout.',
    #                 options.output_dir, input_base_dir)

    # Initialize the refactoring tool
    if future.utils.PY26:
        extra_kwargs = {}
    else:
        extra_kwargs = {
            'append_suffix': options.add_suffix,
            'output_dir': options.output_dir,
            'input_base_dir': input_base_dir,
            }

    # Remove results directory.
    if os.path.isdir(RESULTS_DIR):
        shutil.rmtree(RESULTS_DIR)
    os.mkdir(RESULTS_DIR)

    if os.path.isdir(DIFF_DIR):
        shutil.rmtree(DIFF_DIR)
    os.mkdir(DIFF_DIR)

    # We override their RefactoringTool with `FileRefactoringTool`
    rt = FileRefactoringTool(
        sorted(fixer_names), flags, sorted(explicit),
        options.nobackups, not options.no_diffs,
        **extra_kwargs)

    # Refactor all files and directories passed as arguments
    if not rt.errors:
        if refactor_stdin:
            rt.refactor_stdin()
        else:
            try:
                rt.refactor(args, options.write, None,
                            options.processes)
            except refactor.MultiprocessingUnsupported:
                assert options.processes > 1
                print("Sorry, -j isn't supported on this platform.", file=sys.stderr)
                return 1
        rt.summarize()

    # This is our own custom html reporting.
    table_body = tbody()
    remove_line_count_total = 0
    with table_body:
        for file_name, file_summary in DiffSummary.list_all():
            with tr():
                td(a(file_name, href=file_summary.href))
                td(file_summary.add_line_count, style="text-align:right")
                td(file_summary.remove_line_count, style="text-align:right")
                td(file_summary.percent_coverage, style="text-align:right")
                remove_line_count_total += file_summary.remove_line_count

    with document(title='2/3 Summary') as doc:
        h1('2/3 Summary', style='padding: 0 40px;')
        p('Total lines that need to be removed:', style='padding: 0 40px;').add(b(remove_line_count_total))
        summary_table = table(width='100%', style="padding: 20px 40px; margin: 0 auto;")
        with summary_table.add(thead()):
            with tr():
                th('File Name', style="text-align:left")
                th('Add Lines', style="text-align:right")
                th('Remove Lines', style="text-align:right")
                th('Coverage %', style="text-align:right")
            summary_table.add(table_body)

    with open('{results_dir}/summary.html'.format(results_dir=RESULTS_DIR), 'w+') as summary_file:
        summary_file.write(doc.render())

    # Write a machine readable report that can be parsed later.
    json_report = {
        'summary': {
            'remove_line_count_total': remove_line_count_total
            },
        'files': [
            {
                'file_name': file_name,
                'add_line_count': file_summary.add_line_count,
                'remove_line_count': file_summary.remove_line_count,
                'percent_coverage': file_summary.percent_coverage,
                } for file_name, file_summary in DiffSummary.list_all()
            ]
        }
    json.dump(json_report, open('{results_dir}/report.json'.format(results_dir=RESULTS_DIR), 'w+'))

    # Return error status (0 if rt.errors is zero)
    return int(bool(rt.errors))
