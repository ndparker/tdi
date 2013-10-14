#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<html>
<body>
<div tdi="some">
content <tdi tdi="-count" />
</div>
</body>
</html>
""".strip())

class Model(object):
    def render_some(self, node):
        print repr(node.render())
        print repr(node.render(decode=False))
        node.remove()

    def render_count(self, node):
        node.content = self.count = getattr(self, 'count', 0) + 1

print template.render_string(Model())
