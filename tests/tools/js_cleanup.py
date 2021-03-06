#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.tools import javascript

x = javascript.cleanup(u"""<!-- script1
//-->""")
print repr(x)

x = javascript.cleanup("""<!-- script1
//-->""")
print repr(x)

x = javascript.cleanup("""<!-- script1 - \xc3\xa9
//-->""", encoding='utf-8')
print repr(x)

x = javascript.cleanup(u"""<![CDATA[
    script2
]]>""")
print repr(x)

x = javascript.cleanup("""<![CDATA[
    script2
]]>""")
print repr(x)

x = javascript.cleanup("""<![CDATA[
    script2 - \xc3\xa9
]]>""", encoding='utf-8')
print repr(x)

x = javascript.cleanup(u"""//<![CDATA[
    script3
//]]>""")
print repr(x)

x = javascript.cleanup("""//<![CDATA[
    script3
//]]>""")
print repr(x)

x = javascript.cleanup("""//<![CDATA[
    script3 - \xc3\xa9
//]]>""", encoding='utf-8')
print repr(x)

x = javascript.cleanup(u"""<!--//--><![CDATA[//><!--
    script4
//--><!]]>""")
print repr(x)

x = javascript.cleanup("""<!--//--><![CDATA[//><!--
    script4
//--><!]]>""")
print repr(x)

x = javascript.cleanup("""<!--//--><![CDATA[//><!--
    script4 - \xc3\xa9
//--><!]]>""", encoding='utf-8')
print repr(x)

try:
    x = javascript.cleanup("""<!--//--><![CDATA[//><!--
        script4 - \xe9
    //--><!]]>""", encoding='utf-8')
except UnicodeError:
    print "UnicodeError - OK"
