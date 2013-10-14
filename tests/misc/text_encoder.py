#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.markup.text import encoder as _encoder


encoder = _encoder.TextEncoder('utf-8')

print encoder.starttag('a', [('b', 'c'), ('d', None)], True)
print encoder.starttag('a', [('b1', None), ('c2', 'd3')], False)
print encoder.endtag('ff')
print encoder.name(u'ggg')
print encoder.name('ggg')
print encoder.attribute(u'\u20ac"')
print encoder.attribute(u'\u20ac')
print encoder.attribute(u'\u20ac"'.encode('utf-8'))
print encoder.attribute(u'\u20ac'.encode('utf-8'))
print encoder.content(u'\u20ac')
print encoder.content(u'\u20ac'.encode('utf-8'))
print encoder.encode(u'\u20ac')
print encoder.escape('lalala')
print encoder.escape('[lalala]')
