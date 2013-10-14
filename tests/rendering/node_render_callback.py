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
        def callback(node, *fixed):
            node['fixed'] = ' '.join(map(str, fixed))
        print repr(node.render(callback))
        print repr(node.render(callback, decode=False))
        print repr(node.render(callback, 1, 2, 'a'))
        print repr(node.render(callback, 3, 4, 'b', decode=False))

    def render_count(self, node):
        node.content = self.count = getattr(self, 'count', 0) + 1

print template.render_string(Model())
