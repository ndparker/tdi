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
==================
 Javascript Tools
==================

Javascript Tools.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import re as _re

from tdi import filters as _filters
from tdi import _htmldecode
from tdi.tools._util import norm_enc as _norm_enc


def _make_big_sub_b():
    """ Make bigsub """
    sub = _re.compile(r'(?<!\\)((?:\\\\)*)\\U([0-9a-fA-F]{8})').sub
    int_ = int
    return lambda v: sub(lambda m: "%s\\u%04x\\u%04x" % (
        m.group(1),
        ((((int_(m.group(2), 16) - 0x10000) >> 10) & 0x3FF) + 0xD800),
        ((int_(m.group(2), 16) & 0x3FF) + 0xDC00),
    ), v)

_big_sub_b = _make_big_sub_b()


def _make_big_sub():
    """ Make bigsub """
    sub = _re.compile(ur'(?<!\\)((?:\\\\)*)\\U([0-9a-fA-F]{8})').sub
    int_ = int
    return lambda v: sub(lambda m: u"%s\\u%04x\\u%04x" % (
        m.group(1),
        ((((int_(m.group(2), 16) - 0x10000) >> 10) & 0x3FF) + 0xD800),
        ((int_(m.group(2), 16) & 0x3FF) + 0xDC00),
    ), v)

_big_sub = _make_big_sub()


def _make_small_sub():
    """ Make small sub """
    sub = _re.compile(ur'(?<!\\)((?:\\\\)*)\\x([0-9a-fA-F]{2})').sub
    return lambda v: sub(lambda m: u"%s\\u00%s" % (
        m.group(1), m.group(2)
    ), v)

_small_sub = _make_small_sub()


def _make_escape_inlined():
    """ Make escape_inlined """
    dash_sub = _re.compile(ur'-(-+)').sub
    dash_sub_b = _re.compile(r'-(-+)').sub
    len_, str_, unicode_, isinstance_ = len, str, unicode, isinstance
    norm_enc = _norm_enc

    subber = lambda m: u'-' + u'\\-' * len_(m.group(1))
    subber_b = lambda m: '-' + '\\-' * len_(m.group(1))

    def escape_inlined(toescape, encoding=None): # pylint: disable = W0621
        """
        Escape value for inlining

        :Parameters:
          `toescape` : ``basestring``
            The value to escape

          `encoding` : ``str``
            Encoding in case that toescape is a ``str``. If omitted or
            ``None``, no encoding is applied and `toescape` is expected to be
            ASCII compatible.

        :Return: The escaped value, typed as input
        :Rtype: ``basestring``
        """
        if isinstance_(toescape, unicode_):
            return (dash_sub(subber, toescape)
                .replace(u'</', u'<\\/')
                .replace(u']]>', u']\\]>')
            )
        elif encoding is None:
            return (dash_sub_b(subber_b, str_(toescape))
                .replace('</', '<\\/')
                .replace(']]>', ']\\]>')
            )
        # don't decode ascii, but latin-1. just in case, if it's a
        # dumb default. Doesn't hurt here, but avoids failures.
        if norm_enc(encoding) == 'ascii':
            encoding = 'latin-1'
        return (dash_sub(subber, str_(toescape).decode(encoding))
            .replace(u'</', u'<\\/')
            .replace(u']]>', u']\\]>')
        ).encode(encoding)

    return escape_inlined

escape_inlined = _make_escape_inlined()


def _make_escape_string():
    """ Make escape_string function """
    big_sub_b = _big_sub_b
    unicode_, str_, isinstance_ = unicode, str, isinstance
    escape_inlined_, norm_enc = escape_inlined, _norm_enc

    need_solid = '\\'.encode('string_escape') == '\\'
    need_solid_u = u'\\'.encode('unicode_escape') == '\\'
    need_apos = "'".encode('string_escape') == "'"
    need_apos_u = u"'".encode('unicode_escape') == "'"
    need_quote = '"'.encode('string_escape') == '"'
    need_quote_u = u'"'.encode('unicode_escape') == '"'

    def escape_string(toescape, inlined=True, encoding=None):
        """
        Escape a string for JS output (to be inserted into a JS string)

        This function is one of the building blocks of the
        `tdi.tools.javascript.replace` function. You probably shouldn't
        use it directly in your rendering code.

        :See:
          - `tdi.tools.javascript.fill`
          - `tdi.tools.javascript.fill_attr`
          - `tdi.tools.javascript.replace`

        :Parameters:
          `toescape` : ``basestring``
            The string to escape

          `inlined` : ``bool``
            Do additional escapings (possibly needed for inlining the script
            within a HTML page)?

          `encoding` : ``str``
            Encoding in case that toescape is a ``str``. If omitted or
            ``None``, no encoding is applied and `toescape` is expected to be
            ASCII compatible.

        :Return: The escaped string (ascii)
        :Rtype: ``str``
        """
        # pylint: disable = W0621

        isuni = isinstance_(toescape, unicode_)
        if isuni or encoding is not None:
            if not isuni:
                # don't decode ascii, but latin-1. just in case, if it's a
                # dumb default. The result is similar to encoding = None.
                if norm_enc(encoding) == 'ascii':
                    encoding = 'latin-1'
                toescape = str_(toescape).decode(encoding)
            if need_solid_u:
                toescape = toescape.replace(u'\\', u'\\\\')
            result = big_sub_b(toescape.encode('unicode_escape'))
            if need_apos_u:
                result = result.replace("'", "\\'")
            if need_quote_u:
                result = result.replace('"', '\\"')
        else:
            result = str_(toescape)
            if need_solid:
                result = result.replace('\\', '\\\\')
            result = result.encode('string_escape')
            if need_apos:
                result = result.replace("'", "\\'")
            if need_quote:
                result = result.replace('"', '\\"')

        if inlined:
            return escape_inlined_(result)
        return result

    return escape_string

escape_string = _make_escape_string()


def _make_replace():
    """ Make replace function """
    # pylint: disable = R0912
    # (too many branches)

    default_sub = _re.compile(ur'__(?P<name>[^_]*(?:_[^_]+)*)__').sub
    escape_string_, getattr_, unicode_ = escape_string, getattr, unicode
    isinstance_, escape_inlined_, str_ = isinstance, escape_inlined, str
    big_sub, small_sub, norm_enc = _big_sub, _small_sub, _norm_enc

    def replace(script, holders, pattern=None, as_json=True, inlined=True,
                encoding=None):
        """
        Replace javascript values

        See `fill` and `fill_attr` for more specific usage.

        This functions provides safe (single pass) javascript value
        replacement::

            filled = javascript.replace(script_template, dict(
                a=10,
                b=u'Andr\\xe9',
                c=javascript.SimpleJSON(dict(foo='bar')),
            ))

        Where script_template is something like::

                // more script...
                var count = __a__;
                var name = '__b__';
                var param = __c__;
                // more script...

        :See:
          - `fill`
          - `fill_attr`

        :Parameters:
          `script` : ``basestring``
            Script content to modify

          `holders` : ``dict``
            Placeholders mappings (name -> value). If a placeholder is found
            within the script which has no mapping, it's simply left as-is.
            If `as_json` is true, the values are checked if they have an
            ``as_json`` method. *If* they do have one, the method is called
            and the result (of type ``unicode``) is used as replacement.
            Otherwise the mapped value is piped through the `escape_string`
            function and that result is used as replacement. ``as_json`` is
            passed a boolean ``inlined`` parameter which indicates whether the
            method should escape for inline usage or not.

            Use the `LiteralJSON` class for passing any JSON content literally
            to the script. There is also a `SimpleJSON` class for converting
            complex structures to JSON using the simplejson converter. You may
            pass your own classes as well, of course, as long as they provide
            a proper ``as_json()`` method.

          `pattern` : ``unicode`` or compiled ``re`` object
            Placeholder name pattern. If omitted or ``None``, the pattern is
            (simplified [#]_): ``__(?P<name>.+)__``, i.e. the placeholder name
            enclosed in double-underscores. The name group is expected.

            .. [#] The actual pattern is: ``__(?P<name>[^_]*(?:_[^_]+)*)__``

          `as_json` : ``bool``
            Check the placeholder values for an ``as_json`` method? See the
            description of the `holders` parameter for details.

          `inlined` : ``bool``
            Escape simple content for being inlined (e.g.
            no CDATA endmarkers, ``</script>``).

          `encoding` : ``str``
            Script encoding if `script` is a ``str``. If omitted or ``None``,
            the script is expected to be ASCII compatible.

            If ``script`` is of type ``unicode``, the encoding is applied to
            ``as_json`` method return values. This is to make sure, the JSON
            stuff is encoded safely. If omitted or ``None``, ASCII is assumed.
            JSON result characters not fitting into the this encoding are
            escaped (\\uxxxx).

        :Return: The modified script, typed as input
        :Rtype: ``basestring``
        """
        # pylint: disable = W0621
        if not holders:
            return script
        isuni = isinstance_(script, unicode_)
        if isuni:
            if encoding is None:
                json_encoding = 'ascii'
            else:
                json_encoding = encoding
        else:
            if encoding is None:
                encoding = 'latin-1'
                json_encoding = 'ascii'
            else:
                json_encoding = encoding
                # don't decode ascii, but latin-1. just in case, if it's a
                # dumb default. Doesn't hurt here, but avoids failures.
                if norm_enc(encoding) == 'ascii':
                    encoding = 'latin-1'
            script = str_(script).decode(encoding)
        if pattern is None:
            pattern = default_sub
        else:
            pattern = _re.compile(pattern).sub

        def simple_subber(match):
            """ Substitution function without checking .as_json() """
            name = match.group(u'name')
            if name and name in holders:
                return escape_string_(holders[name],
                    encoding=encoding, inlined=inlined
                ).decode('ascii')
            return match.group(0)

        def json_subber(match):
            """ Substitution function with .as_json() checking """
            name = match.group(u'name')
            if name and name in holders:
                value = holders[name]
                method = getattr_(value, 'as_json', None)
                if method is None:
                    return escape_string_(value,
                        encoding=encoding, inlined=inlined
                    ).decode('ascii')
                value = small_sub(big_sub(unicode_(method(inlined=False))
                    .encode(json_encoding, 'backslashreplace')
                    .decode(json_encoding)
                ))
                if inlined:
                    return escape_inlined_(value)
                return value
            return match.group(0)

        script = pattern(as_json and json_subber or simple_subber, script)
        if not isuni:
            return script.encode(encoding)
        return script

    return replace

replace = _make_replace()


def fill(node, holders, pattern=None, as_json=True):
    """
    Replace javascript values in a script node

    This functions provides safe (single pass) javascript value
    replacement (utilizing the `replace` function)::

        javascript.fill(node, dict(
            a=10,
            b=u'Andr\\xe9',
            c=javascript.SimpleJSON(dict(foo='bar')),
        ))

    Where `node` is something like::

        <script tdi="name">
            var count = __a__;
            var name = '__b__';
            var param = __c__;
        </script>

    :See:
      - `fill_attr`
      - `replace`

    :Parameters:
      `node` : TDI node
        The script node

      `holders` : ``dict``
        Placeholders mappings (name -> value). If a placeholder is found
        within the script which has no mapping, it's simply left as-is.
        If `as_json` is true, the values are checked if they have an
        ``as_json`` method. *If* they do have one, the method is called
        and the result (of type ``unicode``) is used as replacement.
        Otherwise the mapped value is piped through the `escape_string`
        function and the result is used as replacement. ``as_json`` is
        passed a boolean ``inlined`` parameter which indicates whether the
        method should escape for inline usage or not.

        Use the `LiteralJSON` class for passing any JSON content literally
        to the script. There is also a `SimpleJSON` class for converting
        complex structures to JSON using the simplejson converter. You may
        pass your own classes as well, of course, as long as they provide
        a proper ``as_json()`` method.

      `pattern` : ``unicode`` or compiled ``re`` object
        Placeholder name pattern. If omitted or ``None``, the pattern is
        (simplified [#]_): ``__(?P<name>.+)__``, i.e. the placeholder name
        enclosed in double-underscores. The name group is expected.

        .. [#] The actual pattern is: ``__(?P<name>[^_]*(?:_[^_]+)*)__``

      `as_json` : ``bool``
        Check the placeholder values for an ``as_json`` method? See the
        description of the `holders` parameter for details.
    """
    node.raw.content = replace(node.raw.content, holders,
        pattern=pattern,
        as_json=as_json,
        inlined=True,
        encoding=node.raw.encoder.encoding,
    )


def fill_attr(node, attr, holders, pattern=None, as_json=True):
    """
    Replace javascript values in a script attribute

    This functions provides safe (single pass) javascript value
    replacement (utilizing the `replace` function)::

        javascript.fill_attr(node, u'onclick', dict(
            a=10,
            b=u'Andr\\xe9',
            c=javascript.SimpleJSON(dict(foo='bar')),
        ))

    Where `node` is something like::

        <div onclick="return foo(__a__)">...</div>

    :See:
      - `fill`
      - `replace`

    :Parameters:
      `node` : TDI node
        The script node

      `attr` : ``basestring``
        The name of the attribute

      `holders` : ``dict``
        Placeholders mappings (name -> value). If a placeholder is found
        within the script which has no mapping, it's simply left as-is.
        If `as_json` is true, the values are checked if they have an
        ``as_json`` method. *If* they do have one, the method is called
        and the result (of type ``unicode``) is used as replacement.
        Otherwise the mapped value is piped through the `escape_string`
        function and that result is used as replacement. ``as_json`` is
        passed a boolean ``inlined`` parameter which indicates whether the
        method should escape for inline usage or not.

        Use the `LiteralJSON` class for passing any JSON content literally
        to the script. There is also a `SimpleJSON` class for converting
        complex structures to JSON using the simplejson converter. You may
        pass your own classes as well, of course, as long as they provide
        a proper ``as_json()`` method.

      `pattern` : ``unicode`` or compiled ``re`` object
        Placeholder name pattern. If omitted or ``None``, the pattern is
        (simplified [#]_): ``__(?P<name>.+)__``, i.e. the placeholder name
        enclosed in double-underscores. The name group is expected.

        .. [#] The actual pattern is: ``__(?P<name>[^_]*(?:_[^_]+)*)__``

      `as_json` : ``bool``
        Check the placeholder values for an ``as_json`` method? See the
        description of the `holders` parameter for details.
    """
    encoding = node.raw.encoder.encoding
    node[attr] = replace(
        _htmldecode.decode(node[attr], encoding=encoding), holders,
        pattern=pattern,
        as_json=as_json,
        inlined=False,
        encoding=encoding,
    )


class LiteralJSON(object):
    """
    Literal JSON container for use with `replace` or `fill`

    The container just passes its input back through as_json().

    :IVariables:
      `_json` : JSON input
        JSON input

      `_inlined` : ``bool``
        Escape for inlining?

      `_encoding` : ``str``
        Encoding of `_json`
    """

    def __init__(self, json, inlined=False, encoding=None):
        """
        Initialization

        :Parameters:
          `json` : ``basestring``
            JSON to output

          `inlined` : ``bool``
            Escape for inlining? See `escape_inlined` for details.

          `encoding` : ``str``
            Encoding of `json`, in case it's a ``str``. If omitted or ``None``
            and `json` is ``str``, `json` is expected to be UTF-8 encoded (or
            ASCII only, which is compatible here)
        """
        self._json = json
        self._inlined = bool(inlined)
        self._encoding = encoding

    def __repr__(self):
        """ Debug representation """
        return "%s(%r, inlined=%r, encoding=%r)" % (
            self.__class__.__name__,
            self._json, self._inlined, self._encoding
        )

    def as_json(self, inlined=None):
        """
        Content as JSON

        :Parameters:
          `inlined` : ``bool`` or ``None``
            escape for inlining? If omitted or ``None``, the default value
            from construction is used.

        :Return: JSON string
        :Rtype: ``unicode``
        """
        json = self._json
        if inlined is None:
            inlined = self._inlined
        if inlined:
            json = escape_inlined(json, encoding=self._encoding)
        if not isinstance(json, unicode):
            encoding = self._encoding
            if encoding is None:
                encoding = 'utf-8'
            json = json.decode(encoding)
        return (json
            .replace(u'\u2028', u'\\u2028')
            .replace(u'\u2029', u'\\u2029')
        )

    __unicode__ = as_json

    def __str__(self):
        """ JSON as ``str`` (UTF-8 encoded) """
        return self.as_json().encode('utf-8')


class SimpleJSON(object):
    """
    JSON generator for use with `replace` or `fill`

    This class uses simplejson for generating JSON output.

    The encoder looks for either the ``json`` module or, if that fails, for
    the ``simplejson`` module. If both fail, an ImportError is raised from the
    `as_json` method.

    :IVariables:
      `_content` : any
        Wrapped content

      `_inlined` : ``bool``
        Escape for inlining?

      `_str_encoding` : ``str``
        Str encoding
    """

    def __init__(self, content, inlined=False, str_encoding='latin-1'):
        """
        Initialization

        :Parameters:
          `content` : any
            Content to wrap for json conversion

          `inlined` : ``bool``
            Is it going to be inlined? Certain sequences are escaped then.

          `str_encoding` : ``str``
            Encoding to be applied on ``str`` content parts. Latin-1 is
            a failsafe default here, because it always translates. It may be
            wrong though.
        """
        self._content = content
        self._inlined = bool(inlined)
        self._str_encoding = str_encoding

    def __repr__(self):
        """ Debug representation """
        return "%s(%r, %r)" % (
            self.__class__.__name__, self._content, bool(self._inlined)
        )

    def as_json(self, inlined=None):
        """
        Content as JSON

        :Parameters:
          `inlined` : ``bool`` or ``None``
            escape for inlining? If omitted or ``None``, the default value
            from construction is used.

        :Return: The JSON encoded content
        :Rtype: ``unicode``
        """
        try:
            import json as _json # pylint: disable = F0401
        except ImportError:
            import simplejson as _json # pylint: disable = F0401
        json = _json.dumps(self._content,
            separators=(',', ':'),
            ensure_ascii=False,
            encoding=self._str_encoding,
        )
        if isinstance(json, str):
            json = json.decode(self._str_encoding)
        if inlined is None:
            inlined = self._inlined
        if inlined:
            json = escape_inlined(json)
        return (json
            .replace(u'\u2028', u'\\u2028')
            .replace(u'\u2029', u'\\u2029')
        )

    __unicode__ = as_json

    def __str__(self):
        """
        JSON as ``str`` (UTF-8 encoded)

        :Return: JSON string
        :Rtype: ``str``
        """
        return self.as_json().encode('utf-8')


def cleanup(script, encoding=None):
    """
    Cleanup single JS buffer

    This method attempts to remove CDATA and starting/finishing comment
    containers.

    :Parameters:
      `script` : ``basestring``
        Buffer to cleanup

      `encoding` : ``str``
        Encoding in case that toescape is a ``str``. If omitted or
        ``None``, no encoding is applied and `script` is expected to be
        ASCII compatible.

    :Return: The cleaned up buffer, typed as input
    :Rtype: ``basestring``
    """
    # pylint: disable = R0912

    isuni = isinstance(script, unicode)
    if not isuni:
        # don't decode ascii, but latin-1. just in case, if it's a
        # dumb default. Doesn't hurt here, but avoids failures.
        if encoding is None or _norm_enc(encoding) == 'ascii':
            encoding = 'latin-1'
        script = str(script).decode(encoding)
    script = script.strip()
    if script.startswith(u'<!--'):
        script = script[4:]
    if script.endswith(u'-->'):
        script = script[:-3]
    script = script.strip()
    if script.startswith(u'//'):
        pos = script.find(u'\n')
        if pos >= 0:
            script = script[pos + 1:]
    script = script[::-1]
    pos = script.find(u'\n')
    if pos >= 0:
        line = script[:pos].strip()
    else:
        line = script.strip()
        pos = len(line)
    if line.endswith(u'//'):
        script = script[pos + 1:]
    script = script[::-1].strip()
    if script.startswith(u'<![CDATA['):
        script = script[len(u'<![CDATA['):]
    if script.endswith(u']]>'):
        script = script[:-3]
    script = script.strip()
    if script.endswith(u'-->'):
        script = script[:-3]
    script = script.strip()
    if isuni:
        return script
    return script.encode(encoding)


def cdata(script, encoding=None):
    """
    Add a failsafe CDATA container around a script

    See <http://lists.w3.org/Archives/Public/www-html/2002Apr/0053.html>
    for details.

    :Parameters:
      `script` : ``basestring``
        JS to contain

      `encoding` : ``str``
        Encoding in case that toescape is a ``str``. If omitted or
        ``None``, no encoding is applied and `script` is expected to be
        ASCII compatible.

    :Return: The contained JS, typed as input
    :Rtype: ``basestring``
    """
    isuni = isinstance(script, unicode)
    if not isuni:
        # don't decode ascii, but latin-1. just in case, if it's a
        # dumb default. Doesn't hurt here, but avoids failures.
        if encoding is None or _norm_enc(encoding) == 'ascii':
            encoding = 'latin-1'
        script = str(script).decode(encoding)
    script = cleanup(script)
    if script:
        script = u'<!--//--><![CDATA[//><!--\n%s\n//--><!]]>' % script
    if isuni:
        return script
    return script.encode(encoding)


def minify(script, encoding=None):
    """
    Minify a script (using `rjsmin`_)

    .. _rjsmin: http://opensource.perlig.de/rjsmin/

    :Parameters:
      `script` : ``basestring``
        JS to minify

      `encoding` : ``str``
        Encoding in case that toescape is a ``str``. If omitted or
        ``None``, no encoding is applied and `script` is expected to be
        ASCII compatible.

    :Return: The minified JS, typed as input
    :Rtype: ``basestring``
    """
    from tdi.tools import rjsmin as _rjsmin

    isuni = isinstance(script, unicode)
    if not isuni and encoding is not None:
        # don't decode ascii, but latin-1. just in case, if it's a
        # dumb default. Doesn't hurt here, but avoids failures.
        if _norm_enc(encoding) == 'ascii':
            encoding = 'latin-1'
        return _rjsmin.jsmin(script.decode(encoding)).encode(encoding)
    return _rjsmin.jsmin(script)


class JSInlineFilter(_filters.BaseEventFilter):
    """
    TDI filter for modifying inline javascript

    :IVariables:
      `_collecting` : ``bool``
        Currently collecting javascript text?

      `_buffer` : ``list``
        Collection buffer

      `_starttag` : ``tuple`` or ``None``
        Original script starttag parameters

      `_modify` : callable
        Modifier function

      `_attribute` : ``str``
        ``tdi`` attribute name or ``None`` (if standalone)

      `_strip` : ``bool``
        Strip empty script elements?
    """

    def __init__(self, builder, modifier, strip_empty=True, standalone=False):
        """
        Initialization

        :Parameters:
          `builder` : `tdi.interfaces.BuildingListenerInterface`
            Builder

          `modifier` : callable
            Modifier function. Takes a script and returns the (possibly)
            modified result.

          `strip_empty` : ``bool``
            Strip empty script elements?

          `standalone` : ``bool``
            Standalone context? In this case, we won't watch out for TDI
            attributes.
        """
        super(JSInlineFilter, self).__init__(builder)
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

        Script starttags are delayed until the endtag is found. The whole
        element is then evaluated (and possibly thrown away).

        :See: `tdi.interfaces.ListenerInterface`
        """
        if not closed and self._normalize(name) == 'script':
            self._collecting = True
            self._buffer = []
            self._starttag = name, attr, closed, data
        else:
            self.builder.handle_starttag(name, attr, closed, data)

    def handle_endtag(self, name, data):
        """
        Handle endtag

        When currently collecting, it must be a script endtag. The script
        element content is then modified (using the modifiy function passed
        during initialization).  The result replaces the original. If it's
        empty and the starttag neither provides ``src`` nor ``tdi`` attributes
        and the filter was configured to do so: the whole element is thrown
        away.

        :See: `tdi.interfaces.ListenerInterface`
        """
        normalize = self._normalize
        if self._collecting:
            if normalize(name) != 'script':
                raise AssertionError("Invalid event stream")

            self._collecting = False
            script, self._buffer = ''.join(self._buffer), []
            script = self._modify(script)

            if not script and self._strip:
                attrdict = dict((normalize(name), val)
                    for name, val in self._starttag[1]
                )
                if normalize('src') not in attrdict:
                    if self._attribute is None or \
                            self._attribute not in attrdict:
                        return

            self.builder.handle_starttag(*self._starttag)
            self._starttag = None
            self.builder.handle_text(script)

        self.builder.handle_endtag(name, data)

    def handle_text(self, data):
        """
        Handle text

        While collecting javascript text, the received data is buffered.
        Otherwise the event is just passed through.

        :See: `tdi.interfaces.ListenerInterface`
        """
        if not self._collecting:
            return self.builder.handle_text(data)
        self._buffer.append(data)


def MinifyFilter(builder, minifier=None, standalone=False):
    """
    TDI Filter for minifying inline javascript

    :Parameters:
      `minifier` : callable
        Minifier function. If omitted or ``None``, the builtin minifier (see
        `minify`) is applied.

      `standalone` : ``bool``
        Standalone context? In this case, we won't watch out for TDI
        attributes.
    """
    # pylint: disable = C0103, C0322
    if minifier is None:
        minifier = minify
    work = lambda x, m=minifier, c=cleanup: m(c(x))
    return JSInlineFilter(builder, work, standalone=standalone)


def CDATAFilter(builder, standalone=False): # pylint: disable = C0103
    """
    TDI filter for adding failsafe CDATA containers around scripts

    :Parameters:
      `standalone` : ``bool``
        Standalone context? In this case, we won't watch out for TDI
        attributes.

    See <http://lists.w3.org/Archives/Public/www-html/2002Apr/0053.html>
    for details.
    """
    return JSInlineFilter(builder, cdata, standalone=standalone)
