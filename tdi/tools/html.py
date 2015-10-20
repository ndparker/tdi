# -*- coding: ascii -*-
r"""
:Copyright:

 Copyright 2006 - 2015
 Andr\xe9 Malo or his licensors, as applicable

:License:

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.

============
 HTML Tools
============

HTML Tools.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"
__all__ = [
    'decode', 'entities', 'class_add', 'class_del', 'multiline',
    'CommentStripFilter', 'MinifyFilter', 'minify'
]

import codecs as _codecs
import re as _re
try:
    import cStringIO as _string_io
except ImportError:
    import StringIO as _string_io

from .._exceptions import LexerError
from .. import factory as _factory
from .. import filters as _filters
from .. import interfaces as _interfaces
from ..markup.soup import dtd as _dtd
from ..markup.soup import encoder as _encoder
from ..markup.soup import decoder as _decoder
from ..markup.soup import parser as _parser
from . import css as _css
from . import javascript as _javascript
from .._htmldecode import decode
from .._htmlentities import htmlentities as entities


#: HTML named character references, generated from
#: `the HTML5 spec`_\.
#:
#: .. _the HTML5 spec: http://www.w3.org/TR/html5/
#:    syntax.html#named-character-references
#:
#: :Type: ``dict``
entities = dict(entities)


def class_add(node, *class_):
    """
    Add class(es) to a node's class attribute

    :Parameters:
      `node` : TDI node
        The node to modify

      `class_` : ``tuple``
        Class name(s) to add
    """
    try:
        old = decode(node[u'class'], node.raw.encoder.encoding).split()
    except KeyError:
        class_ = u' '.join(class_)
    else:
        class_ = u' '.join(old + list(class_))
    if class_:
        node[u'class'] = class_
    else:
        del node[u'class']


def class_del(node, *class_):
    """
    Remove class(es) from node's class attribute

    :Parameters:
      `node` : TDI node
        The node to modify

      `class_` : ``tuple``
        Class name(s) to remove. It is *not* an error if a class is not
        defined before.
    """
    try:
        old = decode(node[u'class'], node.raw.encoder.encoding).split()
    except KeyError:
        pass
    else:
        class_ = u' '.join([item for item in old if item not in class_])
        if class_:
            node[u'class'] = class_
        else:
            del node[u'class']


def _make_multiline():
    """ Make multiline encoder """

    divmod_, len_ = divmod, len

    def space_func(match):
        """ Space filler """
        length, rest = divmod_(len_(match.group(0)), 2)
        if length == 0:
            return u' '
        return u'&nbsp;' * rest + u'&nbsp; ' * length
    ws_sub = _re.compile(ur'\s+').sub
    ws1_sub = _re.compile(ur'^\s(\S)').sub

    def multiline(content, encoding='ascii', tabwidth=8, xhtml=True):
        """
        Encode multiline content to HTML, assignable to ``node.raw.content``

        :Parameters:
          `content` : ``unicode``
            Content to encode

          `encoding` : ``str``
            Target encoding

          `tabwidth` : ``int``
            Tab width? Used to expand tabs. If ``None``, tabs are not
            expanded.

          `xhtml` : ``bool``
            XHTML? Only used to determine if <br> or <br /> is emitted.

        :Return: The multilined content
        :Rtype: ``str``
        """
        # pylint: disable = redefined-outer-name

        content = (
            content
            .replace(u'&', u'&amp;')
            .replace(u'<', u'&lt;')
            .replace(u'>', u'&gt;')
        )
        lines = []
        for line in content.splitlines():
            line = line.rstrip()
            if not line:
                line = u'&nbsp;'
            else:
                if tabwidth is not None:
                    line = line.expandtabs(tabwidth)
                line = ws1_sub(ur'&nbsp;\1', line)
                line = ws_sub(space_func, line)
            lines.append(line)
        if xhtml:
            res = u'<br />'.join(lines)
        else:
            res = u'<br>'.join(lines)
        return res.encode(encoding, 'xmlcharrefreplace')

    return multiline

multiline = _make_multiline()


class CommentStripFilter(_filters.BaseEventFilter):
    """ Strip comments from the event chain """

    def handle_comment(self, data):
        """ :See: `tdi.interfaces.ListenerInterface` """
        pass


class MinifyFilter(_filters.BaseEventFilter):
    """
    Strip unneeded whitespace and comments

    :IVariables:
      `_buffer` : ``list``
        Current text buffer

      `_stack` : ``list``
        Current tag stack

      `_last` : ``str``
        Last seen endtag name (normalized) or ``None``

      `_blocks` : ``dict``
        List of block elements (in a dict for better lookup)
    """

    def __init__(self, builder, comment_filter=None):
        """
        Initialization

        :Parameters:
          `builder` : `BuildingListenerInterface`
            Next level builder.

          `comment_filter` : callable
            Comment filter. A function which takes the comment data and
            returns a filtered comment (which is passed through to the
            builder) or ``None`` (meaning the comment can be stripped
            completely). For example::

                def keep_ad_comments(data):
                    if 'google_ad_section' in data:
                        return data
                    return None

            If omitted or ``None``, all comments are stripped.
        """
        super(MinifyFilter, self).__init__(builder)
        self._buffer = []
        self._stack = []
        self._last = None
        self._dtd = _dtd.HTMLDTD()
        self._normalize = self.builder.decoder.normalize
        if comment_filter is None:
            comment_filter = lambda x: None
        self._comment_filter = comment_filter
        self._blocks = dict([(item, None) for item in (
            'address',
            'article',
            'aside',
            'blockquote',
            'body',
            'caption',
            'col',
            'colgroup',
            'dd',
            'dir',
            'div',
            'dl',
            'dt',
            'fieldset',
            'figcaption',
            'figure',
            'footer',
            'form',
            'frame',
            'frameset',
            'h1',
            'h2',
            'h3',
            'h4',
            'h5',
            'h6',
            'head',
            'header',
            'hgroup',
            'hr',
            'html',
            'isindex',
            'layer',
            'li',
            'listing',
            'map',
            'marquee',
            'menu',
            'multicol',
            'nav',
            'noframes',
            'ol',
            'option',
            'p',
            'script',
            'style',
            'section',
            'table',
            'tbody',
            'td',
            'title',
            'tfoot',
            'th',
            'thead',
            'tr',
            'ul',
            'xmp',
        )])

    #: Whitespace substitutor
    #:
    #: :Type: ``callable``
    _WS_SUB = _re.compile(r'\s+').sub

    def _flush(self, endtag=False, starttag=None):
        """
        Flush the current text buffer to the builder

        :Parameters:
          `endtag` : ``bool``
            Endtag flush?

          `starttag` : ``str``
            Next starttag (normalized) if starttag flush
        """
        if self._buffer:
            self._buffer, buf, stack = [], ''.join(self._buffer), self._stack
            if stack and \
                    (self._dtd.cdata(stack[-1]) or stack[-1] == 'pre'):
                if stack[-1] == 'pre':
                    buf = [
                        line.rstrip()
                        for line in buf.rstrip().splitlines(False)
                    ]
                elif stack[-1] in ('script', 'style'):
                    buf = buf.strip().splitlines(False)
                else:
                    buf = buf.splitlines(False)
                buf = '\n'.join(buf)
            else:
                buf = self._WS_SUB(' ', buf)
                if self._last in self._blocks:
                    buf = buf.lstrip()
                if (endtag and stack and stack[-1] in self._blocks) \
                        or starttag in self._blocks:
                    buf = buf.rstrip()
            self.builder.handle_text(buf)

    def finalize(self):
        """
        Flush the last chunk

        :See: `tdi.interfaces.BuilderInterface`
        """
        self._flush(starttag=self._blocks.keys()[0])
        return self.builder.finalize()

    def handle_text(self, data):
        """
        Buffer the text

        :See: `tdi.interfaces.ListenerInterface`
        """
        self._buffer.append(data)

    def handle_starttag(self, name, attr, closed, data):
        """ :See: `tdi.interfaces.ListenerInterface` """
        norm = self._normalize
        norm_name = norm(name)
        self._flush(False, norm_name)
        if not closed:
            self._stack.append(norm_name)
        newattr = [(norm(key), value) for key, value in attr]
        newattr.sort()
        data = self.encoder.starttag(
            norm_name, newattr, closed
        )
        self.builder.handle_starttag(norm_name, attr, closed, data)

    def handle_endtag(self, name, data):
        """ :See: `tdi.interfaces.ListenerInterface` """
        self._flush(True)
        norm_name, stack = self._normalize(name), self._stack
        if stack and norm_name == stack[-1]:
            self._last = stack.pop()
        if data:
            data = self.encoder.endtag(norm_name)
        self.builder.handle_endtag(norm_name, data)

    def handle_comment(self, data):
        """ :See: `tdi.interfaces.ListenerInterface` """
        data = self._comment_filter(data)
        if data is not None:
            self.builder.handle_comment(data)

    def handle_msection(self, name, value, data):
        """ :See: `tdi.interfaces.ListenerInterface` """
        self._flush()
        self.builder.handle_msection(name, value, data)

    def handle_decl(self, name, value, data):
        """ :See: `tdi.interfaces.ListenerInterface` """
        self._flush()
        self.builder.handle_decl(name, value, data)

    def handle_pi(self, data):
        """ :See: `tdi.interfaces.ListenerInterface` """
        self._flush()
        self.builder.handle_pi(data)


def minify(html, encoding='ascii', fail_silently=False, comment_filter=None,
           cdata_containers=False):
    """
    Minify HTML

    Enclosed <script> and <style> blocks are minified as well.

    :Parameters:
      `html` : ``basestring``
        HTML to minify

      `encoding` : ``str``
        Initially assumed encoding. Only marginally interesting.

      `fail_silently` : ``bool``
        Fail if a parse error is encountered? If true, the parse error is
        passed. Otherwise it's swallowed and the input html is returned.

      `comment_filter` : callable
        HTML Comment filter. A function which takes the comment data and
        returns a filtered comment (which is passed through to the
        builder) or ``None`` (meaning the comment can be stripped
        completely). For example::

            def keep_ad_comments(data):
                if 'google_ad_section' in data:
                    return data
                return None

        If omitted or ``None``, all HTML comments are stripped.

      `cdata_containers` : ``bool``
        Add CDATA containers to enclosed <script> or <style> content? If true,
        these containers are added after minimization of the content. Default
        is false.

    :Return: the minified HTML - typed as input
    :Rtype: ``basestring``
    """
    def js_minify(builder):
        """ Javascript minifier filter factory """
        return _javascript.MinifyFilter(builder, standalone=True)

    def js_cdata(builder):
        """ Javascript cdata container filter factory """
        return _javascript.CDATAFilter(builder, standalone=True)

    def css_minify(builder):
        """ CSS minifier filter factory """
        return _css.MinifyFilter(builder, standalone=True)

    def css_cdata(builder):
        """ CSS cdata container filter factory """
        return _css.CDATAFilter(builder, standalone=True)

    def html_minify(builder):
        """ HTML minifier filter factory """
        return MinifyFilter(builder, comment_filter=comment_filter)

    filters = cdata_containers and [js_cdata, css_cdata] or []
    isuni = isinstance(html, unicode)
    if isuni:
        html = html.encode('utf-8')
    try:
        result = _factory.Loader(
            builder=_StringBuilder,
            parser=_parser.SoupParser.html,
            encoder=_encoder.SoupEncoder,
            decoder=_decoder.HTMLDecoder,
            eventfilters=filters + [
                js_minify,
                css_minify,
                html_minify,
            ]
        )(_string_io.StringIO(html), '<string>', encoding)
    except LexerError:
        if not fail_silently:
            raise
        result = html
    if isuni:
        return result.decode('utf-8')
    return result


class _StringBuilder(object):
    """ String builder """
    __implements__ = [_interfaces.BuilderInterface,
                      _interfaces.BuildingListenerInterface]

    encoding = 'ascii'

    def __init__(self, encoder, decoder):
        """
        Initialization

        :Parameters:
          `encoder` : ``callable``
            Encoder factory

          `decoder` : ``callable``
            Decoder factory
        """
        self._result = []
        self.encoder = encoder(self.encoding)
        self.decoder = decoder(self.encoding)

    def handle_text(self, data):
        """ :see: `ListenerInterface` """
        self._result.append(data)

    def handle_escape(self, escaped, data):
        """ :see: `ListenerInterface` """
        # pylint: disable = unused-argument
        self._result.append(data)

    def handle_starttag(self, name, attr, closed, data):
        """ :see: `ListenerInterface` """
        # pylint: disable = unused-argument
        self._result.append(data)

    def handle_endtag(self, name, data):
        """ :see: `ListenerInterface` """
        # pylint: disable = unused-argument
        self._result.append(data)

    def handle_comment(self, data):
        """ :see: `ListenerInterface` """
        self._result.append(data)

    def handle_msection(self, name, value, data):
        """ :see: `ListenerInterface` """
        # pylint: disable = unused-argument
        self._result.append(data)

    def handle_decl(self, name, value, data):
        """ :see: `ListenerInterface` """
        # pylint: disable = unused-argument
        self._result.append(data)

    def handle_pi(self, data):
        """ :see: `ListenerInterface` """
        self._result.append(data)

    def handle_encoding(self, encoding):
        """ :See: `tdi.interfaces.BuildingListenerInterface` """
        try:
            _codecs.lookup(encoding)
        except LookupError:
            pass
        else:
            if self.encoding != encoding:
                self.encoding = encoding
                self.encoder.encoding = encoding
                self.decoder.encoding = encoding

    def finalize(self):
        """ :See: `tdi.interfaces.BuilderInterface` """
        return ''.join(self._result)
