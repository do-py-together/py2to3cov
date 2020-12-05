"""
Store and register the diff summary.
"""
from py2to3cov.mgmt.const import DIFF_DIR, ROOT


class DiffSummary(object):
    registry = {}

    def __init__(self, filename):
        self.filename = filename
        self.diff_lines = []
        self.__class__.registry[filename] = self

    def append_line(self, diff_line):
        self.diff_lines.append(diff_line)

    @property
    def line_count(self):
        """
        :rtype: int
        """
        with open('{root_dir}/{filename}'.format(root_dir=ROOT, filename=self.filename)) as original_file:
            line_count = len(original_file.readlines())
        return line_count

    @property
    def percent_coverage(self):
        """
        :rtype: float
        """
        if self.remove_line_count:
            return '%.2f%%' % (100 - round(100.0 * self.remove_line_count / self.line_count, 2))
        else:
            return '100%'

    @property
    def add_line_count(self):
        """
        :rtype: int
        """
        count = 0
        for line in self.diff_lines:
            if line[0] == '+':
                count += 1
        return count

    @property
    def remove_line_count(self):
        """
        :rtype: int
        """
        count = 0
        for line in self.diff_lines:
            if line[0] == '-':
                count += 1
        return count

    @classmethod
    def list_all(cls):
        """
        :rtype: Generator[(str, DiffSummary)]
        """
        for file_name in sorted(cls.registry):
            yield file_name, cls.registry[file_name]

    @property
    def href(self):
        """
        :rtype: str
        """
        if self.remove_line_count:
            return '{diff_dir}/{filename}.diff'.format(diff_dir=DIFF_DIR,
                                                       filename=self.filename)
        else:
            return 'javascript:void(null);'
