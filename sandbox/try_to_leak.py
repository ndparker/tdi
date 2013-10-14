#!/usr/bin/env python

import time
import sys
from tdi.template import html

tpl = html.from_string("""
<x>
<y tdi="zonk">
<z tdi="zapp">
</z>
</y>
</x>
""")

class Model(object):

    def render_zonk(self, node):
        node.repeat(None, xrange(10000))

    def render_zapp(self, node):
        node.content = node.ctx[1]


idx = 0
while 1:
    m = Model()
    tpl.render_string(m)
    idx += 1
    if idx >= 10:
        sys.stdout.write(".")
        sys.stdout.flush()
        idx = 0
