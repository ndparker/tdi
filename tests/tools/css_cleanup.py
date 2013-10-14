#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.tools import css

x = css.cleanup(u"""<!-- style1
-->""")
print repr(x)

x = css.cleanup("""<!-- style1
-->""")
print repr(x)

x = css.cleanup("""<!-- style1 - \xc3\xa9
-->""", encoding='utf-8')
print repr(x)

x = css.cleanup(u"""<![CDATA[
    style2
]]>""")
print repr(x)

x = css.cleanup("""<![CDATA[
    style2
]]>""")
print repr(x)

x = css.cleanup("""<![CDATA[
    style2 - \xc3\xa9
]]>""", encoding='utf-8')
print repr(x)

x = css.cleanup(u"""/*<![CDATA[*/
    style3
/*]]>*/""")
print repr(x)

x = css.cleanup("""/*<![CDATA[*/
    style3
/*]]>*/""")
print repr(x)

x = css.cleanup("""/*<![CDATA[*/
    style3 - \xc3\xa9
/*]]>*/""", encoding='utf-8')
print repr(x)

x = css.cleanup(u"""<!--/*--><![CDATA[/*><!--*/
    style4
/*]]>*/-->""")
print repr(x)

x = css.cleanup("""<!--/*--><![CDATA[/*><!--*/
    style4
/*]]>*/-->""")
print repr(x)

x = css.cleanup("""<!--/*--><![CDATA[/*><!--*/
    style4 - \xc3\xa9
/*]]>*/-->""", encoding='utf-8')
print repr(x)

try:
    x = css.cleanup("""<!--/*--><![CDATA[/*><!--*/
        style4 - \xe9
    /*]]>*/-->""", encoding='utf-8')
except UnicodeError:
    print "UnicodeError - OK"
