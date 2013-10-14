#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<?xml version="1.0" encoding="utf-8" ?>
<node>
    <xnode tdi="foo"></xnode>
</node>
""".lstrip())

class Model(object):
    def render_foo(self, node):
        try:
            node.raw[u'b\xe9lah'] = 'blargh'
        except UnicodeError:
            node.raw[u'blah'] = 'blargh'

template.render(Model())
