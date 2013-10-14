#!/usr/bin/env python
# -*- coding: utf-8 -*-
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi.tools import javascript

print javascript.escape_string(u"\n - é - € - \U0001d51e")
