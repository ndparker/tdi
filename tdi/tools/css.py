# -*- coding: ascii -*-
#
# Copyright 2006 - 2013
# Andr\xe9 Malo or his licensors, as applicable
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
===========
 CSS Tools
===========

CSS Tools.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

from tdi import filters as _filters
from tdi.tools._util import norm_enc as _norm_enc


def cleanup(style, encoding=None):
    """
    Cleanup a single CSS buffer

    This methods removes CDATA and starting/finishing comment containers.

    :Parameters:
      `style` : ``basestring``
        Buffer to cleanup

      `encoding` : ``str``
        Encoding in case that toescape is a ``str``. If omitted or
        ``None``, no encoding is applied and `style` is expected to be
        ASCII compatible.

    :Return: The cleaned up buffer, typed as input
    :Rtype: ``basestring``
    """
    isuni = isinstance(style, unicode)
    if not isuni:
        # don't decode ascii, but latin-1. just in case, if it's a
        # dumb default. Doesn't hurt here, but avoids failures.
        if encoding is None or _norm_enc(encoding) == 'ascii':
            encoding = 'latin-1'
        style = str(style).decode(encoding)
    style = style.strip()
    if style.startswith(u'<!--'):
        style = style[4:]
    if style.endswith(u'-->'):
        style = style[:-3]
    style = style.strip()
    if style.startswith(u'/*'):
        pos = style.find(u'*/')
        if pos >= 0:
            style = style[pos + 2:]
    if style.endswith(u'*/'):
        style = style[::-1]
        pos = style.find(u'*/')
        if pos >= 0:
            style = style[pos + 2:]
        style = style[::-1]
    style = style.strip()
    if style.startswith(u'<![CDATA['):
        style = style[len(u'<![CDATA['):]
    if style.endswith(u']]>'):
        style = style[:-3]
    style = style.strip()
    if isuni:
        return style
    return style.encode(encoding)


def cdata(style, encoding=None):
    """
    Add a failsafe CDATA container around a style

    See <http://lists.w3.org/Archives/Public/www-html/2002Apr/0053.html>
    for details.

    :Parameters:
      `style` : ``basestring``
        JS to contain

      `encoding` : ``str``
        Encoding in case that toescape is a ``str``. If omitted or
        ``None``, no encoding is applied and `style` is expected to be
        ASCII compatible.

    :Return: The contained style, typed as input
    :Rtype: ``basestring``
    """
    isuni = isinstance(style, unicode)
    if not isuni:
        # don't decode ascii, but latin-1. just in case, if it's a
        # dumb default. Doesn't hurt here, but avoids failures.
        if encoding is None or _norm_enc(encoding) == 'ascii':
            encoding = 'latin-1'
        style = str(style).decode(encoding)
    style = cleanup(style)
    if style:
        style = u'<!--/*--><![CDATA[/*><!--*/\n%s\n/*]]>*/-->' % style
    if isuni:
        return style
    return style.encode(encoding)


def minify(style, encoding=None):
    """
    Minify CSS (using `rcssmin`_)

    .. _rcssmin: http://opensource.perlig.de/rcssmin/

    :Parameters:
      `style` : ``basestring``
        CSS to minify

      `encoding` : ``str``
        Encoding in case that toescape is a ``str``. If omitted or
        ``None``, no encoding is applied and `style` is expected to be
        ASCII compatible.

    :Return: Minified CSS, typed as input
    :Rtype: ``basestring``
    """
    from tdi.tools import rcssmin as _rcssmin

    isuni = isinstance(style, unicode)
    if not isuni and encoding is not None:
        # don't decode ascii, but latin-1. just in case, if it's a
        # dumb default. Doesn't hurt here, but avoids failures.
        if _norm_enc(encoding) == 'ascii':
            encoding = 'latin-1'
        return _rcssmin.cssmin(style.decode(encoding)).encode(encoding)
    return _rcssmin.cssmin(style)


class CSSInlineFilter(_filters.BaseEventFilter):
    """
    TDI filter for modifying inline css

    :IVariables:
      `_collecting` : ``bool``
        Currently collecting CSS text?

      `_buffer` : ``list``
        Collection buffer

      `_starttag` : ``tuple`` or ``None``
        Original style starttag parameters

      `_modify` : callable
        Modifier function

      `_attribute` : ``str``
        ``tdi`` attribute name or ``None`` (if standalone)

      `_strip` : ``bool``
        Strip empty style elements?
    """

    def __init__(self, builder, modifier, strip_empty=True, standalone=False):
        """
        Initialization

        :Parameters:
          `builder` : `tdi.interfaces.BuildingListenerInterface`
            Builder

          `modifier` : callable
            Modifier function. Takes a style and returns the (possibly)
            modified result.

          `strip_empty` : ``bool``
            Strip empty style elements?

          `standalone` : ``bool``
            Standalone context? In this case, we won't watch out for TDI
            attributes.
        """
        super(CSSInlineFilter, self).__init__(builder)
        self._collecting = False
        self._buffer = []
        self._starttag = None
        self._modify = modifier
        self._normalize = self.builder.decoder.normalize
        if standalone:
            self._attribute = None
        else:
            self._attribute = self._normalize(
                self.builder.analyze.attribute
            )
        self._strip = strip_empty

    def handle_starttag(self, name, attr, closed, data):
        """
        Handle starttag

        Style starttags are delayed until the endtag is found. The whole
        element is then evaluated (and possibly thrown away).

        :See: `tdi.interfaces.ListenerInterface`
        """
        if not closed and self._normalize(name) == 'style':
            self._collecting = True
            self._buffer = []
            self._starttag = name, attr, closed, data
        else:
            self.builder.handle_starttag(name, attr, closed, data)

    def handle_endtag(self, name, data):
        """
        Handle endtag

        When currently collecting, it must be a style endtag. The style
        element content is then cleaned up (using `cleanup`) and then
        modified (using the modifiy function passed during initialization).
        The result replaces the original. If it's empty and the starttag
        does not provide a ``tdi`` attribute and the filter was
        configured to do so: the whole element is thrown away.

        :See: `tdi.interfaces.ListenerInterface`
        """
        if self._collecting:
            normalize = self._normalize
            if normalize(name) != 'style':
                raise AssertionError("Invalid event stream")

            self._collecting = False
            style, self._buffer = ''.join(self._buffer), []
            style = self._modify(cleanup(style))

            if not style and self._strip:
                attrdict = dict((normalize(name), val)
                    for name, val in self._starttag[1]
                )
                if self._attribute is None or self._attribute not in attrdict:
                    return

            self.builder.handle_starttag(*self._starttag)
            self._starttag = None
            self.builder.handle_text(style)

        self.builder.handle_endtag(name, data)

    def handle_text(self, data):
        """
        Handle text

        While collecting style text, the received data is buffered.
        Otherwise the event is just passed through.

        :See: `tdi.interfaces.ListenerInterface`
        """
        if not self._collecting:
            return self.builder.handle_text(data)
        self._buffer.append(data)


def MinifyFilter(builder, minifier=None, standalone=False):
    """
    TDI Filter for minifying inline CSS

    :Parameters:
      `minifier` : callable``
        Minifier function. If omitted or ``None``, the `builtin minifier`_ is
        applied.

        .. _builtin minifier: http://opensource.perlig.de/rcssmin/

      `standalone` : ``bool``
        Standalone context? In this case, we won't watch out for TDI
        attributes.
    """
    # pylint: disable = C0103
    if minifier is None:
        minifier = minify
    return CSSInlineFilter(builder, minify, standalone=standalone)


def CDATAFilter(builder, standalone=False): # pylint: disable = C0103
    """
    TDI filter for adding failsafe CDATA containers around CSS styles

    See <http://lists.w3.org/Archives/Public/www-html/2002Apr/0053.html>
    for details.

    :Parameters:
      `standalone` : ``bool``
        Standalone context? In this case, we won't watch out for TDI
        attributes.
    """
    return CSSInlineFilter(builder, cdata, standalone=standalone)
