#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

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

# BEGIN INCLUDE
class Model(object):
    def __init__(self, page):
        self._page = page

    def render_menu(self, node):
        node("menu%d" % self._page).hiddenelement = True
#END INCLUDE

model = Model(page=2)
template.render(model)
