import functools
import numbers


sep = '  '


class MathprogWriter(object):
    def __init__(self, output):
        self.w = output.write

    def wparam(self, name):
        self.w(f"param {name} :=\n")

    def wset(self, name):
        self.w(f"set {name} := \n")

    def wset_values(self, values):
        for v in values:
            self.w(sep + v)
        if values:
            self.w(';\n')

    def wlist(self, values, evaluator, end_line=True, first_level=True):
        for value in values:
            rendered_value = f"[{value}]" if first_level else value
            self.w(sep + rendered_value + sep + str(evaluator(value)))
        if end_line:
            self.w(';\n')

    def wmatrix(self, rows, colums, evaluator):
        for n1 in rows:
            self.w(sep + f"[{n1}, *]")
            self.wlist(
                colums,
                functools.partial(evaluator, n1),
                end_line=False,
                first_level=False,
            )
            self.w(n1 == rows[-1] and ';' or '' + '\n')
        if rows and colums:
            self.w('\n')

    def wcomment(self, comment):
        self.w(f'/* {comment} */\n')

    def br(self):
        self.w('\n')

    def wdata(self):
        self.w('data;\n')

    def wend(self):
        self.w('end;\n')
