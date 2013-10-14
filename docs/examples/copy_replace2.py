#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import html
template = html.from_string("""
<html>
<body>
    <ul tdi="tree">
        <li tdi="*item"><a tdi="*link" href=""></a>
        <tdi tdi="*-next" />
        </li>
    </ul>
</body>
</html>
""")

class Model(object):
    def __init__(self, tree):
        self._tree = tree

    def render_tree(self, node):
        tree_node = node.copy()
        def level(node, (title, tree)):
            node.link['href'] = u'/%s/' % title
            node.link.content = title
            if tree:
                node.next.replace(None, tree_node).item.repeat(level, tree)
        node.item.repeat(level, self._tree)


tree = (
    (u'first', (
        (u'first-first', ()),
        (u'first-second', (
            (u'first-second-first', ()),
        )),
    )),
    (u'second!', (
        (u'second-first', ()),
    )),
    (u'third', ()),
)
model = Model(tree=tree)
template.render(model)
