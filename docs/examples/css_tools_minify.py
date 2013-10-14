#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi.tools import css

print css.minify(u"""
fieldset p {
    margin: 0.5em;
}
fieldset p span {
    float: right;
    display: inline-block;
    font-size: 0.8em;
}
""".lstrip())
