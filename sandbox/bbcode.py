#!/usr/bin/env python
# -*- coding: latin-1 -*-

import re as _re

from tdi import LexerError
from tdi import encoder as _encoder
from tdi import filters as _filters
from tdi import builder as _builder
from tdi import parser as _parser
from tdi import template as _template
from tdi import util as _util


class DTD(object):
    def cdata(self, name):
        return name in ('code', 'plain', 'img')

    def nestable(self, outer, inner):
        if inner in ('quote', 'list') and outer != 'quote':
            return False
        if inner == '*' and outer != 'list':
            return False
        if inner == 'url' and outer == 'url':
            return False
        return True

    def empty(self, name):
        return False

    def closed(self, name, attrs):
        return name == 'smiley'

    # Extensions
    def attr(self, name):
        return name in ('list', 'quote', 'url')

    def optional(self, name):
        return name == '*'

_dtd = DTD()


class BBCodeLexer(_parser.SoupLexer):

    def finalize(self):
        try:
            super(BBCodeLexer, self).finalize()
        except LexerError:
            data, self._buffer = self._buffer, ''
            self._listener.handle_text(data)
            super(BBCodeLexer, self).finalize()

    def _lex_text(self):
        data = self._buffer
        pos = data.find('[')
        if pos == 0:
            self.state = self.MARKUP
            return False
        elif pos == -1:
            self._buffer = ''
        else:
            self._buffer, data = data[pos:], data[:pos]
            self.state = self.MARKUP

        self._listener.handle_text(data)
        return False

    def _lex_cdata(self):
        incomplete = False
        data = self._buffer
        pos = data.find('[')
        if pos == -1:
            pos, self._buffer = len(data), ''
        else:
            char = data[pos + 1:pos + 2]
            if char == '/':
                self.state = self.ENDTAG
            elif char == '':
                incomplete = True
            else:
                pos += 1

        if pos > 0:
            self._buffer, data = data[pos:], data[:pos]
            self._listener.handle_text(data)

        return incomplete

    def _lex_markup(self):
        data = self._buffer
        if len(data) < 2:
            return True

        char = data[1]
        if char == '/':
            self.state = self.ENDTAG
        else:
            if char.isalpha() or char == '*':
                self.state = self.STARTTAG
            else:
                self.state = self.TEXT
                self._listener.handle_text(data[0])
                self._buffer = data[1:]
        return False

    _STARTMATCH = _re.compile(r'''
        \[
            (?P<name>[^\s=\]]+)
            \s*
            (?:
                = \s*
                (?P<attr>
                      "[^"\\]*(?:\\["\\][^"\\]*)*"
                    | '[^'\\]*(?:\\['\\][^'\\]*)*'
                    | [^\s\]]*
                )
                \s*
            )?
        \]
    ''', _re.X).match
    _ATTRSUB_D = _re.compile(r'\\([\\"])').sub
    _ATTRSUB_S = _re.compile(r"\\([\\'])").sub
    def _lex_start(self):
        data = self._buffer
        match = self._STARTMATCH(data)
        if match is None:
            return True

        pos = match.end()
        self._buffer, data = data[pos:], data[:pos]

        name, attr = match.group('name', 'attr')
        if attr:
            if attr.startswith('"') and attr.endswith('"'):
                attr = self._ATTRSUB_D(lambda m: m.group(1), attr[1:-1])
            elif attr.startswith("'") and attr.endswith("'"):
                attr = self._ATTRSUB_S(lambda m: m.group(1), attr[1:-1])

        self.state = self.TEXT
        self._listener.handle_starttag(name, [(name, attr)], data)
        return False

    def _lex_end(self):
        data = self._buffer
        pos = data.find(']') + 1
        if pos == 0:
            return True

        self._buffer, data = data[pos:], data[:pos]
        name = data[2:-1].strip()

        self.state = self.TEXT
        self._listener.handle_endtag(name, data)
        return False


class BBCodeParser(_parser.SoupParser):
    def __init__(self, builder, dtd=_dtd, lexer=BBCodeLexer):
        super(BBCodeParser, self).__init__(builder, dtd=dtd, lexer=lexer)


class NewlineFilter(_filters.BaseEventFilter):
    def __init__(self, builder, dtd):
        super(NewlineFilter, self).__init__(builder)
        self._text = []
        self._nlre = _re.compile(u'(\r?\n)+').search
        self._dtd = dtd
        self._tagstack = [('', None)]

    def _flush_text(self):
        data, self._text = ''.join(self._text), []
        name, attr = self._tagstack[-1]
        check = not(
            self._dtd.cdata(name) or (name == 'url' and attr[0][1] is None)
        )
        matcher, data = self._nlre, data.decode('utf-8')
        while check:
            match = matcher(data)
            if match is None:
                break
            nl = match.group(0).replace(u'\r', u'')
            before, data = data[:match.start()], data[match.end():]
            if before:
                self.builder.handle_text(before.encode('utf-8'))
            if len(nl) > 1:
                nl, data = nl[:1], u'\xa0' + nl[1:] + data
            self.builder.handle_starttag('br', [], '[br]')
            self.builder.handle_endtag('br', '')
        if data:
            self.builder.handle_text(data.encode('utf-8'))

    def finalize(self):
        self._flush_text()
        return self.builder.finalize()

    def handle_text(self, data):
        self._text.append(data)

    def handle_starttag(self, name, attr, data):
        self._flush_text()
        self._tagstack.append((name, attr))
        self.builder.handle_starttag(name, attr, data)

    def handle_endtag(self, name, data):
        self._flush_text()
        self._tagstack.pop()
        self.builder.handle_endtag(name, data)


class NewlineFilterFactory(object):
    def __init__(self, dtd=_dtd):
        self._dtd = dtd

    def __call__(self, builder):
        return NewlineFilter(builder, self._dtd)


class SmileyFilter(_filters.BaseEventFilter):

    def __init__(self, builder, smilies, dtd):
        super(SmileyFilter, self).__init__(builder)
        self._text = []
        self._smileyre = _re.compile(u'(^|[^\w])(%s)' % u'|'.join(
            _re.escape(unicode(key, 'utf-8')) for key in
            sorted(smilies.iterkeys(), key=len, reverse=True)
        ), _re.U).search
        self._dtd = dtd
        self._tagstack = [('', None)]

    def _flush_text(self):
        data, self._text = ''.join(self._text), []
        name, attr = self._tagstack[-1]
        check = not(
            self._dtd.cdata(name) or (name == 'url' and attr[0][1] is None)
        )
        matcher, data = self._smileyre, data.decode('utf-8')
        while check:
            match = matcher(data)
            if match is None:
                break
            prefix, smile = match.group(1, 2)
            before, data = data[:match.start()], data[match.end():]
            before += prefix
            if before:
                self.builder.handle_text(before.encode('utf-8'))
            self.builder.handle_starttag('smiley', [('smiley',
                '"%s"' % smile.replace('\\', '\\\\').replace('"', '\\"')
            )], smile)
            self.builder.handle_endtag('smiley', '')
        if data:
            self.builder.handle_text(data.encode('utf-8'))

    def finalize(self):
        self._flush_text()
        return self.builder.finalize()

    def handle_text(self, data):
        self._text.append(data)

    def handle_starttag(self, name, attr, data):
        self._flush_text()
        self._tagstack.append((name, attr))
        self.builder.handle_starttag(name, attr, data)

    def handle_endtag(self, name, data):
        self._flush_text()
        self._tagstack.pop()
        self.builder.handle_endtag(name, data)


class SmileyFilterFactory(object):
    def __init__(self, smilies, dtd=_dtd):
        self._smilies = smilies
        self._dtd = dtd

    def __call__(self, builder):
        return SmileyFilter(builder, self._smilies, self._dtd)


class TidyFilter(_filters.BaseEventFilter):
    def __init__(self, builder):
        super(TidyFilter, self).__init__(builder)
        self._tagstack = []
        self._dtd = _dtd

    def handle_starttag(self, name, attr, data):
        name = name.lower()
        self._tagstack.append(name)
        attr = attr and attr[0][1]
        if not self._dtd.attr(name):
            attr = None

        astring = attr and \
            '="%s"' % attr.replace('\\', '\\\\').replace('"', '\\"') or ""
        data = "[%s%s]" % (name, astring)
        self.builder.handle_starttag(name, [(name, attr)], data)

    def handle_endtag(self, name, data):
        name = name.lower()
        if self._tagstack and self._tagstack[-1] == name:
            self._tagstack.pop()
            if self._dtd.optional(name):
                data = ''
            else:
                data = '[/%s]' % name
            self.builder.handle_endtag(name, data)


class _encode(object):
    def __init__(self):
        self._encode = _encode = _encoder.SoupEncoder('ascii')
        self.starttag = _encode.starttag
        self.endtag = _encode.endtag

    def attribute(self, value):
        return self._encode.attribute(value.decode('utf-8'))

    def content(self, value):
        return self._encode.content(value.decode('utf-8'))
_encode = _encode()


class Node(list):
    def render(self, builder):
        text = []
        for item in self:
            if isinstance(item, TextNode):
                text.append(item.text)
            else:
                if text:
                    builder.handle_text(_encode.content(''.join(text)))
                    text = []
                item.render(builder)
        if text:
            builder.handle_text(_encode.content(''.join(text)))


class EncodedTextNode(Node):
    def __init__(self, text):
        self.text = text

    def render(self, builder):
        builder.handle_text(self.text)


class TextNode(EncodedTextNode):
    pass


class ElementNode(Node):
    def __init__(self, tag):
        self.tag = tag

    def render(self, builder):
        self.tag.render_starttag(self, builder)
        super(ElementNode, self).render(builder)
        self.tag.render_endtag(self, builder)


class TagFilter(_filters.BaseEventFilter):

    def __init__(self, builder, tags):
        super(TagFilter, self).__init__(builder)
        self._tags = dict((tag.name, tag) for tag in tags)
        self._nodestack = [Node()]

    def handle_text(self, data):
        self._nodestack[-1].append(TextNode(data))

    def handle_starttag(self, name, attr, data):
        if name in self._tags:
            self._nodestack.append(self._tags[name](attr))
            self._nodestack[-1].starttag = data
        else:
            self.handle_text(data)

    def handle_endtag(self, name, data):
        if name in self._tags:
            node = self._nodestack.pop()
            node.endtag = data
            self._nodestack[-1].append(node)
        else:
            self.handle_text(data)

    def finalize(self):
        self._nodestack.pop().render(self.builder)
        return self.builder.finalize()


class TagFilterFactory(object):
    def __init__(self, tags):
        self._tags = tags

    def __call__(self, builder):
        return TagFilter(builder, self._tags)


class SimpleTag(object):
    def __init__(self, name, newname=None, attr=()):
        self.name = name
        self.newname, self.attr = newname or name, attr

    def __call__(self, attr):
        return ElementNode(self)

    def render_starttag(self, node, builder):
        builder.handle_starttag(
            self.newname, self.attr, _encode.starttag(
            self.newname, self.attr, ''
        ))

    def render_endtag(self, node, builder):
        builder.handle_endtag(self.newname, _encode.endtag(self.newname))


class SmileyTag(SimpleTag):
    def __init__(self, name, newname=None, attr=(), smilies=None):
        if smilies is None:
            raise TypeError("Smilies must be set")
        super(SmileyTag, self).__init__(name, newname, attr)
        self.smilies = smilies
        self.smilies_reverse = dict((value, key) for key, value in
            smilies.iteritems())

    def __call__(self, attr):
        name = attr[0][1][1:-1].replace('\\"', '"').replace('\\\\', '\\')
        oname = self.smilies.get(name, name)
        smiley = SimpleTag(self.name, self.newname, [
            ('tdi', '"-forget"'), ('tdi:overlay', '"smilies.%s"' % oname)
        ])
        node = ElementNode(smiley)
        node.append(TextNode(self.smilies_reverse.get(name, name)))
        return node


class ListTag(SimpleTag):

    def __call__(self, attr):
        if attr[0][1] is not None:
            try:
                int(attr[0][1])
            except (ValueError, TypeError):
                kind = 'a'
            else:
                kind = None
            name, attr = 'ol', kind and [('type', '"%s"' % kind)] or []
        else:
            name, attr = 'ul', []
        slist = SimpleTag(self.name, name, attr)
        return ElementNode(slist)


class CodeTag(SimpleTag):

    def render_starttag(self, node, builder):
        super(CodeTag, self).render_starttag(node, builder)
        node[:] = [EncodedTextNode(
            _util.multiline_to_html(u''.join(item.text for item in node))
        )]


class QuoteTag(SimpleTag):

    def __call__(self, attr):
        node = ElementNode(self)
        attr = attr[0][1]
        if attr is not None:
            cite = ElementNode(SimpleTag('p'))
            cite.append(TextNode("%s wrote:" % attr))
            node.append(cite)
        return node


class ImgTag(SimpleTag):
    def __init__(self, name, newname=None, attr=(), allowed=('http', 'https')):
        super(ImgTag, self).__init__(name, newname, attr)
        self.allowed = set(item.lower() for item in allowed)

    def __call__(self, attr):
        return ElementNode(self.__class__(
            self.name, self.newname, self.attr, self.allowed
        ))

    def render_starttag(self, node, builder):
        import urlparse
        url = urlparse.urlparse(''.join(item.text for item in node).strip())
        if url[0] in self.allowed:
            url = _encode.attribute(urlparse.urlunparse(url))
            name, attr = self.newname, [('src', url), ('alt', '""'),
                ('class', '"bbcodeImage"'), ('/', None)]
            builder.handle_starttag(name, attr, _encode.starttag(
                name, attr, ''
            ))
            node[:] = []
        else:
            builder.handle_text(_encode.content(node.starttag))
            self.render_endtag = self.render_endtag_text

    def render_endtag(self, node, builder):
        builder.handle_endtag(self.newname, '')

    def render_endtag_text(self, node, builder):
        builder.handle_text(_encode.content(node.endtag))


class BrTag(SimpleTag):

    def render_starttag(self, node, builder):
        builder.handle_starttag(
            self.newname, [('/', None)], _encode.starttag(
                self.newname, [], ' /')
        )

    def render_endtag(self, node, builder):
        builder.handle_endtag(self.newname, '')


class URLTag(SimpleTag):
    def __init__(self, name, newname=None, attr=(),
                 allowed=('http', 'https', 'ftp', 'mailto', '')):
        super(URLTag, self).__init__(name, newname, attr)
        self.allowed = set(item.lower() for item in allowed)

    def __call__(self, attr):
        anchor = self.__class__(
            self.name, self.newname, self.attr, self.allowed
        )
        anchor.attr = [('href', attr[0][1])]
        return ElementNode(anchor)

    def render_starttag(self, node, builder):
        url = self.attr[0][1]
        if url is None:
            parts = []
            for part in node:
                if isinstance(part, TextNode):
                    parts.append(part.text)
                else:
                    break
            else:
                url = ''.join(parts)
        else:
            url = url.replace('\\"', '"').replace('\\\\', '\\')
        if url is not None:
            url = url.strip()
            if url:
                import urlparse
                url = urlparse.urlparse(url)
                if url[0].lower() in self.allowed:
                    url = _encode.attribute(urlparse.urlunparse(url))
                    attr=[('href', url), ('rel', '"nofollow"')]
                    builder.handle_starttag(self.newname, attr,
                        _encode.starttag(self.newname, attr, ''))
                    return
        builder.handle_text(_encode.content(node.starttag))
        self.render_endtag = self.render_endtag_text

    def render_endtag_text(self, node, builder):
        builder.handle_text(_encode.content(node.endtag))


_tags = [
    SimpleTag('b'),
    SimpleTag('i'),
    SimpleTag('u'),
    SimpleTag('s'),
    SimpleTag('*', 'li'),
    BrTag('br'),
    ListTag('list'),
    CodeTag('code'),
    QuoteTag('quote', 'div', [('class', '"quote"')]),
    ImgTag('img'),
    URLTag('url', 'a'),
]

_smilies = {
    ':-)': 'smile',
    ':)': 'smile',
    ':(': 'sad',
    '8-)': 'laugh',
    ':D': 'bigsmile',
    ':-@': 'angry',
    ':\\': 'thinking',
    ';-)': 'wink',
    ':-o': 'gasp',
    ':-*': 'kiss',
    ':p': 'tongue',
    ':P': 'tongue',
    ';-(': 'cry',
    ':-O': 'yawn',
}

def bb2html(data, smiley_overlay=None, smilies=None, tags=None):
    """ BBCode -> HTML converter """
    data = data.encode('utf-8')
    if tags is None:
        tags = _tags
    if smilies is None:
        smilies = _smilies
    tags = list(tags) + [SmileyTag('smiley', 'span', smilies=smilies)]
    bbcode = _template.Factory(parser=BBCodeParser, eventfilters=(
        TagFilterFactory(tags),
        NewlineFilterFactory(),
        SmileyFilterFactory(smilies),
        TidyFilter,
    ))
    t = bbcode.from_string(data)
    if smiley_overlay is not None:
        t = t.overlay(smiley_overlay)
    return t.render_string().decode('utf-8')


def _test():
    """ Smoke test """
    print bb2html(u"""
        [b]fett alter![/b]

        [url="http://www.billiger.de/"]Hier wirds g\xfcnstig :-)[/url]
    """)

if __name__ == '__main__':
    _test()
