#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import html

# xml prolog
template = html.from_string(
    """<?xml version="1.0" encoding="latin-1"?>..."""
)
print template.encoding

# meta
template = html.from_string(
    """<html>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    </html>"""
)
print template.encoding

# meta HTML5
template = html.from_string(
    """<html>
        <meta charset="windows-1252">
    </html>"""
)
print template.encoding

# xml prolog + meta
template = html.from_string(
    """<?xml version="1.0" encoding="latin-1"?>
       <meta charset=utf-8>
    """
)
print template.encoding

# none
template = html.from_string("<html>...</html>")
print template.encoding
