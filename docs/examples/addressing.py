#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import html
template = html.from_string("""
<html>
<body>
    <ul class="menu" tdi="menu">
        <li><a href="menu1" tdi="menu1">some menu item</a></li>
        <li><a href="menu2" tdi="menu2">Editing Content &amp; Attributes</a></li>
        <li><a href="menu3" tdi="menu3">Other menu item</a></li>
    </ul>
</body>
</html>
""")

class Model(object):
    def __init__(self, page):
        self._page = page

    def render_menu(self, node):
        if self._page == 1:
            node.menu1.hiddenelement = True
        elif self._page == 2:
            node.menu2.hiddenelement = True
        elif self._page == 3:
            node.menu3.hiddenelement = True

model = Model(page=2)
template.render(model)
