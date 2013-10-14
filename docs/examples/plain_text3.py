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
        decode = node.raw.decoder.attribute
        print decode(node.raw['myown']).encode('utf-8')
        print decode(node.raw['another']).encode('utf-8')

template.render_string(Model())
