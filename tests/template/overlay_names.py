#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<node tdi="item">
    <znode tdi:overlay="foo">
        <ynode tdi:overlay="bar"></ynode>
        <ynode tdi:overlay="<zonk"></ynode>
        <ynode tdi:overlay=">plenk"></ynode>
    </znode>
    <xnode tdi:overlay=">baz"></xnode>
</node>
""".lstrip())

print list(sorted(template.source_overlay_names))
print list(sorted(template.target_overlay_names))
