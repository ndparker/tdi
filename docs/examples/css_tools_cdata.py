#!/usr/bin/env python
# -*- coding: utf-8 -*-
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi.tools import css

print css.cdata("""
/*<![CDATA[*/
    body {font-family: sans-serif;}
/*]]>*/
""".strip())

