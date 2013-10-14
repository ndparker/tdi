#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

import re as _re

from tdi import html
from tdi.tools import javascript

tpl = html.from_string("""
<a tdi="link" onclick="alert('__what__'); return false">Click me</a>
""".lstrip())
json = javascript.LiteralJSON(u'{"name": "Andr\xe9]]>"}')
class Model(object):
    def render_link(self, node):
        javascript.fill_attr(node, u'onclick', dict(
            what = u'Andr\xe9',
        ))
tpl.render(Model())

tpl = html.from_string("""
<a tdi="link" onclick="alert('__what__'); return false">Click me</a>
""".lstrip())
json = javascript.LiteralJSON(u'{"name": "Andr\xe9]]>"}')
class Model(object):
    def render_link(self, node):
        javascript.fill_attr(node, u'onclick', dict(
            what = json,
        ))
tpl.render(Model())

tpl = html.from_string("""
<meta charset=utf-8>
<a tdi="link" onclick="alert('__what__'); return false">Click me</a>
""".lstrip())
json = javascript.LiteralJSON(u'{"name": "Andr\xe9]]>"}')
class Model(object):
    def render_link(self, node):
        javascript.fill_attr(node, u'onclick', dict(
            what = json,
        ))
tpl.render(Model())

tpl = html.from_string("""
<meta charset=utf-8>
<a tdi="link" onclick="alert('__what__'); return false">Click me</a>
""".lstrip())
json = javascript.LiteralJSON(u'{"name": "Andr\xe9]]>"}')
class Model(object):
    def render_link(self, node):
        javascript.fill_attr(node, u'onclick', dict(
            what = json,
        ), as_json=False)
tpl.render(Model())

tpl = html.from_string("""
<meta charset=utf-8>
<a tdi="link" onclick="alert('@what@'); return false">Click me</a>
""".lstrip())
json = javascript.LiteralJSON(u'{"name": "Andr\xe9]]>"}')
class Model(object):
    def render_link(self, node):
        javascript.fill_attr(node, u'onclick', dict(
            what = json,
        ), pattern=ur'@(?P<name>[^@]+)@', as_json=False)
tpl.render(Model())

tpl = html.from_string("""
<meta charset=utf-8>
<a tdi="link" onclick="alert('@what@'); return false">Click me</a>
""".lstrip())
json = javascript.LiteralJSON(u'{"name": "Andr\xe9]]>"}')
class Model(object):
    def render_link(self, node):
        javascript.fill_attr(node, u'onclick', dict(
            what = json,
        ), pattern=_re.compile(ur'@(?P<name>[^@]+)@'), as_json=False)
tpl.render(Model())

tpl = html.from_string("""
<meta charset=utf-8>
<a tdi="link" onclick="alert('@what@'); return false">Click me</a>
""".lstrip())
json = javascript.LiteralJSON(u'{"name": "Andr\xe9]]>"}')
class Model(object):
    def render_link(self, node):
        javascript.fill_attr(node, u'onclick', dict(
            what = json,
        ), pattern=_re.compile(ur'@(?P<name>[^@]+)@'))
tpl.render(Model())
