"""
Store and register the diff summary.
"""
from mgmt.const import KILI_ROOT


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
        with open('{root_dir}/{filename}'.format(root_dir=KILI_ROOT, filename=self.filename)) as original_file:
            line_count = len(original_file.readlines())
        return line_count

    @property
    def percent_coverage(self):
        """
        :rtype: float
        """
        return '%.2f%%' % round(100.0 * self.remove_line_count / self.line_count, 2)

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
        for file_name, instance_ref in cls.registry.items():
            yield file_name, instance_ref
