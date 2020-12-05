import os
from lib2to3.main import StdoutRefactoringTool, diff_texts

from py2to3cov.data_model.diff_summary import DiffSummary
from py2to3cov.mgmt.const import DIFF_DIR, ROOT


class FileRefactoringTool(StdoutRefactoringTool):
    """
    Override the original factoring tool in order to write to a file instead of printing to the console.
    """

    def write_file(self, new_text, filename, old_text, encoding):
        pass

    def print_output(self, old, new, filename, equal):
        filename = filename.replace(ROOT + '/', '')
        if equal:
            DiffSummary(filename)
        else:
            if self.show_diffs:
                diff_lines = diff_texts(old, new, filename)
                # Create the directories needed to create the files in the diff directory.
                dirs = ''
                for subdir in filename.split('/')[:-1]:
                    dirs += '/' + subdir
                    full_dir = '{diff_dir}{subdir}'.format(diff_dir=DIFF_DIR, subdir=dirs)
                    if not os.path.isdir(full_dir):
                        os.mkdir(full_dir)

                diff_file_name = '{diff_dir}/{filename}.diff'.format(diff_dir=DIFF_DIR, filename=filename)
                diff_summary = DiffSummary(filename)
                with open(diff_file_name, 'w+') as diff_file:
                    for line in diff_lines:
                        diff_file.write(line + '\n')
                        diff_summary.append_line(line)
                if diff_summary.line_count:
                    self.errors.append(('{filename}: Add {add}, remove {remove}'.format(
                        filename=filename,
                        add=diff_summary.add_line_count,
                        remove=diff_summary.remove_line_count
                        ), (), {}))
