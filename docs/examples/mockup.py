#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import html
template = html.from_string("""
<ul>
<li tdi="item">1st</li>
<li tdi="-">2nd</li>
<li tdi="-">3rd</li>
</ul>
""")
template.render()
