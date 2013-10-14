#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.model_adapters import RenderAdapter
from tdi import html

template = html.from_string("""
<anode tdi="level1">
    <node tdi="-nested" tdi:scope="foo.bar" tdi:overlay="ov">
        <xnode tdi="a" tdi:scope="baz"></xnode>
    </node>
    <ynode tdi="-:nested">lalala</ynode>
</anode>
""".lstrip()).overlay(html.from_string("""
<znode tdi:scope="zonk">
    <widget tdi:overlay="ov">widget!</widget>
</znode>
""".lstrip()))

template.render(None, adapter=RenderAdapter.for_prerender)
