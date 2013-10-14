#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<node>
    <xnode></xnode>
</node>
""".lstrip())

print template
print template.tree
template.render()
