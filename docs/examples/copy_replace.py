#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import NodeNotFoundError
from tdi import html
template = html.from_string("""
<html>
<body>
    <div tdi="content">
        <div tdi="page_1">
            This is page 1
        </div>
        <div tdi="page_2">
            This is page 2
        </div>
    </div>
</body>
</html>
""")

class Model(object):
    def __init__(self, page):
        self._page = page

    def render_content(self, node):
        try:
            page, number = node("page_%s" % self._page), self._page
        except NodeNotFoundError:
            page, number = node.page_1, 1
        node.replace(self.render_page, page, number)

    def render_page(self, node, page_no):
        node['title'] = u"Page %s" % page_no


model = Model(page=2)
template.render(model)
model = Model(page=10)
template.render(model)
