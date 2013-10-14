#!/usr/bin/env python
import pprint as _pprint
import sys as _sys
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import filters as _filters

class Collector(object):
    def __init__(self):
        self.events = []
        self.canary = 'bla'
    def __getattr__(self, name):
        if name.startswith('handle_'):
            def method(*args):
                self.events.append((name, args))
            return method
        raise AttributeError(name)


class Foo(_filters.BaseEventFilter):
    def __init__(self, builder):
        super(Foo, self).__init__(builder)

    def finalize(self):
        self.builder.handle_blob(self.canary)


class Bar(_filters.BaseEventFilter):
    def __init__(self, builder):
        super(Bar, self).__init__(builder)

    def __getattr__(self, name):
        if name == 'canary':
            raise AttributeError('lol')
        return getattr(self.builder, name)

    def finalize(self):
        self.builder.handle_blob(self.canary)


def test(cls, method, *inp):
    def inner(*expected):
        c = Collector()
        f = cls(c)
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


test(Foo, 'foo', 'bar', 'baz')(('AttributeError', 'foo'),)
test(Foo, 'handle_blub', 'plop', 'poeh')(('handle_blub', ('plop', 'poeh')),)
test(Foo, 'finalize')(('handle_blob', ('bla',)),)

test(Bar, 'foo', 'bar', 'baz')(('AttributeError', 'foo'),)
test(Bar, 'handle_blub', 'plop', 'poeh')(('handle_blub', ('plop', 'poeh')),)
test(Bar, 'finalize')(('AttributeError', 'lol'),)

