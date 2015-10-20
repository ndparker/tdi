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

=====================
 Markup Parser Logic
=====================

Soup Parser
~~~~~~~~~~~

This module provides a very lenient HTML/XML lexer. The `SoupLexer` class is
initialized with a listener object, which receives all low level events
(like starttag, endtag, text etc). Listeners must implement the
`ListenerInterface`.

On top of the lexer there's `SoupParser` class, which actually implements the
`ListenerInterface` itself (the parser listens to the lexer). The parser adds
HTML semantics to the lexed data and passes the events to a building listener
(`BuildingListenerInterface`). In addition to the events sent by the lexer the
`SoupParser` class generates endtag events (with empty data arguments) for
implicitly closed elements. Furthermore it knows about CDATA elements like
``<script>`` or ``<style>`` and modifies the lexer state accordingly.

The actual semantics are provided by a DTD query class (implementing
`DTDInterface`.)
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

import re as _re

from ..._exceptions import LexerEOFError, LexerFinalizedError
from ... import interfaces as _interfaces
from . import dtd as _dtd


class SoupLexer(object):
    """
    (X)HTML Tagsoup Lexer

    The lexer works hard to preserve the original data. In order to achieve
    this goal, it does not validate the input and recognizes its input in a
    quite lenient way.

    :Groups:
      - `Lexer states` :
        `TEXT`,
        `CDATA`,
        `MARKUP`,
        `STARTTAG`,
        `ENDTAG`,
        `COMMENT`,
        `MSECTION`,
        `DECL`,
        `PI`,
        `EMPTY`,
        `FINAL`
      - `Regex Matchers` :
        `_START_MATCH`,
        `_ATT_ITER`,
        `_COMMENT_SEARCH`,
        `_MSECTION_MATCH`,
        `_MSECTIONINVALID_MATCH`,
        `_MEND_SEARCH`,
        `_MSEND_SEARCH`,
        `_DECL_MATCH`

    :CVariables:
      `TEXT` : ``int``
        Lexer state ``TEXT`` (between tags)

      `CDATA` : ``int``
        Lexer state ``CDATA`` (between (P)CDATA tags)

      `MARKUP` : ``int``
        Lexer state ``MARKUP`` (``<``)

      `STARTTAG` : ``int``
        Lexer state ``STARTTAG`` (``<[letter]``)

      `ENDTAG` : ``int``
        Lexer state ``ENDTAG`` (``</``)

      `COMMENT` : ``int``
        Lexer state ``COMMENT`` (``<!--``)

      `MSECTION` : ``int``
        Lexer state ``MSECTION`` (``<![``)

      `DECL` : ``int``
        Lexer state ``DECL`` (``<!``)

      `PI` : ``int``
        Lexer state ``PI`` (``<?``)

      `EMPTY` : ``int``
        Lexer state ``EMPTY`` (``<>``)

      `FINAL` : ``int``
        Lexer state ``FINAL``

      `_LEXERS` : ``tuple``
        The state lexer method names (``('method', ...)``)

      `_STATES` : ``tuple``
        The state names (``('name', ...)``)

    :IVariables:
      `_state` : ``int``
        The current lexer state

      `_lexers` : ``list``
        The state lexer methods (``[method, ...]``)

      `_listener` : `ListenerInterface`
        The listener the events shall be sent to

      `_buffer` : ``str``
        Current unprocessed buffer

      `_conditional_ie_comments` : ``bool``
        Handle conditional IE comments as text?
    """
    # pylint: disable = no-member

    def __init__(self, listener, conditional_ie_comments=True):
        r"""
        Initialization

        :Parameters:
          `listener` : `ListenerInterface`
            The event listener

          `conditional_ie_comments` : ``bool``
            Handle conditional IE comments as text?

            Conditional comments are described in full detail
            at `MSDN`_\.

        .. _MSDN: http://msdn.microsoft.com/en-us/library/
                  ms537512%28v=vs.85%29.aspx
        """
        self._listener = listener
        self._normalize = None
        self._cdata_name = None

        self._state = self.TEXT
        self._lexers = [getattr(self, name) for name in self._LEXERS]
        self._buffer = ''
        self._conditional_ie_comments = bool(conditional_ie_comments)

    def feed(self, food):
        """
        Feed the lexer with new data

        :Parameters:
          `food` : ``str``
            The data to process
        """
        self._buffer += food
        self._lex()

    def finalize(self):
        """
        Finalize the lexer

        This processes the rest buffer (if any)

        :Exceptions:
          - `LexerEOFError` : The rest buffer could not be consumed
        """
        self._lex()
        if self._buffer:
            raise LexerEOFError(
                "Unfinished parser state %s" % self._STATES[self._state]
            )

        self._state = self.FINAL

    def cdata(self, normalize, name):
        """ Set CDATA state """
        if self._state != self.FINAL:
            self._state = self.CDATA
            self._normalize = normalize
            self._cdata_name = normalize(name)

    def _lex(self):
        """ Parse the current buffer """
        while self._buffer:
            if self._lexers[self._state]():
                break

    def _lex_text(self):
        """
        Text lexer

        State: We are between tags or at the very beginning of the document
        and look for a ``<``.

        :Return: Unfinished state?
        :Rtype: ``bool``
        """
        data = self._buffer
        pos = data.find('<')
        if pos == 0:
            self._state = self.MARKUP
            return False
        elif pos == -1:
            self._buffer = ''
        else:
            self._buffer, data = data[pos:], data[:pos]
            self._state = self.MARKUP

        self._listener.handle_text(data)
        return False

    def _lex_cdata(self):
        """
        (PR)CDATA lexer

        State: We are inside a text element and looking for the end tag only

        :Return: Unfinished state?
        :Rtype: ``bool``
        """
        incomplete = False
        data, pos = self._buffer, 0
        while True:
            pos = data.find('<', pos)
            if pos == -1:
                pos = len(data)
                self._buffer = ''
                break
            else:
                char = data[pos + 1:pos + 2]
                if char == '/':
                    self._state = self.ENDTAG
                    break
                elif char == '':
                    incomplete = True
                    break
                else:
                    pos += 1

        if pos > 0:
            self._buffer, data = data[pos:], data[:pos]
            self._listener.handle_text(data)

        return incomplete

    #: Regex matcher for a tagname character
    #:
    #: :Type: ``callable``
    _TAGNAME_MATCH = _re.compile(r'[a-zA-Z0-9]').match

    def _lex_markup(self):
        """
        Markup lexer

        State: We've hit a ``<`` character and now find out, what it's
        becoming

        :Return: Unfinished state?
        :Rtype: ``bool``
        """
        data = self._buffer
        if len(data) < 2:
            return True

        char = data[1]
        state = (self.ENDTAG, self.DECL, self.PI, self.EMPTY, -1)[
            "/!?>".find(char)
        ]
        if state == -1:
            if self._TAGNAME_MATCH(char):
                state = self.STARTTAG
            else:
                state = self.TEXT
                self._buffer = data[1:]
                self._listener.handle_text(data[0])

        self._state = state
        return False

    #: Regex matcher for a start tag
    #:
    #: :Type: ``callable``
    _START_MATCH = _re.compile(r'''
        <
            (?P<name>[^ \t\r\n\f/>]+)
            (?P<attr>
                [^"'>]*
                (?:
                    (?:
                        "[^"]*"
                      | '[^']*'
                    )
                    [^"'>]*
                )*
            )
            [ \t\r\n\f]*
        >
    ''', _re.X).match

    #: Regex iterator for extracting start tag attributes
    #:
    #: :Type: ``callable``
    _ATT_ITER = _re.compile(r'''
        [ \t\r\n\f]*
        (?P<name>(?:/|[^ \t\r\n\f/=>]*))   # attribute name
        [ \t\r\n\f]*
        (?:
            =
            (?P<value>                     # optional value
                [ \t\r\n\f]*"[^"]*"
              | [ \t\r\n\f]*'[^']*'
              | [^ \t\r\n\f/>]*
            )
        )?
    ''', _re.X).finditer

    def _lex_start(self):
        """
        Starttag lexer

        State: We've hit a ``<x`` and now look for the ``>``.

        :Return: Unfinished State?
        :Rtype: ``bool``
        """
        data = self._buffer
        match = self._START_MATCH(data)
        if match is None:
            return True

        pos = match.end()
        self._buffer, data = data[pos:], data[:pos]

        name, attrstring = match.group('name', 'attr')
        attr, closed = [], False
        if attrstring:
            for match in self._ATT_ITER(attrstring):
                key, value = match.group('name', 'value')
                if key == '/' and value is None:
                    closed = True
                    continue
                if key or value is not None:
                    if value:
                        value = value.strip()
                    attr.append((key.strip(), value))
                else:  # bug in Python < 2.3.5 (fixed in rev 37262)
                    break

        self._state = self.TEXT
        self._listener.handle_starttag(name, attr, closed, data)
        return False

    def _lex_end(self):
        """
        Endtag lexer

        State: We've hit ``</``.

        :Return: Unfinished state?
        :Rtype: ``bool``
        """
        data = self._buffer
        pos = data.find('>') + 1
        if pos == 0:
            return True

        self._buffer, data = data[pos:], data[:pos]
        name = data[2:-1].strip()

        if self._cdata_name is not None and \
                self._normalize(name) != self._cdata_name:
            self._state = self.CDATA
            self._listener.handle_text(data)
        else:
            self._cdata_name = self._normalize = None
            self._state = self.TEXT
            self._listener.handle_endtag(name, data)
        return False

    #: Regex searcher for finding the end of a comment
    #:
    #: :Type: ``callable``
    _COMMENT_SEARCH = _re.compile(r'--[ \t\r\n\f]*>').search

    #: Regex searcher for matching IE conditional comment
    #:
    #: :Type: ``callable``
    _IE_COMMENT_MATCH = _re.compile(r'''
        \[[ \t\r\n\f]* (?:
            [iI][fF] | [eE][lL][sS][eE] | [eE][nN][dD][iI][fF]
        ) [^\]]+]>
    ''', _re.X).match

    def _lex_comment(self):
        """
        Comment lexer

        State: We've hit ``<!--``.

        :Return: Unfinished state?
        :Rtype: ``bool``
        """
        data = self._buffer
        if len(data) < 7:
            return True

        if self._conditional_ie_comments:
            match = iec = self._IE_COMMENT_MATCH(data, 4)
        else:
            match = iec = None
        if match is None:
            match = self._COMMENT_SEARCH(data, 4)
            if match is None:
                return True

        pos = match.end()
        self._buffer, data = data[pos:], data[:pos]

        self._state = self.TEXT
        if iec:
            self._listener.handle_text(data)
        else:
            self._listener.handle_comment(data)

        return False

    #: List of MS-specific marked section names (lowercased)
    #:
    #: :Type: ``tuple``
    _MSSECTIONS = ('if', 'else', 'endif')

    #: Regex matcher for the start of a marked section
    #:
    #: :Type: ``callable``
    _MSECTION_MATCH = _re.compile(r'''
        <!\[[ \t\r\n\f]*(?P<name>[^\][ \t\r\n\f>]+)(?=[\][ \t\r\n\f>])
    ''', _re.X).match

    #: Regex matcher for the start of an invalid marked section
    #:
    #: :Type: ``callable``
    _MSECTIONINVALID_MATCH = _re.compile(r'<!\[[ \t\r\n\f]*[\][>]').match

    #: Regex searcher for the end of a marked section
    #:
    #: :Type: ``callable``
    _MEND_SEARCH = _re.compile(r'][ \t\r\n\f]*][ \t\r\n\f]*>').search

    #: Regex searcher for the end of a MS specific marked section
    #:
    #: :Type: ``callable``
    _MSEND_SEARCH = _re.compile(r'][ \t\r\n\f]*(?:--)?[ \t\r\n\f]*>').search

    def _lex_msection(self):
        """
        Marked section lexer

        State: We've hit a ``<![`` and now seek the end

        :Return: Unfinished state?
        :Rtype: ``bool``
        """
        data = self._buffer
        match = self._MSECTION_MATCH(data)
        if match is None:
            match = self._MSECTIONINVALID_MATCH(data)
            if match is not None:  # pass invalid msection as text
                pos = match.end()
                self._buffer = data[pos:]
                data = data[:pos]
                self._state = self.TEXT
                self._listener.handle_text(data)
                return False
            return True

        name = match.group('name')
        start = match.end()
        if self._conditional_ie_comments and name.lower() in self._MSSECTIONS:
            match = iec = self._MSEND_SEARCH(data, start)
        else:
            pos = data.find('[', start)
            if pos >= 0:
                start = pos + 1
            match = self._MEND_SEARCH(data, start)
            iec = None
        if match is None:
            return True
        pos, end = match.end(), match.start()
        value = data[start:end]
        self._buffer, data = data[pos:], data[:pos]

        self._state = self.TEXT
        if iec:
            self._listener.handle_text(data)
        else:
            self._listener.handle_msection(name, value, data)
        return False

    #: Regex matcher for a complete declaration
    #:
    #: This regex seems a bit nasty, but it should catch all stuff allowed
    #: in declarations (including doctype). Some day, it probably needs to
    #: be replaced it by real lexer states...
    #:
    #: :Type: ``callable``
    _DECL_MATCH = _re.compile(r'''
        <!
        (?P<name>[^\][ \t\r\n\f>]*)
        (?P<value>
            [^"'<>-]*                    # any nonspecial
            (?:
                (?:
                    "[^"]*"              # double quoted string
                  | '[^']*'              # single quoted string (valid?)
                  | <!\[                 # marked section
                    [^\]]*
                    (?:
                        ](?![ \t\r\n\f]*][ \t\r\n\f]*>)
                        [^\]]*
                    )*
                    ][ \t\r\n\f]*][ \t\r\n\f]*>
                  | <(?!!\[)             # declaration
                                         # hopefully not a doctype
                                         # (but unlikely, because we are
                                         # probably already in a DT subset)
                    [^"'>-]*
                    (?:
                        (?:
                            "[^"]*"
                          | '[^']*'
                          | --           # comment
                                [^-]*
                                (?:-[^-]+)*
                            --
                          | -(?!-)       # just a hyphen
                        )
                        [^"'>-]*
                    )*
                    >
                  | --                   # comment
                    [^-]*
                    (?:-[^-]+)*
                    --
                  | -(?!-)               # just a hyphen
                )
                [^"'<>-]*                # more non-specials
            )*
        )
        >
    ''', _re.X).match

    def _lex_decl(self):
        """
        Declaration lexer

        State: We've hit a ``<!`` and now peek inside

        :Return: Unfinished state?
        :Rtype: ``bool``
        """
        data = self._buffer
        if len(data) < 3:
            return True

        if data.startswith('<!--'):
            self._state = self.COMMENT
            return False
        elif data.startswith('<!['):
            self._state = self.MSECTION
            return False
        elif data == '<!-':
            return True

        match = self._DECL_MATCH(data)
        if match is None:
            return True

        name, value = match.group('name', 'value')
        pos = match.end()
        self._buffer, data = data[pos:], data[:pos]

        self._state = self.TEXT
        self._listener.handle_decl(name, value.strip(), data)
        return False

    def _lex_pi(self):
        """
        Processing instruction lexer

        State: We've hit a ``<?`` and now peek inside

        :Return: Unfinished state?
        :Rtype: ``bool``
        """
        data = self._buffer
        pos = data.find('?>', 2)
        if pos == -1:
            return True
        pos += 2

        self._buffer, data = data[pos:], data[:pos]

        self._state = self.TEXT
        self._listener.handle_pi(data)
        return False

    def _lex_empty(self):
        """
        Empty tag lexer

        State: We've hit a ``<>``

        :Return: Unfinished state?
        :Rtype: ``bool``
        """
        self._buffer, data = self._buffer[2:], self._buffer[:2]

        self._state = self.TEXT
        self._listener.handle_starttag('', [], False, data)
        return False

    def _lex_final(self):
        """
        Called after the lexer was finalized

        State: after all

        :Exceptions:
          - `LexerFinalizedError` : The lexer was already finalized
            (raised always)
        """
        raise LexerFinalizedError("The lexer was already finalized")

_LEXERS = []
_STATES = []
for _idx, (_statename, _funcname) in enumerate([
        # pylint: disable = bad-whitespace

        ('FINAL',    '_lex_final'),
        ('TEXT',     '_lex_text'),
        ('CDATA',    '_lex_cdata'),
        ('MARKUP',   '_lex_markup'),
        ('STARTTAG', '_lex_start'),
        ('ENDTAG',   '_lex_end'),
        ('COMMENT',  '_lex_comment'),
        ('MSECTION', '_lex_msection'),
        ('DECL',     '_lex_decl'),
        ('PI',       '_lex_pi'),
        ('EMPTY',    '_lex_empty'),
    ]):  # noqa
    setattr(SoupLexer, _statename, _idx)
    _LEXERS.append(_funcname)
    _STATES.append(_statename)

SoupLexer._LEXERS = tuple(_LEXERS)  # pylint: disable = protected-access
SoupLexer._STATES = tuple(_STATES)  # pylint: disable = protected-access
del _idx, _statename, _funcname  # pylint: disable = undefined-loop-variable
del _LEXERS, _STATES


from ... import c
c = c.load('impl')
if c is not None:
    DEFAULT_LEXER = c.SoupLexer
else:
    DEFAULT_LEXER = SoupLexer  # pylint: disable = invalid-name
del c


class SoupParser(object):
    """
    =========================
     (X)HTML Tag Soup Parser
    =========================

    Overview
    ~~~~~~~~

    The parser is actually a tagsoup parser by design in order to process
    most of the "HTML" that can be found out there. Of course, if the HTML
    is well-formed and valid, this would be the best. There is only as
    much HTML syntax applied as necessary to parse it. You can influence
    these syntax definitions by picking another lexer. You can change
    the semantics by picking another dtd query class.

    This parser guarantees, that for each not-self-closing starttag event also
    an endtag event is generated (if the endtag is not actually there, the
    data parameter is an empty string). This also happens for empty tags (like
    ``br``). On the other hand, there may be more endtag events than starttag
    events, because of unbalanced or wrongly nested tags.

    Special constructs, which are comments, PIs, marked sections and
    declarations may occur anywhere, i.e. they are not closing elements
    implicitly.

    The default lexer does not deal with NET tags (<h1/Heading/). Neither
    does it handle unfinished starttags by SGML rules like ``<map<area>``.
    It *does* know about empty tags (``<>`` and ``</>``).

    CDATA elements and comments are handled in a simplified way. Once
    the particular state is entered, it's only left, when the accompanying
    end marker was found (``<script>...</script>``, ``<!-- ... -->``).
    Anything in between is text.

    How is it used?
    ~~~~~~~~~~~~~~~

    The parser API is "streamy" on the input side and event based on the
    output side. So, what you need first is a building listener, which will
    receive all generated parser events and process them. Such is listener
    object is expected to implement the `BuildingListenerInterface`.

    Now you create a `SoupParser` instance and pass the listener object to
    the contructor and the parser is ready to be fed. You can feed as many
    chunks of input data you like into the parser by using the `feed`
    method. Every feed call may generate mutiple events on the output side.
    When you're done feeding, call the parser's `finalize` method in order
    to clean up. This also flushes pending events to the listener.

    :IVariables:
      `listener` : `BuildingListenerInterface`
        The building listener to send the events to

      `lexer` : `SoupLexer`
        The lexer instance

      `_tagstack` : ``list``
        The current tag stack

      `_inempty` : ``bool``
        indicates if the last tag on the stack is an empty one

      `_lastopen` : ``str``
        Stores the last seen open tag name
    """
    __implements__ = [
        _interfaces.ListenerInterface, _interfaces.ParserInterface
    ]

    def __init__(self, listener, dtd, lexer=None):
        """
        Initialization

        :Parameters:
          `listener` : `ListenerInterface`
            The building listener

          `dtd` : `DTDInterface`
            DTD query object

          `lexer` : ``callable``
            Lexer class/factory. This mus be a callable taking an
            event listener and returning a lexer instance. If omitted or
            ``None``, the default lexer will be used (`DEFAULT_LEXER`).
        """
        self._tagstack, self._inempty, self._lastopen = [], False, ''
        self.listener = listener
        self._is_nestable = dtd.nestable
        self._is_cdata = dtd.cdata
        self._is_empty = dtd.empty
        if lexer is None:
            lexer = DEFAULT_LEXER
        self._lexer = lexer(self)
        self._normalize = listener.decoder.normalize

    @classmethod
    def html(cls, listener):
        """
        Construct a parser using the `HTMLDTD`

        :Parameters:
          `listener` : `BuildingListenerInterface`
            The building listener

        :Return: The new parser instance
        :Rtype: `SoupParser`
        """
        return cls(listener, _dtd.HTMLDTD())

    @classmethod
    def xml(cls, listener):
        """
        Construct a parser using the `XMLDTD`

        :Parameters:
          `listener` : `ListenerInterface`
            The building listener

        :Return: The new parser instance
        :Rtype: `SoupParser`
        """
        return cls(listener, _dtd.XMLDTD())

    def _close_empty(self):
        """ Ensure we close last empty tag """
        if self._inempty:
            self._inempty = False
            self.listener.handle_endtag(self._tagstack.pop()[1], '')

    #########################################################################
    # ListenerInterface #####################################################
    #########################################################################

    def handle_text(self, data):
        """ :See: `ListenerInterface` """
        self._close_empty()
        self.listener.handle_text(data)

    def handle_starttag(self, name, attrs, closed, data):
        """ :See: `ListenerInterface` """
        self._close_empty()

        if name == '' and not attrs:
            name = self._lastopen
        else:
            self._lastopen = name

        tagstack = self._tagstack
        nestable = self._is_nestable
        starttag = self._normalize(name)
        while tagstack and not nestable(tagstack[-1][0], starttag):
            self.listener.handle_endtag(tagstack.pop()[1], '')

        if closed:
            self.listener.handle_starttag(name, attrs, closed, data)
        else:
            if self._is_cdata(starttag):
                self._lexer.cdata(self._normalize, starttag)
            self.listener.handle_starttag(name, attrs, closed, data)
            tagstack.append((starttag, name))
            if self._is_empty(starttag):
                self._inempty = True

    def handle_endtag(self, name, data):
        """ :See: `ListenerInterface` """
        tagstack = self._tagstack
        if tagstack:
            if name == '':
                name = tagstack[-1][1]
            endtag = self._normalize(name)
            if endtag in dict(tagstack):
                toclose, original = tagstack.pop()
                self._inempty = False
                while toclose != endtag:
                    self.listener.handle_endtag(original, '')
                    toclose, original = tagstack.pop()

        self._close_empty()
        self.listener.handle_endtag(name, data)

    def handle_comment(self, data):
        """ :See: `ListenerInterface` """
        self._close_empty()
        self.listener.handle_comment(data)

    def handle_msection(self, name, value, data):
        """ :See: `ListenerInterface` """
        self._close_empty()
        self.listener.handle_msection(name, value, data)

    def handle_decl(self, name, value, data):
        """ :See: `ListenerInterface` """
        self._close_empty()
        self.listener.handle_decl(name, value, data)

    def handle_pi(self, data):
        """ :See: `ListenerInterface` """
        self._close_empty()
        self.listener.handle_pi(data)

    def handle_escape(self, escaped, data):
        """ :See: `ListenerInterface` """
        # pylint: disable = unused-argument

        raise AssertionError()

    #########################################################################
    # ParserInterface #######################################################
    #########################################################################

    def feed(self, food):
        """ :See: `ParserInterface` """
        self._lexer.feed(food)

    def finalize(self):
        """
        :See: `ParserInterface`

        :Exceptions:
          - `LexerEOFError` : EOF in the middle of a state
        """
        if self._lexer is not None:
            self._lexer, _ = None, self._lexer.finalize()  # noqa

        tagstack = self._tagstack
        while tagstack:
            self.listener.handle_endtag(tagstack.pop()[1], '')


from ... import c
c = c.load('impl')
if c is not None:
    DEFAULT_PARSER = c.SoupParser
else:
    DEFAULT_PARSER = SoupParser  # pylint: disable = invalid-name
del c
