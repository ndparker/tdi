#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html
from tdi.tools import css

html = html.replace(eventfilters=[css.MinifyFilter])

tpl = html.from_string("""
<html>
<style><!--
--></style>
<style><!--
a b c{
    foo: bar;
    baz: blub;
}
--></style>
<style tdi="bar"><!--
--></style>
</html>
""".lstrip())

tpl.render()
