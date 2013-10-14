#!/usr/bin/env python
import pprint as _pprint
import sys as _sys
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.markup.soup import filters as _filters

class Decoder(object):
    def normalize(self, name):
        return name.lower()

class Collector(object):
    def __init__(self):
        self.events = []
        self.decoder = Decoder()
    def __getattr__(self, name):
        if name.startswith('handle_'):
            def method(*args):
                self.events.append((name, args))
            return method
        raise AttributeError(name)

def test(method, *inp):
    def inner(*expected):
        c = Collector()
        f = _filters.EncodingDetectFilter(c)
        try:
            getattr(f, method)(*inp)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            e = _sys.exc_info()[:2]
            c.events.append((e[0].__name__, str(e[1])))
        if c.events == list(expected):
            print "OK", method, inp
        else:
            print "FAIL", method, inp
            _pprint.pprint(tuple(c.events))
    return inner

#_test, test = test, lambda *a, **k: lambda *e: None


test('handle_endtag', '</foo>')(('handle_endtag', ('</foo>',)))
test('handle_pi', '<foo>')(('handle_pi', ('<foo>',)),)
test('handle_pi', '<?foo encoding="latin-1"?>')(
    ('handle_pi', ('<?foo encoding="latin-1"?>',)),
)
test('handle_pi', '<?xml encoding="latin-1"?>')(
    ('handle_encoding', ('latin-1',)),
    ('handle_pi', ('<?xml encoding="latin-1"?>',))
)
test('handle_pi', '<?XML encoding="latin-1"?>')(
    ('handle_encoding', ('latin-1',)),
    ('handle_pi', ('<?XML encoding="latin-1"?>',))
)
test('handle_pi', '<?  XML \t encoding  \n =  \r\n  "   \tlatin-1 \f"  ?>')(
    ('handle_encoding', ('latin-1',)),
    ('handle_pi', ('<?  XML \t encoding  \n =  \r\n  "   \tlatin-1 \f"  ?>',))
)
test('handle_pi', '<?  XML  version=  "1.0"  encoding  \n =  \r\n  "   '
                  '\tlatin-1 "  ?>')(
    ('handle_encoding', ('latin-1',)),
    ('handle_pi', ('<?  XML  version=  "1.0"  encoding  \n =  \r\n  "   '
                   '\tlatin-1 "  ?>',))
)
test('handle_pi', '<?  XML  encoding  \n =  \r\n  "   '
                  '\tlatin-1 "   version ="1.0"    ?>')(
    ('handle_encoding', ('latin-1',)),
    ('handle_pi', ('<?  XML  encoding  \n =  \r\n  "   \tlatin-1 "   '
                   'version ="1.0"    ?>',))
)
test('handle_pi', '<?  xml  version="1.0"   ?>')(
    ('handle_encoding', ('utf-8',)),
    ('handle_pi', ('<?  xml  version="1.0"   ?>',))
)

################
test('handle_starttag', 'xxx', [('charset', 'utf-8')], True, '<lalala>')(
    ('handle_starttag', ('xxx', [('charset', 'utf-8')], True, '<lalala>')),
)
test('handle_starttag', 'MeTa', [('charset', 'cp1252')], True, '<lalala>')(
    ('handle_encoding', ('cp1252',)),
    ('handle_starttag', ('MeTa', [('charset', 'cp1252')], True, '<lalala>'))
)
test('handle_starttag', 'MeTa', [('charset', None)], True, '<lalala>')(
    ('handle_starttag', ('MeTa', [('charset', None)], True, '<lalala>')),
)

####################
test('handle_starttag', 'MeTa', [
        ('HTTp-eqUiv', 'Content-Type'),
        ('CONTeNT', 'text/html; charset="yyy"')],
        True, '<hohoho!>')(
    ('handle_encoding', ('yyy',)),
    ('handle_starttag', (
        'MeTa', [
            ('HTTp-eqUiv', 'Content-Type'),
            ('CONTeNT', 'text/html; charset="yyy"')
        ],
        True,
        '<hohoho!>'
    ))
)
test('handle_starttag', 'MeTa', [
        ('HTTp-eqUi', 'Content-Type'),
        ('CONTeNT', 'text/html; charset="yyy"')],
        True, '<hohoho!>')(
    ('handle_starttag', (
        'MeTa', [
            ('HTTp-eqUi', 'Content-Type'),
            ('CONTeNT', 'text/html; charset="yyy"')
        ],
        True,
        '<hohoho!>'
    ))
)
test('handle_starttag', 'MeTa', [
        ('HTTp-eqUivx', 'Content-Type'),
        ('CONTeNT', 'text/html; charset="yyy"')],
        True, '<hohoho!>')(
    ('handle_starttag', (
        'MeTa', [
            ('HTTp-eqUivx', 'Content-Type'),
            ('CONTeNT', 'text/html; charset="yyy"')
        ],
        True,
        '<hohoho!>'
    ))
)
test('handle_starttag', 'MeTa', [
        ('HTTp-eqUiv', '" \tContent-Type\n \f"'),
        ('CONTeNT', ' \ttext/html  ; \f charset=" \ryyy  "    ')],
        True, '<hohoho!>')(
    ('handle_encoding', ('yyy',)),
    ('handle_starttag', (
        'MeTa', [
            ('HTTp-eqUiv', '" \tContent-Type\n \x0c"'),
            ('CONTeNT', ' \ttext/html  ; \x0c charset=" \ryyy  "    ')
        ],
        True,
        '<hohoho!>'
    ))
)
test('handle_starttag', 'MeTa', [
        ('HTTp-eqUiv', '" \tContent-Type\n \f"'),
        ('CONTeNT', ' \ttext/html  ; \f charset  =\n \ryyy      ')],
        True, '<hohoho!>')(
    ('handle_encoding', ('yyy',)),
    ('handle_starttag', (
        'MeTa', [
            ('HTTp-eqUiv', '" \tContent-Type\n \x0c"'),
            ('CONTeNT', ' \ttext/html  ; \x0c charset  =\n \ryyy      ')
        ],
        True,
        '<hohoho!>'
    ))
)

