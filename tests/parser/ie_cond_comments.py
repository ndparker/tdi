#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.markup.soup import parser as _parser
from tdi.markup.soup import decoder as _decoder

class Builder(object):
    def __init__(self):
        self.events = []
        self.decoder = _decoder.HTMLDecoder('ascii')
    def __getattr__(self, name):
        if name.startswith('handle_'):
            def method(*args):
                self.events.append((name, args))
            return method
        raise AttributeError(name)


builder = Builder()
parser = _parser.SoupParser.html(builder)
parser.feed("""
<node>
    <![if !IE 8]>
    <xnode tdi="foo"></xnode>
    <![endif]>
</node>
""".strip().replace('\r\n', '\n').replace('\r', '\n'))
parser.finalize()

print builder.events == [
    ('handle_starttag', ('node', [], False, '<node>')),
    ('handle_text', ('\n    ',)),
    ('handle_text', ('<![if !IE 8]>',)),
    ('handle_text', ('\n    ',)),
    ('handle_starttag', ('xnode', [('tdi', '"foo"')], False,
        '<xnode tdi="foo">')),
    ('handle_endtag', ('xnode', '</xnode>')),
    ('handle_text', ('\n    ',)),
    ('handle_text', ('<![endif]>',)),
    ('handle_text', ('\n',)),
    ('handle_endtag', ('node', '</node>'))
]
