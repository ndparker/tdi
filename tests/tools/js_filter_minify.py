#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html
from tdi.tools import javascript

html = html.replace(eventfilters=[javascript.MinifyFilter])

tpl = html.from_string("""
<html>
<script src="foo"></script>
<script><!--
//--></script>
<script><!--
var x=1;
var y = 2;
alert( x + y );
//--></script>
<script tdi="bar"><!--
--></script>
</html>
""".lstrip())

tpl.render()
