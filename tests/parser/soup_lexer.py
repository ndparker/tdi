#!/usr/bin/env python
import sys as _sys
import warnings as _warnings
import pprint as _pprint
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.markup.soup import parser as _parser

class Collector(object):
    def __init__(self):
        self.events = []
    def __getattr__(self, name):
        if name.startswith('handle_'):
            def method(*args):
                self.events.append((name, args))
            return method
        raise AttributeError(name)


def normalize(s):
    return s.lower()

def lex(inp, cdata=None, ie=True):
    def inner(*expected):
        collector = Collector()
        lexer = _parser.DEFAULT_LEXER(
            collector, conditional_ie_comments=ie
        )
        if cdata:
            lexer.cdata(*cdata)
        try:
            lexer.feed(inp)
            lexer.finalize()
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            e = _sys.exc_info()[:2]
            collector.events.append((e[0].__name__, str(e[1])))

        if collector.events == list(expected):
            if len(inp) > 70:
                print 'OK', repr(inp[:70]) + '...'
            else:
                print 'OK', repr(inp)
        else:
            print 'FAIL', repr(inp)
            _pprint.pprint(tuple(collector.events))

    return inner

#_lex, lex = lex, lambda *args, **kwargs: lambda *x: None


lex('some text')(('handle_text', ('some text',)),)
lex('<>')(('handle_starttag', ('', [], False, '<>')),)
lex('text<>')(
    ('handle_text', ('text',)),
    ('handle_starttag', ('', [], False, '<>'))
)
lex('text<>more')(
    ('handle_text', ('text',)),
    ('handle_starttag', ('', [], False, '<>')),
    ('handle_text', ('more',))
)
lex('<#')(('handle_text', ('<',)), ('handle_text', ('#',)))

#########
lex('<?')(('LexerEOFError', 'Unfinished parser state PI'),)
lex('lalala<?lololo?>')(
    ('handle_text', ('lalala',)),
    ('handle_pi', ('<?lololo?>',))
)
lex('lalala<?>lulul')(
    ('handle_text', ('lalala',)),
    ('LexerEOFError', 'Unfinished parser state PI')
)
lex('lalala<??>lulul')(
    ('handle_text', ('lalala',)),
    ('handle_pi', ('<??>',)),
    ('handle_text', ('lulul',))
)
lex('lalala<???>lulul')(
    ('handle_text', ('lalala',)),
    ('handle_pi', ('<???>',)),
    ('handle_text', ('lulul',))
)

###########
lex('xxx', cdata=(normalize, 'foo'))(('handle_text', ('xxx',)),)
lex('xxx<', cdata=(normalize, 'foo'))(
    ('handle_text', ('xxx',)),
    ('LexerEOFError', 'Unfinished parser state CDATA')
)
lex('xxx<x', cdata=(normalize, 'foo'))(('handle_text', ('xxx<x',)),)
lex('xxx<x<', cdata=(normalize, 'foo'))(
    ('handle_text', ('xxx<x',)),
    ('LexerEOFError', 'Unfinished parser state CDATA')
)
lex('xxx<x</', cdata=(normalize, 'foo'))(
    ('handle_text', ('xxx<x',)),
    ('LexerEOFError', 'Unfinished parser state ENDTAG')
)
lex('xxx<x<</', cdata=(normalize, 'foo'))(
    ('handle_text', ('xxx<x<',)),
    ('LexerEOFError', 'Unfinished parser state ENDTAG')
)
lex('xxx<x<</bar>', cdata=(normalize, 'foo'))(
    ('handle_text', ('xxx<x<',)),
    ('handle_text', ('</bar>',))
)
lex('xxx<x<</bar>xxx</fOo>yyy', cdata=(normalize, 'Foo'))(
    ('handle_text', ('xxx<x<',)),
    ('handle_text', ('</bar>',)),
    ('handle_text', ('xxx',)),
    ('handle_endtag', ('fOo', '</fOo>')),
    ('handle_text', ('yyy',))
)

#########
lex('<')(('LexerEOFError', 'Unfinished parser state MARKUP'),)
lex('<a')(('LexerEOFError', 'Unfinished parser state STARTTAG'),)
lex('<a>')(('handle_starttag', ('a', [], False, '<a>')),)
lex('hey<a>')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [], False, '<a>'))
)
lex('hey<a>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [], False, '<a>')),
    ('handle_text', ('ho.',))
)
lex('hey<a href>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', None)], False, '<a href>')),
    ('handle_text', ('ho.',))
)
lex('hey<a href=">ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
lex('hey<a href="">ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', '""')], False, '<a href="">')),
    ('handle_text', ('ho.',))
)
lex('hey<a href=""">ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
lex('hey<a href=\'>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
lex('hey<a href=\'\'>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', "''")], False, "<a href=''>")),
    ('handle_text', ('ho.',))
)
lex('hey<a href=\'\'\'>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
lex('hey<a href="link">ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', '"link"')], False,
        '<a href="link">')),
    ('handle_text', ('ho.',))
)
lex('hey<a href=\'link\'>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', "'link'")], False,
        "<a href='link'>")),
    ('handle_text', ('ho.',))
)
lex('hey<a href="link" >ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', '"link"')], False,
        '<a href="link" >')),
    ('handle_text', ('ho.',))
)
lex('hey<a href=\'link\' >ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', "'link'")], False,
        "<a href='link' >")),
    ('handle_text', ('ho.',))
)
lex('hey<a href="link\'>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
lex('hey<a href=\'link">ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
lex('hey<a href=link>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', 'link')], False, '<a href=link>')),
    ('handle_text', ('ho.',))
)
lex('hey<a href=li"nk>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
lex('hey<abc href="lala" lolo xxx="yyy">ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', (
        'abc',
        [('href', '"lala"'), ('lolo', None), ('xxx', '"yyy"')],
        False,
        '<abc href="lala" lolo xxx="yyy">')
    ),
    ('handle_text', ('ho.',))
)

###########
lex('<a />')(('handle_starttag', ('a', [], True, '<a />')),)
lex('<a/>')(('handle_starttag', ('a', [], True, '<a/>')),)
lex('hey<ab/>')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('ab', [], True, '<ab/>'))
)
lex('hey<ab />')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('ab', [], True, '<ab />'))
)
lex('hey<a/>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [], True, '<a/>')),
    ('handle_text', ('ho.',))
)
lex('hey<a href/>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', None)], True, '<a href/>')),
    ('handle_text', ('ho.',))
)
lex('hey<a href="/>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
lex('hey<a href=""/>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', '""')], True, '<a href=""/>')),
    ('handle_text', ('ho.',))
)
lex('hey<a href="" />ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', '""')], True, '<a href="" />')),
    ('handle_text', ('ho.',))
)
lex('hey<a href="""/>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
lex('hey<a href=\'/>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
lex('hey<a href=\'\'/>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', "''")], True, "<a href=''/>")),
    ('handle_text', ('ho.',))
)
lex('hey<a href=\'\'\'/>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
lex('hey<axx href="link" />ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag',
        ('axx', [('href', '"link"')], True, '<axx href="link" />')),
    ('handle_text', ('ho.',))
)
lex('hey<a href=\'link\' />ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag',
        ('a', [('href', "'link'")], True, "<a href='link' />")),
    ('handle_text', ('ho.',))
)
lex('hey<a href="link" / >ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag',
        ('a', [('href', '"link"')], True, '<a href="link" / >')),
    ('handle_text', ('ho.',))
)
lex('hey<a href=\'link\' / >ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag',
        ('a', [('href', "'link'")], True, "<a href='link' / >")),
    ('handle_text', ('ho.',))
)
lex('hey<a href="link\'/>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
lex('hey<a href=\'link" />ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
lex('hey<a href=link />ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', 'link')], True, '<a href=link />')),
    ('handle_text', ('ho.',))
)
lex('hey<a href=li"nk/>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
lex('hey<abc href="lala" lolo xxx="yyy" />ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', (
        'abc',
        [('href', '"lala"'), ('lolo', None), ('xxx', '"yyy"')],
        True,
        '<abc href="lala" lolo xxx="yyy" />')
    ),
    ('handle_text', ('ho.',))
)

#####
lex('</')(('LexerEOFError', 'Unfinished parser state ENDTAG'),)
lex('</>')(('handle_endtag', ('', '</>')),)
lex('</xy')(('LexerEOFError', 'Unfinished parser state ENDTAG'),)
lex('</xy>')(('handle_endtag', ('xy', '</xy>')),)
lex('</ xy>')(('handle_endtag', ('xy', '</ xy>')),)
lex('</ \n xy>')(('handle_endtag', ('xy', '</ \n xy>')),)
lex('</ hjkhk   \t>')(('handle_endtag', ('hjkhk', '</ hjkhk   \t>')),)

######
lex('<!')(('LexerEOFError', 'Unfinished parser state DECL'),)
lex('<!-')(('LexerEOFError', 'Unfinished parser state DECL'),)
lex('<!--')(('LexerEOFError', 'Unfinished parser state COMMENT'),)
lex('<!-->')(('LexerEOFError', 'Unfinished parser state COMMENT'),)
lex('<!--->')(('LexerEOFError', 'Unfinished parser state COMMENT'),)
lex('<!---->')(('handle_comment', ('<!---->',)),)
lex('<!----  \n>')(('handle_comment', ('<!----  \n>',)),)
lex('<!--\n\n \f--  \n>')(('handle_comment', ('<!--\n\n \x0c--  \n>',)),)
lex('<!-- lalalal -->')(('handle_comment', ('<!-- lalalal -->',)),)

##############
lex('<!--[if')(('LexerEOFError', 'Unfinished parser state COMMENT'),)
lex('<!--[ \tif   \n]>')(('handle_text', ('<!--[ \tif   \n]>',)),)
lex('<!--[else')(('LexerEOFError', 'Unfinished parser state COMMENT'),)
lex('<!--[ \telse   \n]>')(('handle_text', ('<!--[ \telse   \n]>',)),)
lex('<!--[endif')(('LexerEOFError', 'Unfinished parser state COMMENT'),)
lex('<!--[ \tendif   \n]>')(('handle_text', ('<!--[ \tendif   \n]>',)),)
lex('<!--[ \tENDIF   \n]>')(('handle_text', ('<!--[ \tENDIF   \n]>',)),)
lex('<!--[ \tIf   \n]>')(('handle_text', ('<!--[ \tIf   \n]>',)),)
lex('<!--[xxx')(('LexerEOFError', 'Unfinished parser state COMMENT'),)
lex('<!--[ \txxx   \n]>')(
    ('LexerEOFError', 'Unfinished parser state COMMENT'),
)
lex('<!--[if', ie=False)(
    ('LexerEOFError', 'Unfinished parser state COMMENT'),
)
lex('<!--[ \tif   \n]>', ie=False)(
    ('LexerEOFError', 'Unfinished parser state COMMENT'),
)

#################
lex('<![')(('LexerEOFError', 'Unfinished parser state MSECTION'),)
lex('<![lalal')(('LexerEOFError', 'Unfinished parser state MSECTION'),)
lex('<![lalala]]>')(('handle_msection', ('lalala', '', '<![lalala]]>')),)
lex('<![ \tlalala   xxxxx   ] \r\n]   >')(
    ('handle_msection',
        ('lalala', '   xxxxx   ', '<![ \tlalala   xxxxx   ] \r\n]   >')),
)
lex('<![ \tlalala  [ xxxxx   ] \r\n]   >')(
    ('handle_msection',
        ('lalala', ' xxxxx   ', '<![ \tlalala  [ xxxxx   ] \r\n]   >')),
)
lex('<![]>')(('handle_text', ('<![]',)), ('handle_text', ('>',)))
lex('<![ ]>')(('handle_text', ('<![ ]',)), ('handle_text', ('>',)))
lex('<![  \t] >')(('handle_text', ('<![  \t]',)), ('handle_text', (' >',)))

lex('<![if !IE 8]>')(('handle_text', ('<![if !IE 8]>',)),)
lex('<![endif]>')(('handle_text', ('<![endif]>',)),)
lex('<![endif]-->')(('handle_text', ('<![endif]-->',)),)
lex('<![eNDiF] -- >')(('handle_text', ('<![eNDiF] -- >',)),)
lex('<![eNDiFx] -- >')(('LexerEOFError', 'Unfinished parser state MSECTION'),)
lex('<![eNDix] -- >')(('LexerEOFError', 'Unfinished parser state MSECTION'),)
lex('<![if !IE 8]>', ie=False)(
    ('LexerEOFError', 'Unfinished parser state MSECTION'),
)
lex('<![endif]>', ie=False)(
    ('LexerEOFError', 'Unfinished parser state MSECTION'),
)
lex('<![endif]-->', ie=False)(
    ('LexerEOFError', 'Unfinished parser state MSECTION'),
)
lex('<![eNDiF] -- >', ie=False)(
    ('LexerEOFError', 'Unfinished parser state MSECTION'),
)

##############
lex('<!DOCTYPE>')(('handle_decl', ('DOCTYPE', '', '<!DOCTYPE>')),)
lex('<!DOCTYPE html>')(
    ('handle_decl', ('DOCTYPE', 'html', '<!DOCTYPE html>')),
)
lex('<!DOCTYPE \thtml\f \n>')(
    ('handle_decl', ('DOCTYPE', 'html', '<!DOCTYPE \thtml\f \n>')),
)
lex('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">')(
    ('handle_decl', (
        'DOCTYPE',
        'html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"',
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'
    )),
)
lex("<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Transitional//EN' 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd'>")(
    ('handle_decl', (
        'DOCTYPE',
        "html PUBLIC '-//W3C//DTD XHTML 1.0 Transitional//EN' 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd'",
        "<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Transitional//EN' 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd'>"
    )),
)
lex('<!DOCTYPE html -- some comment -- >')(
    ('handle_decl', (
        'DOCTYPE',
        'html -- some comment --',
        '<!DOCTYPE html -- some comment -- >'
    )),
)
lex('<!DOCTYPE html -- some co"mment -- >')(
    ('handle_decl', (
        'DOCTYPE',
        'html -- some co"mment --',
        '<!DOCTYPE html -- some co"mment -- >'
    )),
)
lex('<!DOCTYPE html -- some comment -a >')(
    ('LexerEOFError', 'Unfinished parser state DECL'),
)
lex('<!DOCTYPE html -- some comment -a -- >')(
    ('handle_decl', (
        'DOCTYPE',
        'html -- some comment -a --',
        '<!DOCTYPE html -- some comment -a -- >'
    )),
)
lex('<!DOCTYPE html -- some comment -- -a >')(
    ('handle_decl', (
        'DOCTYPE',
        'html -- some comment -- -a',
        '<!DOCTYPE html -- some comment -- -a >'
    )),
)
lex('''<!DOCTYPE html [
<! -- comment -- >

<!ENTITY % events
 "onclick     %Script;       #IMPLIED  -- a pointer button was clicked --
  ondblclick  %Script;       #IMPLIED  -- a pointer button was double clicked--
  onmousedown %Script;       #IMPLIED  -- a pointer button was pressed down --
  onmouseup   %Script;       #IMPLIED  -- a pointer button was released --
  onmouseover %Script;       #IMPLIED  -- a pointer was moved onto --
  onmousemove %Script;       #IMPLIED  -- a pointer was moved within --
  onmouseout  %Script;       #IMPLIED  -- a pointer was moved away --
  onkeypress  %Script;       #IMPLIED  -- a key was pressed and released --
  onkeydown   %Script;       #IMPLIED  -- a key was pressed down --
  onkeyup     %Script;       #IMPLIED  -- a key was released --"
  >

<!ELEMENT (SUB|SUP) - - (%inline;)*    -- subscript, superscript -->
<!ATTLIST (SUB|SUP)
  %attrs;                              -- %coreattrs, %i18n, %events --
  >
]>''')(
    ('handle_decl', (
        'DOCTYPE',
        'html [\n<! -- comment -- >\n\n<!ENTITY % events\n "onclick     %Script;       #IMPLIED  -- a pointer button was clicked --\n  ondblclick  %Script;       #IMPLIED  -- a pointer button was double clicked--\n  onmousedown %Script;       #IMPLIED  -- a pointer button was pressed down --\n  onmouseup   %Script;       #IMPLIED  -- a pointer button was released --\n  onmouseover %Script;       #IMPLIED  -- a pointer was moved onto --\n  onmousemove %Script;       #IMPLIED  -- a pointer was moved within --\n  onmouseout  %Script;       #IMPLIED  -- a pointer was moved away --\n  onkeypress  %Script;       #IMPLIED  -- a key was pressed and released --\n  onkeydown   %Script;       #IMPLIED  -- a key was pressed down --\n  onkeyup     %Script;       #IMPLIED  -- a key was released --"\n  >\n\n<!ELEMENT (SUB|SUP) - - (%inline;)*    -- subscript, superscript -->\n<!ATTLIST (SUB|SUP)\n  %attrs;                              -- %coreattrs, %i18n, %events --\n  >\n]',
        '<!DOCTYPE html [\n<! -- comment -- >\n\n<!ENTITY % events\n "onclick     %Script;       #IMPLIED  -- a pointer button was clicked --\n  ondblclick  %Script;       #IMPLIED  -- a pointer button was double clicked--\n  onmousedown %Script;       #IMPLIED  -- a pointer button was pressed down --\n  onmouseup   %Script;       #IMPLIED  -- a pointer button was released --\n  onmouseover %Script;       #IMPLIED  -- a pointer was moved onto --\n  onmousemove %Script;       #IMPLIED  -- a pointer was moved within --\n  onmouseout  %Script;       #IMPLIED  -- a pointer was moved away --\n  onkeypress  %Script;       #IMPLIED  -- a key was pressed and released --\n  onkeydown   %Script;       #IMPLIED  -- a key was pressed down --\n  onkeyup     %Script;       #IMPLIED  -- a key was released --"\n  >\n\n<!ELEMENT (SUB|SUP) - - (%inline;)*    -- subscript, superscript -->\n<!ATTLIST (SUB|SUP)\n  %attrs;                              -- %coreattrs, %i18n, %events --\n  >\n]>'
    )),
)
lex('<!DOCTYPE html -- some comment -- <![CDATA[ lalala ]]> -a >')(
    ('handle_decl', (
        'DOCTYPE',
        'html -- some comment -- <![CDATA[ lalala ]]> -a',
        '<!DOCTYPE html -- some comment -- <![CDATA[ lalala ]]> -a >'
    )),
)
lex('<!DOCTYPE html -- some comment -- <![CDATA[ l" --alala ]]> -a >')(
    ('handle_decl', (
        'DOCTYPE',
        'html -- some comment -- <![CDATA[ l" --alala ]]> -a',
        '<!DOCTYPE html -- some comment -- <![CDATA[ l" --alala ]]> -a >'
    )),
)

# !!! KEEP TESTS IN SYNC WITH soup_lexer_mashed! !!! #

# vim: nowrap
