#!/usr/bin/env python
"""
Submitted by: Roland Sommer <roland.sommer@gmx.org>

segfault in tdi.c
"""
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

import os
from tdi import html

template = html.from_files([
    '_baselayout.html', 'results.html', '_widgets.html',
], basedir=os.path.dirname(os.path.abspath(__file__)))

for _ in xrange(10):
    template.render(startnode="resulttable")
print
