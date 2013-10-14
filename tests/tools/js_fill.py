#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

import re as _re

from tdi import html
from tdi.tools import javascript

tpl = html.from_string("""
<script tdi="script">
    var count = __a__;
    var name = '__b__';
    var param = __c__;
</script>
""".lstrip())
json = javascript.LiteralJSON(u'{"name": "Andr\xe9]]>"}')
class Model(object):
    def render_script(self, node):
        javascript.fill(node, dict(
            a=10,
            b=u'Andr\xe9',
            c=json,
        ))
tpl.render(Model())

tpl = html.from_string("""
<meta charset=utf-8>
<script tdi="script">
    var count = __a__;
    var name = '__b__';
    var param = __c__;
</script>
""".lstrip())
json = javascript.LiteralJSON(u'{"name": "Andr\xe9]]>"}')
class Model(object):
    def render_script(self, node):
        javascript.fill(node, dict(
            a=10,
            b=u'Andr\xe9',
            c=json,
        ))
tpl.render(Model())

tpl = html.from_string("""
<meta charset=utf-8>
<script tdi="script">
    var count = __a__;
    var name = '__b__';
    var param = __c__;
</script>
""".lstrip())
json = javascript.LiteralJSON(u'{"name": "Andr\xe9]]>"}')
class Model(object):
    def render_script(self, node):
        javascript.fill(node, dict(
            a=10,
            b=u'Andr\xe9',
            c=json,
        ), as_json=False)
tpl.render(Model())

tpl = html.from_string("""
<meta charset=utf-8>
<script tdi="script">
    var count = @a@;
    var name = '@b@';
    var param = @c@;
</script>
""".lstrip())
json = javascript.LiteralJSON(u'{"name": "Andr\xe9]]>"}')
class Model(object):
    def render_script(self, node):
        javascript.fill(node, dict(
            a=10,
            b=u'Andr\xe9',
            c=json,
        ), pattern=ur'@(?P<name>[^@]+)@')
tpl.render(Model())

tpl = html.from_string("""
<meta charset=utf-8>
<script tdi="script">
    var count = @a@;
    var name = '@b@';
    var param = @c@;
</script>
""".lstrip())
json = javascript.LiteralJSON(u'{"name": "Andr\xe9]]>"}')
class Model(object):
    def render_script(self, node):
        javascript.fill(node, dict(
            a=10,
            b=u'Andr\xe9',
            c=json,
        ), pattern=_re.compile(ur'@(?P<name>[^@]+)@'))
tpl.render(Model())

tpl = html.from_string("""
<meta charset=utf-8>
<script tdi="script">
    var count = @a@;
    var name = '@b@';
    var param = @c@;
</script>
""".lstrip())
json = javascript.LiteralJSON(u'{"name": "Andr\xe9]]>"}')
class Model(object):
    def render_script(self, node):
        javascript.fill(node, dict(
            a=10,
            b=u'Andr\xe9',
            c=json,
        ), pattern=ur'@(?P<name>[^@]+)@', as_json=False)
tpl.render(Model())
