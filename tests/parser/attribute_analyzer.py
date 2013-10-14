#!/usr/bin/env python
import sys as _sys
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.markup import _analyzer
from tdi.markup.soup import decoder as _decoder

def test(*args, **kwargs):
    for hidden in (False, True):
        for remove in (False, True):
            analyze = _analyzer.DEFAULT_ANALYZER(
                _decoder.HTMLDecoder('cp1252'),
                hidden=hidden,
                removeattribute=remove,
            )
            try:
                res = analyze(*args, **kwargs)
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                e = _sys.exc_info()[:2]
                print "%s: %s" % (e[0].__name__, e[1])
            else:
                print "%r, tdi=%r, scope=%r, overlay=%r" % (
                    res[0],
                    res[1].get('attribute'),
                    res[1].get('scope'),
                    res[1].get('overlay'),
                )

test([])
test([('tdi:scope', None)])
test([('tdi:scope', '')])
test([('tdi:scope', '" "')])
test([('tdi:scope', '"x"')])
test([('tdi:scope', '"9"')])
test([('tdi:scope', '"x9"')])
test([('tdi:scope', '".x9"')])
test([('tdi:scope', '"x9.0"')])
test([('tdi:scope', '"x9.y"')])
test([('tdi:scope', '"x9.A"')])
test([('tdi:scope', '"x9.A0"')])
test([('tdi:scope', '"x9.A0."')])
test([('tdi:scope', '"=x9.A0"')])
test([('tdi:scope', '"=+x9.A0"')])
test([('tdi:scope', '"=-x9.A0"')])
test([('tdi:scope', '"==-x9.A0"')])
test([('tdi:scope', '"=-+x9.A0"')])
test([('tdi:scope', '"="')])

test([('tdi:overlay', None)])
test([('tdi:overlay', '')])
test([('tdi:overlay', '" "')])
test([('tdi:overlay', '"x"')])
test([('tdi:overlay', '"9"')])
test([('tdi:overlay', '"x9"')])
test([('tdi:overlay', '"x9.0"')])
test([('tdi:overlay', '"x9.y"')])
test([('tdi:overlay', '"x9_A"')])
test([('tdi:overlay', '"x9_A0"')])
test([('tdi:overlay', '"x9_A0_"')])
test([('tdi:overlay', '"=x9_A0"')])
test([('tdi:overlay', '"<x9_A0"')])
test([('tdi:overlay', '">x9_A0"')])
test([('tdi:overlay', '"<>x9_A0"')])
test([('tdi:overlay', '"+X9_A0"')])
test([('tdi:overlay', '"<-x9_A0"')])
test([('tdi:overlay', '"<<-x9_A0"')])
test([('tdi:overlay', '"<-+x9_A0"')])
test([('tdi:overlay', '"<"')])
test([('tdi:overlay', '"&lt;x"')])

test([('tdi', None)])
test([('tdi', '')])
test([('tdi', '" "')])
test([('tdi', '"x"')])
test([('tdi', '"-"')])
test([('tdi', '"9"')])
test([('tdi', '"x9"')])
test([('tdi', '"x9.0"')])
test([('tdi', '"x9.y"')])
test([('tdi', '"x9_A"')])
test([('tdi', '"x9_A0"')])
test([('tdi', '"x9_A0_"')])
test([('tdi', '"=x9_A0"')])
test([('tdi', '"<x9_A0"')])
test([('tdi', '"*x9_A0"')])
test([('tdi', '":x9_A0"')])
test([('tdi', '":*x9_A0"')])
test([('tdi', '"+X9_A0"')])
test([('tdi', '"*:-x9_A0"')])
test([('tdi', '"**-x9_A0"')])
test([('tdi', '"::-x9_A0"')])
test([('tdi', '"*-+x9_A0"')])
test([('tdi', '"*"')])
test([('tdi', '"&#42;x"')])

test([], name='')
test([], name='x')
test([], name='-')
test([], name='9')
test([], name='x9')
test([], name='x9.0')
test([], name='x9.y')
test([], name='x9_A')
test([], name='x9_A0')
test([], name='x9_A0_')
test([], name='=x9_A0')
test([], name='<x9_A0')
test([], name='*x9_A0')
test([], name=':x9_A0')
test([], name=':*x9_A0')
test([], name='+X9_A0')
test([], name='*:-x9_A0')
test([], name='**-x9_A0')
test([], name='::-x9_A0')
test([], name='*-+x9_A0')
test([], name='*')
test([], name='&#42;x')

test([('tdi', 'aa')], name='aa')
test([('tdi', '+aa')], name='aa')
test([('tdi', '+aa')], name='+aa')
test([('tdi', '-aa')], name='aa')
test([('tdi', 'bb')], name='aa')
