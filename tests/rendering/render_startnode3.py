#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<anode tdi="level1">
    <bnode tdi:scope="bar">
        <node tdi="nested">
            <cnode tdi:scope="baz" tdi="subnested">sup.</cnode>
        </node>
    </bnode>
</anode>
""".lstrip())

template.render(startnode='subnested')
print
