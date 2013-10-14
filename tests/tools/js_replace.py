#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

import re as _re

from tdi.tools import javascript

json = javascript.LiteralJSON(u'{"name": "Andr\xe9"}')
script = u"""
var count = __a__;
var name = '__b__';
var param = __c__;
var notreplaced = '__d__';
var with_ = '__foo_bar__';
""".strip()
x = javascript.replace(script, dict(
    a=10, b=u'__c__', c=json, foo_bar=u'Andr\xe9',
))
print type(x).__name__
print x.encode('utf-8')

json = javascript.LiteralJSON(u'{"name": "Andr\xe9"}')
script = u"""
var count = __a__;
var name = '__b__';
var param = __c__;
var notreplaced = '__d__';
var with_ = '__foo_bar__';
""".strip()
x = javascript.replace(script, dict(
    a=10, b=u'__c__', c=json, foo_bar=u'Andr\xe9',
), encoding='utf-8')
print type(x).__name__
print x.encode('utf-8')

json = javascript.LiteralJSON(u'{"name": "Andr\xe9"}')
script = """
var count = __a__;
var name = '__b__';
var param = __c__;
""".strip()
x = javascript.replace(script, dict(
    a=10, b=u'__c__', c=json
))
print type(x).__name__
print x

json = javascript.LiteralJSON(u'{"name": "Andr\xe9"}')
script = """
var count = __a__;
var name = '__b__';
var param = __c__;
""".strip()
x = javascript.replace(script, dict(
    a=10, b=u'__c__', c=json
), encoding='latin-1')
print type(x).__name__
print x

json = javascript.LiteralJSON(u'{"name": "Andr\xe9 - \u20ac"}')
script = """
var count = __a__;
var name = '__b__';
var param = __c__;
""".strip()
x = javascript.replace(script, dict(
    a=10, b=u'__c__', c=json
), encoding='latin-1')
print type(x).__name__
print x

json = javascript.LiteralJSON(u'{"name": "Andr\xe9 - \u20ac"}')
script = """
var count = __a__;
var name = '__b__';
var param = __c__;
var notreplaced = '__d__';
var with_ = '__foo_bar__';
""".strip()
x = javascript.replace(script, dict(
    a=10, b=u'__c__', c=json, foo_bar=u'Andr\xe9'
), encoding='ascii')
print type(x).__name__
print x


json = javascript.LiteralJSON(u'{"name": "Andr\xe9 </script>]]>"}')
script = u"""
var name = '__b__';
var param = __c__;
""".strip()

x = javascript.replace(script, dict(
    b=u'__c__', c=json
))
print type(x).__name__
print x.encode('utf-8')

json = javascript.LiteralJSON(u'{"name": "Andr\xe9 </script>]]>"}',
    inlined=False
)
x = javascript.replace(script, dict(
    b=u'__</script>--]]>__', c=json
))
print type(x).__name__
print x.encode('utf-8')

json = javascript.LiteralJSON(u'{"name": "Andr\xe9 </script>]]>"}',
    inlined=False
)
x = javascript.replace(script, dict(
    b=u'__</script>--]]>__', c=json
), inlined=False)
print type(x).__name__
print x.encode('utf-8')

x = javascript.replace(script, dict(
    b=u'__</script>--]]>__', c=json
), inlined=False, as_json=False)
print type(x).__name__
print x.encode('utf-8')


json = javascript.LiteralJSON(u'{"name": "Andr\xe9 </script>]]>"}')
script = u"""
var name = '@b@';
var param = @c@;
""".strip()

x = javascript.replace(script, dict(
    b=u'@c@', c=json
), pattern=ur'@(?P<name>[^@]+)@')
print type(x).__name__
print x.encode('utf-8')

x = javascript.replace(script, dict(
    b=u'@c@', c=json
), pattern=_re.compile(ur'@(?P<name>[^@]+)@'))
print type(x).__name__
print x.encode('utf-8')
