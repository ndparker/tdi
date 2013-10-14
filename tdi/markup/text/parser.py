# -*- coding: ascii -*-
#
# Copyright 2012 - 2013
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
===================
 Text Parser Logic
===================

Text Parser.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import re as _re

from tdi._exceptions import LexerEOFError, LexerFinalizedError
from tdi import interfaces as _interfaces


class TextLexer(object):
    """ Text Lexer """
    # pylint: disable = E1101

    def __init__(self, listener):
        """
        Initialization

        :Parameters:
          `listener` : `ListenerInterface`
            The event listener
        """
        self._listener = listener

        self.state = self.TEXT
        self._lexers = [getattr(self, name) for name in self._LEXERS]
        self._buffer = ''

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
                "Unfinished parser state %s" % self._STATES[self.state]
            )

        self.state = self.FINAL

    def _lex(self):
        """ Parse the current buffer """
        while self._buffer:
            if self._lexers[self.state]():
                break

    def _lex_text(self):
        """
        Text lexer

        State: We are between tags or at the very beginning of the document
        and look for a ``[``.

        :Return: Unfinished state?
        :Rtype: ``bool``
        """
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

    def _lex_markup(self):
        """
        Markup lexer

        State: We've hit a ``[`` character and now find out, what it's
        becoming

        :Return: Unfinished state?
        :Rtype: ``bool``
        """
        data = self._buffer
        if len(data) < 2:
            return True

        char = data[1]
        if char == '/':
            state = self.ENDTAG
        elif char == '#':
            state = self.COMMENT
        elif char == '?':
            state = self.PI
        elif char == ']':
            state = self.TEXT
            self._listener.handle_escape(data[0], data[:2])
            self._buffer = data[2:]
        else:
            state = self.STARTTAG

        self.state = state
        return False


    #: Regex matcher for a start tag
    #:
    #: :Type: ``callable``
    _START_MATCH = _re.compile(r'''
        \[
            (
                [^\\"'\[\]]*
                (?:
                    (?:
                        "[^\\"]*(?:\\.[^\\"]*)*"
                      | '[^\\']*(?:\\.[^\\']*)*'
                    )
                    [^\\"'\[\]]*
                )*
            )
        \]
    ''', _re.X | _re.S).match

    #: Regex matcher for an empty start tag
    #:
    #: :Type: ``callable``
    _EMPTY_START_MATCH = _re.compile(r'''
        \[
            (
                \[
                [^\\"'\[\]]*
                (?:
                    (?:
                        "[^\\"]*(?:\\.[^\\"]*)*"
                      | '[^\\']*(?:\\.[^\\']*)*'
                    )
                    [^\\"'\[\]]*
                )*
                \]
            )
        \]
    ''', _re.X | _re.S).match


    #: Regex iterator for extracting start tag attributes
    #:
    #: :Type: ``callable``
    _ATT_ITER = _re.compile(r'''
        \s*
        (?P<name>[^\s=\]]*)           # attribute name
        \s*
        (?:
            =
            (?P<value>                # optional value
                \s* "[^\\"]*(?:\\.[^\\"]*)*"
              | \s* '[^\\']*(?:\\.[^\\']*)*'
              | [^\\\s\]]*
            )
        )?
    ''', _re.X | _re.S).finditer

    def _lex_start(self):
        """
        Starttag lexer

        State: We've hit a ``[tag`` and now look for the ``]``

        :Return: Unfinished State?
        :Rtype: ``bool``
        """
        data = self._buffer
        match = self._EMPTY_START_MATCH(data) or self._START_MATCH(data)
        if match is None:
            return True

        pos = match.end()
        self._buffer, data = data[pos:], data[:pos]

        attrstring = match.group(1)
        quoted = attrstring.startswith('[')
        if quoted:
            attrstring = attrstring[1:-1]

        splitted = attrstring.split(None, 1)
        if not splitted:
            self._listener.handle_text(data)
            self.state = self.TEXT
            return False
        name = splitted[0]
        if '=' in name:
            name = ''
        elif len(splitted) == 1:
            attrstring = None
        else:
            attrstring = splitted[1]

        attr = []
        if attrstring:
            for match in self._ATT_ITER(attrstring):
                key, value = match.group('name', 'value')
                if key or value is not None:
                    if value:
                        value = value.strip()
                    attr.append((key.strip(), value))
                else: # bug protection for Python < 2.3.5 (fixed in rev 37262)
                    break

        self.state = self.TEXT
        self._listener.handle_starttag(name, attr, quoted, data)
        return False

    def _lex_end(self):
        """
        Endtag lexer

        State: We've hit ``[/``.

        :Return: Unfinished state?
        :Rtype: ``bool``
        """
        data = self._buffer
        pos = data.find(']') + 1
        if pos == 0:
            return True

        self._buffer, data = data[pos:], data[:pos]
        name = data[2:-1].strip()

        self.state = self.TEXT
        self._listener.handle_endtag(name, data)
        return False


    #: Regex searcher for finding the end of a comment
    #:
    #: :Type: ``callable``
    _COMMENT_SEARCH = _re.compile(r'#\]').search

    def _lex_comment(self):
        """
        Comment lexer

        State: We've hit ``[#``.

        :Return: Unfinished state?
        :Rtype: ``bool``
        """
        data = self._buffer
        if len(data) < 4:
            return True

        match = self._COMMENT_SEARCH(data, 2)
        if match is None:
            return True

        pos = match.end()
        self._buffer, data = data[pos:], data[:pos]

        self.state = self.TEXT
        self._listener.handle_comment(data)
        return False

    def _lex_pi(self):
        """
        Processing instruction lexer

        State: We've hit a ``[?`` and now peek inside

        :Return: Unfinished state?
        :Rtype: ``bool``
        """
        data = self._buffer
        pos = data.find('?]', 2)
        if pos == -1:
            return True
        pos += 2

        self._buffer, data = data[pos:], data[:pos]

        self.state = self.TEXT
        self._listener.handle_pi(data)
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
    ('FINAL',    '_lex_final'),
    ('TEXT',     '_lex_text'),
    ('MARKUP',   '_lex_markup'),
    ('STARTTAG', '_lex_start'),
    ('ENDTAG',   '_lex_end'),
    ('PI',       '_lex_pi'),
    ('COMMENT',  '_lex_comment'),
]):
    setattr(TextLexer, _statename, _idx)
    _LEXERS.append(_funcname)
    _STATES.append(_statename)

TextLexer._LEXERS = tuple(_LEXERS)
TextLexer._STATES = tuple(_STATES)
del _idx, _statename, _funcname, _LEXERS, _STATES # pylint: disable = W0631


class TextParser(object):
    """ Text Parser """
    __implements__ = [
        _interfaces.ListenerInterface, _interfaces.ParserInterface
    ]

    def __init__(self, listener, lexer=TextLexer):
        """
        Initialization

        :Parameters:
          `listener` : `BuildingListenerInterface`
            The building listener

          `lexer` : ``callable``
            Lexer class/factory. This must be a callable taking an
            event listener and returning a lexer instance
        """
        self._tagstack = []
        self.listener = listener
        self._lexer = lexer(self)
        self._normalize = self.listener.decoder.normalize

    #########################################################################
    ### ListenerInterface ###################################################
    #########################################################################

    def handle_text(self, data):
        """ :See: `ListenerInterface` """
        self.listener.handle_text(data)

    def handle_escape(self, escaped, data):
        """ :See: `ListenerInterface` """
        self.listener.handle_escape(escaped, data)

    def handle_starttag(self, name, attrs, closed, data):
        """ :See: `ListenerInterface` """
        self.listener.handle_starttag(name, attrs, closed, data)
        if not closed:
            self._tagstack.append((self._normalize(name), name))

    def handle_endtag(self, name, data):
        """ :See: `ListenerInterface` """
        tagstack = self._tagstack
        if tagstack:
            if name == '':
                name = tagstack[-1][1]
            endtag = self._normalize(name)
            if endtag in dict(tagstack):
                toclose, original = tagstack.pop()
                while toclose != name:
                    self.listener.handle_endtag(original, '')
                    toclose, original = tagstack.pop()
        self.listener.handle_endtag(name, data)

    def handle_comment(self, data):
        """ :See: `ListenerInterface` """
        self.listener.handle_comment(data)

    def handle_pi(self, data):
        """ :See: `ListenerInterface` """
        self.listener.handle_pi(data)

    def handle_msection(self, name, value, data):
        """ :See: `ListenerInterface` """
        # pylint: disable = W0613
        raise AssertionError()

    def handle_decl(self, name, value, data):
        """ :See: `ListenerInterface` """
        # pylint: disable = W0613
        raise AssertionError()

    #########################################################################
    ### ParserInterface #####################################################
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
            self._lexer, _ = None, self._lexer.finalize()

        tagstack = self._tagstack
        while tagstack:
            self.listener.handle_endtag(tagstack.pop()[1], '')
