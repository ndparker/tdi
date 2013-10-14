#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import html
template = html.from_string("""
<html>
<body>
    <p>My fruit salad contains <tdi tdi="-fruit">Apples</tdi><tdi
    tdi=":-fruit">, </tdi>.</p>
</body>
</html>
""".lstrip())

class Model(object):
    def __init__(self, fruits):
        self._fruits = fruits

    def render_fruit(self, node):
        node.repeat(self.repeat_fruit, self._fruits, len(fruits) - 2)

    def repeat_fruit(self, node, fruit, last_sep_idx):
        node.content = fruit

    def separate_fruit(self, node, last_sep_idx):
        if node.ctx[0] == last_sep_idx:
            node.content = u' and '


fruits = [
    u'apples', u'pears', u'bananas', u'pineapples',
]
model = Model(fruits)
template.render(model)
