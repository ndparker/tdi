#!/usr/bin/env python
import sys as _sys
import warnings as _warnings
import pprint as _pprint
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.markup.soup import parser as _parser

class Decoder(object):
    def normalize(self, s):
        return s.lower()

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


def parse(inp, dtd='html'):
    def inner(*expected):
        collector = Collector()
        parser = getattr(_parser.DEFAULT_PARSER, dtd)(collector)
        try:
            parser.feed(inp)
            parser.finalize()
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

#_parse, parse = parse, lambda *args, **kwargs: lambda *x: None


parse('some text')(('handle_text', ('some text',)),)
parse('<>')(
    ('handle_starttag', ('', [], False, '<>')),
    ('handle_endtag', ('', ''))
)
parse('text<>')(
    ('handle_text', ('text',)),
    ('handle_starttag', ('', [], False, '<>')),
    ('handle_endtag', ('', ''))
)
parse('text<>more')(
    ('handle_text', ('text',)),
    ('handle_starttag', ('', [], False, '<>')),
    ('handle_text', ('more',)),
    ('handle_endtag', ('', ''))
)
parse('<#')(('handle_text', ('<',)), ('handle_text', ('#',)))

#########
parse('<?')(('LexerEOFError', 'Unfinished parser state PI'),)
parse('lalala<?lololo?>')(
    ('handle_text', ('lalala',)),
    ('handle_pi', ('<?lololo?>',))
)
parse('lalala<?>lulul')(
    ('handle_text', ('lalala',)),
    ('LexerEOFError', 'Unfinished parser state PI')
)
parse('lalala<??>lulul')(
    ('handle_text', ('lalala',)),
    ('handle_pi', ('<??>',)),
    ('handle_text', ('lulul',))
)
parse('lalala<???>lulul')(
    ('handle_text', ('lalala',)),
    ('handle_pi', ('<???>',)),
    ('handle_text', ('lulul',))
)

###########
parse('<style>xxx')(
    ('handle_starttag', ('style', [], False, '<style>')),
    ('handle_text', ('xxx',)),
    ('handle_endtag', ('style', ''))
)
parse('<style>xxx<')(
    ('handle_starttag', ('style', [], False, '<style>')),
    ('handle_text', ('xxx',)),
    ('LexerEOFError', 'Unfinished parser state CDATA')
)
parse('<style>xxx<x')(
    ('handle_starttag', ('style', [], False, '<style>')),
    ('handle_text', ('xxx<x',)),
    ('handle_endtag', ('style', ''))
)
parse('<style>xxx<x<')(
    ('handle_starttag', ('style', [], False, '<style>')),
    ('handle_text', ('xxx<x',)),
    ('LexerEOFError', 'Unfinished parser state CDATA')
)
parse('<style>xxx<x</')(
    ('handle_starttag', ('style', [], False, '<style>')),
    ('handle_text', ('xxx<x',)),
    ('LexerEOFError', 'Unfinished parser state ENDTAG')
)
parse('<style>xxx<x<</')(
    ('handle_starttag', ('style', [], False, '<style>')),
    ('handle_text', ('xxx<x<',)),
    ('LexerEOFError', 'Unfinished parser state ENDTAG')
)
parse('<style>xxx<x<</bar>')(
    ('handle_starttag', ('style', [], False, '<style>')),
    ('handle_text', ('xxx<x<',)),
    ('handle_text', ('</bar>',)),
    ('handle_endtag', ('style', ''))
)
parse('<style>xxx<x<</bar>xxx</STyLe>yyy')(
    ('handle_starttag', ('style', [], False, '<style>')),
    ('handle_text', ('xxx<x<',)),
    ('handle_text', ('</bar>',)),
    ('handle_text', ('xxx',)),
    ('handle_endtag', ('STyLe', '</STyLe>')),
    ('handle_text', ('yyy',))
)

#########
parse('<')(('LexerEOFError', 'Unfinished parser state MARKUP'),)
parse('<a')(('LexerEOFError', 'Unfinished parser state STARTTAG'),)
parse('<a>')(
    ('handle_starttag', ('a', [], False, '<a>')),
    ('handle_endtag', ('a', ''))
)
parse('hey<a>')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [], False, '<a>')),
    ('handle_endtag', ('a', ''))
)
parse('hey<a>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [], False, '<a>')),
    ('handle_text', ('ho.',)),
    ('handle_endtag', ('a', ''))
)
parse('hey<a href>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', None)], False, '<a href>')),
    ('handle_text', ('ho.',)),
    ('handle_endtag', ('a', ''))
)
parse('hey<a href=">ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
parse('hey<a href="">ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', '""')], False, '<a href="">')),
    ('handle_text', ('ho.',)),
    ('handle_endtag', ('a', ''))
)
parse('hey<a href=""">ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
parse('hey<a href=\'>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
parse('hey<a href=\'\'>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', "''")], False, "<a href=''>")),
    ('handle_text', ('ho.',)),
    ('handle_endtag', ('a', ''))
)
parse('hey<a href=\'\'\'>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
parse('hey<a href="link">ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', '"link"')], False,
        '<a href="link">')),
    ('handle_text', ('ho.',)),
    ('handle_endtag', ('a', ''))
)
parse('hey<a href=\'link\'>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', "'link'")], False,
        "<a href='link'>")),
    ('handle_text', ('ho.',)),
    ('handle_endtag', ('a', ''))
)
parse('hey<a href="link" >ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', '"link"')], False,
        '<a href="link" >')),
    ('handle_text', ('ho.',)),
    ('handle_endtag', ('a', ''))
)
parse('hey<a href=\'link\' >ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', "'link'")], False,
        "<a href='link' >")),
    ('handle_text', ('ho.',)),
    ('handle_endtag', ('a', ''))
)
parse('hey<a href="link\'>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
parse('hey<a href=\'link">ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
parse('hey<a href=link>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', 'link')], False, '<a href=link>')),
    ('handle_text', ('ho.',)),
    ('handle_endtag', ('a', ''))
)
parse('hey<a href=li"nk>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
parse('hey<abc href="lala" lolo xxx="yyy">ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', (
        'abc',
        [('href', '"lala"'), ('lolo', None), ('xxx', '"yyy"')],
        False,
        '<abc href="lala" lolo xxx="yyy">')
    ),
    ('handle_text', ('ho.',)),
    ('handle_endtag', ('abc', ''))
)

###########
parse('<a />')(('handle_starttag', ('a', [], True, '<a />')),)
parse('<a/>')(('handle_starttag', ('a', [], True, '<a/>')),)
parse('hey<ab/>')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('ab', [], True, '<ab/>'))
)
parse('hey<ab />')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('ab', [], True, '<ab />'))
)
parse('hey<a/>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [], True, '<a/>')),
    ('handle_text', ('ho.',))
)
parse('hey<a href/>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', None)], True, '<a href/>')),
    ('handle_text', ('ho.',))
)
parse('hey<a href="/>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
parse('hey<a href=""/>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', '""')], True, '<a href=""/>')),
    ('handle_text', ('ho.',))
)
parse('hey<a href="" />ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', '""')], True, '<a href="" />')),
    ('handle_text', ('ho.',))
)
parse('hey<a href="""/>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
parse('hey<a href=\'/>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
parse('hey<a href=\'\'/>ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', "''")], True, "<a href=''/>")),
    ('handle_text', ('ho.',))
)
parse('hey<a href=\'\'\'/>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
parse('hey<axx href="link" />ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag',
        ('axx', [('href', '"link"')], True, '<axx href="link" />')),
    ('handle_text', ('ho.',))
)
parse('hey<a href=\'link\' />ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag',
        ('a', [('href', "'link'")], True, "<a href='link' />")),
    ('handle_text', ('ho.',))
)
parse('hey<a href="link" / >ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag',
        ('a', [('href', '"link"')], True, '<a href="link" / >')),
    ('handle_text', ('ho.',))
)
parse('hey<a href=\'link\' / >ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag',
        ('a', [('href', "'link'")], True, "<a href='link' / >")),
    ('handle_text', ('ho.',))
)
parse('hey<a href="link\'/>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
parse('hey<a href=\'link" />ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
parse('hey<a href=link />ho.')(
    ('handle_text', ('hey',)),
    ('handle_starttag', ('a', [('href', 'link')], True, '<a href=link />')),
    ('handle_text', ('ho.',))
)
parse('hey<a href=li"nk/>ho.')(
    ('handle_text', ('hey',)),
    ('LexerEOFError', 'Unfinished parser state STARTTAG')
)
parse('hey<abc href="lala" lolo xxx="yyy" />ho.')(
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
parse('</')(('LexerEOFError', 'Unfinished parser state ENDTAG'),)
parse('</>')(('handle_endtag', ('', '</>')),)
parse('</xy')(('LexerEOFError', 'Unfinished parser state ENDTAG'),)
parse('</xy>')(('handle_endtag', ('xy', '</xy>')),)
parse('</ xy>')(('handle_endtag', ('xy', '</ xy>')),)
parse('</ \n xy>')(('handle_endtag', ('xy', '</ \n xy>')),)
parse('</ hjkhk   \t>')(('handle_endtag', ('hjkhk', '</ hjkhk   \t>')),)

######
parse('<!')(('LexerEOFError', 'Unfinished parser state DECL'),)
parse('<!-')(('LexerEOFError', 'Unfinished parser state DECL'),)
parse('<!--')(('LexerEOFError', 'Unfinished parser state COMMENT'),)
parse('<!-->')(('LexerEOFError', 'Unfinished parser state COMMENT'),)
parse('<!--->')(('LexerEOFError', 'Unfinished parser state COMMENT'),)
parse('<!---->')(('handle_comment', ('<!---->',)),)
parse('<!----  \n>')(('handle_comment', ('<!----  \n>',)),)
parse('<!--\n\n \f--  \n>')(('handle_comment', ('<!--\n\n \x0c--  \n>',)),)
parse('<!-- lalalal -->')(('handle_comment', ('<!-- lalalal -->',)),)

##############
parse('<!--[if')(('LexerEOFError', 'Unfinished parser state COMMENT'),)
parse('<!--[ \tif   \n]>')(('handle_text', ('<!--[ \tif   \n]>',)),)
parse('<!--[else')(('LexerEOFError', 'Unfinished parser state COMMENT'),)
parse('<!--[ \telse   \n]>')(('handle_text', ('<!--[ \telse   \n]>',)),)
parse('<!--[endif')(('LexerEOFError', 'Unfinished parser state COMMENT'),)
parse('<!--[ \tendif   \n]>')(('handle_text', ('<!--[ \tendif   \n]>',)),)
parse('<!--[ \tENDIF   \n]>')(('handle_text', ('<!--[ \tENDIF   \n]>',)),)
parse('<!--[ \tIf   \n]>')(('handle_text', ('<!--[ \tIf   \n]>',)),)
parse('<!--[xxx')(('LexerEOFError', 'Unfinished parser state COMMENT'),)
parse('<!--[ \txxx   \n]>')(
    ('LexerEOFError', 'Unfinished parser state COMMENT'),
)
#parse('<!--[if', ie=False)(
#    ('LexerEOFError', 'Unfinished parser state COMMENT'),
#)
#parse('<!--[ \tif   \n]>', ie=False)(
#    ('LexerEOFError', 'Unfinished parser state COMMENT'),
#)

#################
parse('<![')(('LexerEOFError', 'Unfinished parser state MSECTION'),)
parse('<![lalal')(('LexerEOFError', 'Unfinished parser state MSECTION'),)
parse('<![lalala]]>')(('handle_msection', ('lalala', '', '<![lalala]]>')),)
parse('<![ \tlalala   xxxxx   ] \r\n]   >')(
    ('handle_msection',
        ('lalala', '   xxxxx   ', '<![ \tlalala   xxxxx   ] \r\n]   >')),
)
parse('<![ \tlalala  [ xxxxx   ] \r\n]   >')(
    ('handle_msection',
        ('lalala', ' xxxxx   ', '<![ \tlalala  [ xxxxx   ] \r\n]   >')),
)
parse('<![]>')(('handle_text', ('<![]',)), ('handle_text', ('>',)))
parse('<![ ]>')(('handle_text', ('<![ ]',)), ('handle_text', ('>',)))
parse('<![  \t] >')(('handle_text', ('<![  \t]',)), ('handle_text', (' >',)))

parse('<![if !IE 8]>')(('handle_text', ('<![if !IE 8]>',)),)
parse('<![endif]>')(('handle_text', ('<![endif]>',)),)
parse('<![endif]-->')(('handle_text', ('<![endif]-->',)),)
parse('<![eNDiF] -- >')(('handle_text', ('<![eNDiF] -- >',)),)
parse('<![eNDiFx] -- >')(('LexerEOFError', 'Unfinished parser state MSECTION'),)
parse('<![eNDix] -- >')(('LexerEOFError', 'Unfinished parser state MSECTION'),)
#parse('<![if !IE 8]>', ie=False)(
#    ('LexerEOFError', 'Unfinished parser state MSECTION'),
#)
#parse('<![endif]>', ie=False)(
#    ('LexerEOFError', 'Unfinished parser state MSECTION'),
#)
#parse('<![endif]-->', ie=False)(
#    ('LexerEOFError', 'Unfinished parser state MSECTION'),
#)
#parse('<![eNDiF] -- >', ie=False)(
#    ('LexerEOFError', 'Unfinished parser state MSECTION'),
#)

##############
parse('<!DOCTYPE>')(('handle_decl', ('DOCTYPE', '', '<!DOCTYPE>')),)
parse('<!DOCTYPE html>')(
    ('handle_decl', ('DOCTYPE', 'html', '<!DOCTYPE html>')),
)
parse('<!DOCTYPE \thtml\f \n>')(
    ('handle_decl', ('DOCTYPE', 'html', '<!DOCTYPE \thtml\f \n>')),
)
parse('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">')(
    ('handle_decl', (
        'DOCTYPE',
        'html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"',
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'
    )),
)
parse("<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Transitional//EN' 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd'>")(
    ('handle_decl', (
        'DOCTYPE',
        "html PUBLIC '-//W3C//DTD XHTML 1.0 Transitional//EN' 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd'",
        "<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Transitional//EN' 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd'>"
    )),
)
parse('<!DOCTYPE html -- some comment -- >')(
    ('handle_decl', (
        'DOCTYPE',
        'html -- some comment --',
        '<!DOCTYPE html -- some comment -- >'
    )),
)
parse('<!DOCTYPE html -- some co"mment -- >')(
    ('handle_decl', (
        'DOCTYPE',
        'html -- some co"mment --',
        '<!DOCTYPE html -- some co"mment -- >'
    )),
)
parse('<!DOCTYPE html -- some comment -a >')(
    ('LexerEOFError', 'Unfinished parser state DECL'),
)
parse('<!DOCTYPE html -- some comment -a -- >')(
    ('handle_decl', (
        'DOCTYPE',
        'html -- some comment -a --',
        '<!DOCTYPE html -- some comment -a -- >'
    )),
)
parse('<!DOCTYPE html -- some comment -- -a >')(
    ('handle_decl', (
        'DOCTYPE',
        'html -- some comment -- -a',
        '<!DOCTYPE html -- some comment -- -a >'
    )),
)
parse('''<!DOCTYPE html [
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
parse('<!DOCTYPE html -- some comment -- <![CDATA[ lalala ]]> -a >')(
    ('handle_decl', (
        'DOCTYPE',
        'html -- some comment -- <![CDATA[ lalala ]]> -a',
        '<!DOCTYPE html -- some comment -- <![CDATA[ lalala ]]> -a >'
    )),
)
parse('<!DOCTYPE html -- some comment -- <![CDATA[ l" --alala ]]> -a >')(
    ('handle_decl', (
        'DOCTYPE',
        'html -- some comment -- <![CDATA[ l" --alala ]]> -a',
        '<!DOCTYPE html -- some comment -- <![CDATA[ l" --alala ]]> -a >'
    )),
)

#####################
parse('<bR>lalala')(
    ('handle_starttag', ('bR', [], False, '<bR>')),
    ('handle_endtag', ('bR', '')),
    ('handle_text', ('lalala',))
)
parse('<bR/>lalala')(
    ('handle_starttag', ('bR', [], True, '<bR/>')),
    ('handle_text', ('lalala',))
)
parse('<Br><br><p>yo<s>no</div>')(
    ('handle_starttag', ('Br', [], False, '<Br>')),
    ('handle_endtag', ('Br', '')),
    ('handle_starttag', ('br', [], False, '<br>')),
    ('handle_endtag', ('br', '')),
    ('handle_starttag', ('p', [], False, '<p>')),
    ('handle_text', ('yo',)),
    ('handle_starttag', ('s', [], False, '<s>')),
    ('handle_text', ('no',)),
    ('handle_endtag', ('div', '</div>')),
    ('handle_endtag', ('s', '')),
    ('handle_endtag', ('p', ''))
)
parse('<Br><br><p>yo<s>no</p></div>')(
    ('handle_starttag', ('Br', [], False, '<Br>')),
    ('handle_endtag', ('Br', '')),
    ('handle_starttag', ('br', [], False, '<br>')),
    ('handle_endtag', ('br', '')),
    ('handle_starttag', ('p', [], False, '<p>')),
    ('handle_text', ('yo',)),
    ('handle_starttag', ('s', [], False, '<s>')),
    ('handle_text', ('no',)),
    ('handle_endtag', ('s', '')),
    ('handle_endtag', ('p', '</p>')),
    ('handle_endtag', ('div', '</div>'))
)
parse('<div><Br><br><p>yo<s>no</div>')(
    ('handle_starttag', ('div', [], False, '<div>')),
    ('handle_starttag', ('Br', [], False, '<Br>')),
    ('handle_endtag', ('Br', '')),
    ('handle_starttag', ('br', [], False, '<br>')),
    ('handle_endtag', ('br', '')),
    ('handle_starttag', ('p', [], False, '<p>')),
    ('handle_text', ('yo',)),
    ('handle_starttag', ('s', [], False, '<s>')),
    ('handle_text', ('no',)),
    ('handle_endtag', ('s', '')),
    ('handle_endtag', ('p', '')),
    ('handle_endtag', ('div', '</div>'))
)
parse('<div><br><p>yo<s>no<br></div>')(
    ('handle_starttag', ('div', [], False, '<div>')),
    ('handle_starttag', ('br', [], False, '<br>')),
    ('handle_endtag', ('br', '')),
    ('handle_starttag', ('p', [], False, '<p>')),
    ('handle_text', ('yo',)),
    ('handle_starttag', ('s', [], False, '<s>')),
    ('handle_text', ('no',)),
    ('handle_starttag', ('br', [], False, '<br>')),
    ('handle_endtag', ('br', '')),
    ('handle_endtag', ('s', '')),
    ('handle_endtag', ('p', '')),
    ('handle_endtag', ('div', '</div>'))
)
parse('<br><!--yo -->')(
    ('handle_starttag', ('br', [], False, '<br>')),
    ('handle_endtag', ('br', '')),
    ('handle_comment', ('<!--yo -->',))
)
parse('<x><!--yo -->')(
    ('handle_starttag', ('x', [], False, '<x>')),
    ('handle_comment', ('<!--yo -->',)),
    ('handle_endtag', ('x', ''))
)
parse('<br><![cdata [lalala ]]>')(
    ('handle_starttag', ('br', [], False, '<br>')),
    ('handle_endtag', ('br', '')),
    ('handle_msection', ('cdata', 'lalala ', '<![cdata [lalala ]]>'))
)
parse('<x><![cdata [lalala ]]>')(
    ('handle_starttag', ('x', [], False, '<x>')),
    ('handle_msection', ('cdata', 'lalala ', '<![cdata [lalala ]]>')),
    ('handle_endtag', ('x', ''))
)
parse('<br><!doctype html>')(
    ('handle_starttag', ('br', [], False, '<br>')),
    ('handle_endtag', ('br', '')),
    ('handle_decl', ('doctype', 'html', '<!doctype html>'))
)
parse('<x><!doctype html>')(
    ('handle_starttag', ('x', [], False, '<x>')),
    ('handle_decl', ('doctype', 'html', '<!doctype html>')),
    ('handle_endtag', ('x', ''))
)
parse('<br><? yo! ?>')(
    ('handle_starttag', ('br', [], False, '<br>')),
    ('handle_endtag', ('br', '')),
    ('handle_pi', ('<? yo! ?>',))
)
parse('<x><? yo! ?>')(
    ('handle_starttag', ('x', [], False, '<x>')),
    ('handle_pi', ('<? yo! ?>',)),
    ('handle_endtag', ('x', ''))
)
parse('<p>xxx<div>yyy<div>zzz')(
    ('handle_starttag', ('p', [], False, '<p>')),
    ('handle_text', ('xxx',)),
    ('handle_endtag', ('p', '')),
    ('handle_starttag', ('div', [], False, '<div>')),
    ('handle_text', ('yyy',)),
    ('handle_starttag', ('div', [], False, '<div>')),
    ('handle_text', ('zzz',)),
    ('handle_endtag', ('div', '')),
    ('handle_endtag', ('div', ''))
)
parse('<p>lalala<s></P>xxx')(
    ('handle_starttag', ('p', [], False, '<p>')),
    ('handle_text', ('lalala',)),
    ('handle_starttag', ('s', [], False, '<s>')),
    ('handle_endtag', ('s', '')),
    ('handle_endtag', ('P', '</P>')),
    ('handle_text', ('xxx',)),
)

# vim: nowrap
