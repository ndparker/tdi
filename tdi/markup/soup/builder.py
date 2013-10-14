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
========================
 Template Builder Logic
========================

This module provides the logic to build a nodetree out of parser
events.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import codecs as _codecs

from tdi._exceptions import TemplateEncodingError
from tdi import interfaces as _interfaces
from tdi import nodetree as _nodetree
from tdi.markup import _analyzer


class SoupBuilder(object):
    """
    HTML Template tree builder

    :IVariables:
      `_tree` : `nodetree.Root`
        The built subtree

      `_text` : ``list``
        The current text buffer

      `_tagstack` : ``list``
        The stack of currently nested tag names with associated nodes

      `_nodestack` : ``list``
        The stack of currently nested snippet parameters

      `_devnull` : ``bool``
        Are we inside a removed element?

      `encoding` : ``str``
        Template encoding

      `encoder` : `EncoderInterface`
        Encoder

      `decoder` : `DecoderInterface`
        Decoder

      `analyze` : `AttributeAnalyzerInterface`
        Attribute analyzer
    """
    __implements__ = [_interfaces.BuilderInterface,
                      _interfaces.BuildingListenerInterface]

    encoding = 'ascii'

    def __init__(self, encoder, decoder, analyzer=None):
        """
        Initialization

        :Parameters:
          `encoder` : ``callable``
            Encoder factory

          `decoder` : ``callable``
            Decoder factory

          `analyzer` : `AttributeAnalyzerInterface`
            Attribute analyzer
        """
        root = _nodetree.Root()
        self._tree = root
        self._text = []
        self._tagstack = []
        self._nodestack = [root]
        self._devnull = False
        self.encoder = encoder(self.encoding)
        self.decoder = decoder(self.encoding)
        if analyzer is None:
            analyzer = _analyzer.DEFAULT_ANALYZER(self.decoder, hidden=False)
        self.analyze = analyzer

    def _flush_text(self):
        """ Flush current text buffer """
        if self._text:
            if not self._devnull:
                self._nodestack[-1].append_text(''.join(self._text))
            self._text = []

    #########################################################################
    ### ListenerInterface ###################################################
    #########################################################################

    def handle_text(self, data):
        """ :see: `ListenerInterface` """
        if not self._devnull:
            self._text.append(data)

    def handle_escape(self, escaped, data):
        """ :see: `ListenerInterface` """
        if not self._devnull:
            self._flush_text()
            self._nodestack[-1].append_escape(escaped, data)

    def handle_starttag(self, name, attr, closed, data):
        """ :see: `ListenerInterface` """
        starttag = self.decoder.normalize(name)

        if not self._devnull:
            attr, special = self.analyze(attr)
            if special:
                self._flush_text()
                flags, tdi = special.get('attribute', ('', None))
                if not closed and tdi is None and flags == '-':
                    self._devnull = True
                    self._tagstack.append((starttag, '-'))
                    self._nodestack.append('-')
                    return

                node = self._nodestack[-1].append_node(
                    name, attr, special, closed
                )
                if not closed:
                    self._tagstack.append((starttag, node))
                    self._nodestack.append(node)
                return

        # Else: handle literal stuff.
        if not closed and len(self._nodestack) > 1:
            # need that for proper (un-)nesting
            self._tagstack.append((starttag, None))
        self.handle_text(data)

    def handle_endtag(self, name, data):
        """ :see: `ListenerInterface` """
        endtag = self.decoder.normalize(name)
        tagstack = self._tagstack
        if tagstack:
            starttag, node = tagstack[-1]
            if starttag == endtag:
                tagstack.pop()

                # Handle endtag of processable node.
                if node is not None:
                    self._flush_text()
                    node = self._nodestack.pop()
                    if self._devnull:
                        self._devnull = False
                    else:
                        node.endtag = data
                    return

        self.handle_text(data)

    def handle_comment(self, data):
        """ :see: `ListenerInterface` """
        self.handle_text(data)

    def handle_msection(self, name, value, data):
        """ :see: `ListenerInterface` """
        # pylint: disable = W0613
        self.handle_text(data)

    def handle_decl(self, name, value, data):
        """ :see: `ListenerInterface` """
        # pylint: disable = W0613
        self.handle_text(data)

    def handle_pi(self, data):
        """ :see: `ListenerInterface` """
        self.handle_text(data)

    #########################################################################
    ### BuildingListenerInterface Extension #################################
    #########################################################################

    def handle_encoding(self, encoding):
        """
        :See: `tdi.interfaces.BuildingListenerInterface`

        :Exceptions:
          - `TemplateEncodingError` : encoding was not recognized
        """
        try:
            _codecs.lookup(encoding)
        except LookupError, e:
            raise TemplateEncodingError(str(e))
        if self.encoding != encoding:
            self.encoding = encoding
            self.encoder.encoding = encoding
            self.decoder.encoding = encoding

    #########################################################################
    ### BuilderInterface ####################################################
    #########################################################################

    def finalize(self):
        """ :See: `tdi.interfaces.BuilderInterface` """
        self._flush_text()
        self._tree.finalize(self.encoder, self.decoder)
        return self._tree
