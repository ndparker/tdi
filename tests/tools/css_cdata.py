#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.tools import css

x = css.cdata(u"""<!-- style1
-->""")
print repr(x)

x = css.cdata("""<!-- style1
-->""")
print repr(x)

x = css.cdata("""<!-- style1 - \xc3\xa9
-->""", encoding='utf-8')
print repr(x)

x = css.cdata(u"""<![CDATA[
    style2
]]>""")
print repr(x)

x = css.cdata("""<![CDATA[
    style2
]]>""")
print repr(x)

x = css.cdata("""<![CDATA[
    style2 - \xc3\xa9
]]>""", encoding='utf-8')
print repr(x)

x = css.cdata(u"""/*<![CDATA[*/
    style3
/*]]>*/""")
print repr(x)

x = css.cdata("""/*<![CDATA[*/
    style3
/*]]>*/""")
print repr(x)

x = css.cdata("""/*<![CDATA[*/
    style3 - \xc3\xa9
/*]]>*/""", encoding='utf-8')
print repr(x)

x = css.cdata(u"""<!--/*--><![CDATA[/*><!--*/
    style4
/*]]>*/-->""")
print repr(x)

x = css.cdata("""<!--/*--><![CDATA[/*><!--*/
    style4
/*]]>*/-->""")
print repr(x)

x = css.cdata("""<!--/*--><![CDATA[/*><!--*/
    style4 - \xc3\xa9
/*]]>*/-->""", encoding='utf-8')
print repr(x)

try:
    x = css.cdata("""<!--/*--><![CDATA[/*><!--*/
        style4 - \xe9
    /*]]>*/-->""", encoding='utf-8')
except UnicodeError:
    print "UnicodeError - OK"
