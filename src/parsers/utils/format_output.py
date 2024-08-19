# -*- coding: utf-8 -*-
import inspect


class AutoIndent(object):
    """Indent debug output based on function call depth."""

    def __init__(self, stream, depth=len(inspect.stack())):
        """
        stream is something like sys.stdout.
        depth is to compensate for stack depth.
        The default is to get current stack depth when class created.

        """
        self.stream = stream
        self.depth = depth

    def indent_level(self):
        return len(inspect.stack()) - self.depth

    def write(self, data):
        indentation = '  ' * self.indent_level()

        def indent(l):
            if l:
                return indentation + l
            else:
                return l

        data = '\n'.join([indent(line) for line in data.split('\n')])
        self.stream.write(data)

    def flush(self):
        self.stream.flush()

