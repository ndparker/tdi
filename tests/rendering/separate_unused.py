#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

import warnings

from tdi import NodeWarning
from tdi import html

warnings.filterwarnings("error", category=NodeWarning)

try:
    template = html.from_string("""
    <node tdi="item">
        <node tdi="nested">
            <node tdi="subnested"></node>
        </node><tdi tdi=":-nested">
        </tdi><tdi tdi=":-nested2">
        </tdi>
    </node>
    """.lstrip())
except NodeWarning, e:
    print "OK: Nodewarning: %s" % (str(e),)
