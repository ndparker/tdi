#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import text
template = text.from_string("""
Hello [[name]],

[item]* some stuff[/item][:item]
[/:item]
""".strip())
template.render()
print
