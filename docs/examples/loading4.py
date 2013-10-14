#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

import os
os.chdir(os.path.dirname(os.path.abspath(os.path.normpath(__file__))))

# BEGIN INCLUDE
from tdi import factory_memoize
from tdi import html

t1 = html.from_file('loading.html')
t2 = html.from_file('loading.html')

# t1 and t2 are different template objects here
print t1 is t2 # False

# 1) Tell the factory that we want memoized calls
html = html.replace(memoizer={})

# Wrap into the key provider
html = factory_memoize.MemoizedFactory(html)

t1 = html.from_file('loading.html')
t2 = html.from_file('loading.html')

# t1 and t2 are the same objects here
print t1 is t2 # True
