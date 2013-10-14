#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import text
template = text.from_string(r"""
[tdi="xxx" tdi:overlay="foo" myown="hey\\!\"" another=yo!],
""".strip())

class Model(object):
    def render_xxx(self, node):
        print node['myown']
        print node['another']

template.render_string(Model())
