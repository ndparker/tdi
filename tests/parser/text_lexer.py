#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.markup.text import parser as _parser

class Collector(object):
    def __init__(self):
        self.events = []
    def __getattr__(self, name):
        if name.startswith('handle_'):
            def method(*args):
                self.events.append((name, args))
            return method
        raise AttributeError(name)


collector = Collector()
def lex(inp):
    lexer = _parser.TextLexer(collector)
    lexer.feed(inp)
    lexer.finalize()

lex('some text')
lex('[[hello]]')
lex('[]')
lex('[#this is a comment #]')
lex('[/endtag]')

print collector.events == [
    ('handle_text', ('some text',)),
    ('handle_starttag', ('hello', [], True, '[[hello]]')),
    ('handle_escape', ('[', '[]')),
    ('handle_comment', ('[#this is a comment #]',)),
    ('handle_endtag', ('endtag', '[/endtag]')),
]
