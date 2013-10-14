# -*- coding: ascii -*-
#
# Copyright 2007 - 2013
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
====================================
 Interfaces used in the tdi package
====================================

The module provides all interfaces required or provided by the `tdi`
package and a small function to check for them.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"


def implements(obj, *interfaces):
    """
    Check if `obj` implements one or more interfaces.

    The check looks for the ``__implements__`` attribute of ``obj``, which
    is expected to be an iterable containing the implemented interfaces.

    :Parameters:
      `obj` : ``type`` or ``object``
        The object to inspect

      `interfaces` : ``tuple``
        Interface classes to check

    :Return: Are all interfaces implemented?
    :Rtype: ``bool``
    """
    try:
        impls = tuple(obj.__implements__)
    except AttributeError:
        return False

    def subclass(sub, sup, _subclass=issubclass):
        """ Type error proof subclass check """
        try:
            return _subclass(sub, sup)
        except TypeError:
            return False

    # O(n**2), better ideas welcome, however, usually the list is pretty
    # small.
    for interface in interfaces:
        for impl in impls:
            if subclass(impl, interface):
                break
        else:
            return False
    return True


class ListenerInterface(object):
    """
    Interface for a parser/lexer event listener.
    """

    def handle_text(self, data):
        """
        Handle text data

        :Parameters:
          `data` : ``str``
            The text data to handle
        """

    def handle_escape(self, escaped, data):
        """
        Handle escaped data

        :Parameters:
          `escaped` : ``str``
            The escaped string (unescaped, despite the name)

          `data` : ``str``
            The full escape sequence
        """

    def handle_starttag(self, name, attrs, closed, data):
        """
        Handle start tag (``<foo ....>``)

        :Parameters:
          `name` : ``str``
            The element name (``''`` for empty tag)

          `attrs` : ``list``
            The attributes (``[(name, value), ...]``), where ``value``
            may be ``None`` for short attributes.

          `closed` : ``bool``
            Is the start tag closed? In that case, no endtag will be needed.

          `data` : ``str``
            The raw tag string
        """

    def handle_endtag(self, name, data):
        """
        Handle end tag (``</foo>``)

        :Parameters:
          `name` : ``str``
            The element name (``''`` for empty tag)

          `data` : ``str``
            The raw tag string
        """

    def handle_comment(self, data):
        """
        Handle comment (``<!-- ... -->``)

        :Parameters:
          `data` : ``str``
            The comment block
        """

    def handle_msection(self, name, value, data):
        """
        Handle marked section (``<![name[...]]>`` or ``<![name ...]>``)

        The ``<![name ... ]>`` sections are MS specific. ``markupbase``
        comments::

          # An analysis of the MS-Word extensions is available at
          # http://www.planetpublish.com/xmlarena/xap/Thursday/WordtoXML.pdf

        :Parameters:
          `name` : ``str``
            The section name

          `value` : ``str``
            The section value

          `data` : ``str``
            The section block
        """

    def handle_decl(self, name, value, data):
        """
        Handle declaration (``<!...>``)

        :Parameters:
          `name` : ``str``
            The name of the declaration block

          `value` : ``str``
            The value of the declaration block

          `data` : ``str``
            The declaration block
        """

    def handle_pi(self, data):
        """
        Handle Processing instruction (``<? ... ?>``)

        :Parameters:
          `data` : ``str``
            The PI block
        """


class ParserInterface(object):
    """ Interface for template parsers """

    def feed(self, food):
        """
        Take a chunk of data and generate parser events out of it

        :Parameters:
          `food` : ``str``
            The data to process
        """

    def finalize(self):
        """
        Finish the parser

        Calling `finalize` indicates that `feed` is not called any more
        and advises the parser to flush all pending events.
        """


class DTDInterface(object):
    """ Interface for DTD query classes """

    def cdata(self, name):
        """
        Determine if the element `name` is a CDATA element

        :Parameters:
          `name` : ``str``
            The name of the element (lowercased)

        :Return: CDATA element?
        :Rtype: ``bool``
        """

    def nestable(self, outer, inner):
        """
        Determine if the element `inner` may occur in `outer`.

        :Parameters:
          `outer` : ``str``
            The name of the outer element (lowercased)

          `inner` : ``str``
            The name of the inner element (lowercased)

        :Return: nestable?
        :Rtype: ``bool``
        """

    def empty(self, name):
        """
        Determines if the element `name` is empty.

        :Parameters:
          `name` : ``str``
            The element name (lowercased)

        :Return: Empty element?
        :Rtype: ``bool``
        """


class AttributeAnalyzerInterface(object):
    """
    Interface for Attribute analyzers

    :IVariables:
      `attribute` : ``str``
        The attribute name

      `scope` : ``str``
        The scope attribute name
    """

    def __call__(self, normalize, attr, name=''):
        """
        Analyze attributes

        :Parameters:
          `normalize` : ``callable``
            Element and attribute name normalizer

          `attr` : sequence
            (key, value) list of attributes. value may be ``None``

          `name` : ``str``
            Name to treat as attribute. Only applied if set and not empty.

        :Return: The (possibly) reduced attributes and a dict of special
                 attributes. All of the special attributes are optional:

                 ``attribute``
                    ``(flags, name)``
                 ``overlay``
                    ``(flags, name)`` or ``None``
                 ``scope``
                    ``(flags, name)`` or ``None``

        :Rtype: ``tuple``
        """


class BuilderInterface(object):
    """ Interface for builders """

    def finalize(self):
        """
        Finalize the build

        Flush all buffers, finalize the parse tree, etc

        :Return: The built result
        :Rtype: any
        """


class BuildingListenerInterface(ListenerInterface):
    """
    Extensions to the listener interface

    :IVariables:
      `encoder` : `EncoderInterface`
        Encoder

      `decoder` : `DecoderInterface`
        Decoder

      `encoding` : ``str``
        Encoding of the template

      `analyze` : `AttributeAnalyzerInterface`
        Attribute analyzer
    """

    def handle_encoding(self, encoding):
        """
        Handle an encoding declaration

        :Parameters:
          `encoding` : ``str``
            The encoding to handle
        """


class FilterFactoryInterface(object):
    """ Interface for a factory returning a filter """

    def __call__(self, builder):
        """
        Determine the actual filter instance

        :Parameters:
          `builder` : `BuildingListenerInterface`
            The next level builder

        :Return: The new filter instance
        :Rtype: `BuildingListenerInterface`
        """


class DecoderInterface(object):
    """
    Decoder Interface

    :IVariables:
      `encoding` : ``str``
        The source encoding
    """

    def normalize(self, name):
        """
        Normalize a name

        :Parameters:
          `name` : ``basestring``
            The name to normalize

        :Return: The normalized name
        :Rtype: ``basestring``
        """

    def decode(self, value, errors='strict'):
        """
        Decode an arbitrary value

        :Parameters:
          `value` : ``str``
            attribute value

          `errors` : ``str``
            Error handler description

        :Return: The decoded value
        :Rtype: ``unicode``
        """

    def attribute(self, value, errors='strict'):
        """
        Decode a raw attribute value

        :Parameters:
          `value` : ``str``
            Raw attribute value

          `errors` : ``str``
            Error handler description

        :Return: The decoded attribute
        :Rtype: ``unicode``
        """


class EncoderInterface(object):
    """
    Encoder Interface

    :IVariables:
      `encoding` : ``str``
        The target encoding
    """

    def starttag(self, name, attr, closed):
        """
        Build a starttag

        :Parameters:
          `name` : ``str``
            The tag name

          `attr` : iterable
            The tag attributes (``((name, value), ...)``)

          `closed` : ``bool``
            Closed tag?

        :Return: The starttag
        :Rtype: ``str``
        """

    def endtag(self, name):
        """
        Build an endtag

        :Parameters:
          `name` : ``str``
            Tag name

        :Return: The endtag
        :Rtype: ``str``
        """

    def name(self, name):
        """
        Encode a name (tag or attribute name)

        :Parameters:
          `name` : ``basestring``
            Name

        :Return: The encoded name
        :Rtype: ``str``
        """

    def attribute(self, value):
        """
        Attribute encoder

        Note that this method also needs to put quotes around the attribute
        (if applicable).

        :Parameters:
          `value` : ``basestring``
            The value to encode

        :Return: The encoded attribute
        :Rtype: ``str``
        """

    def content(self, value):
        """
        Regular text content encoder

        :Parameters:
          `value` : ``basestring``
            The value to encode

        :Return: The encoded attribute
        :Rtype: ``str``
        """

    def encode(self, value):
        """
        Character-encode a unicode string to `encoding`

        :Parameters:
          `value` : ``unicode``
            The value to encode

        :Return: The encoded value
        :Rtype: ``str``
        """

    def escape(self, value):
        """
        Escape text (scan for sequences needing escaping and escape them)

        :Parameters:
          `value` : ``str``
            The value to escape

        :Return: The escaped value
        :Rtype: ``str``
        """


class ModelAdapterInterface(object):
    """
    Model Adapter Interface

    :IVariables:
      `modelmethod` : ``callable``
        The function to resolve model methods

      `emit_escaped` : ``bool``
        Emit escaped text as escape sequence? (Needed for pre-rendering)
    """


class MemoizerInterface(object):
    """
    Interface for factory memoizers

    :Note: dicts implement this easily, but without the (optional) local lock.

    :IVariables:
      `lock` : Lock
        A lock object for the cache access. The lock needs an acquire method
        and a release method. If the attribute does not exist or is ``None``,
        cache access is serialized using a global lock. If you have multiple
        caches (for whatever reasons) this local lock is handy.
    """

    def __contains__(self, key):
        """
        Is this key memoized already?

        :Parameters:
          `key` : hashable
            Key

        :Return: Is it?
        :Rtype: ``bool``

        :Exceptions:
          - `TypeError` : Unhashable key
        """

    def __getitem__(self, key):
        """
        Get memoized entry

        :Parameters:
          `key` : hashable
            Key

        :Return: The memoized value
        :Rtype: any

        :Exceptions:
          - `TypeError` : Unhashable key
        """

    def __setitem__(self, key, value):
        """
        Memoize entry

        :Parameters:
          `key` : hashable
            Key

          `value` : any
            The value to memoize

        :Exceptions:
          - `TypeError` : Unhashable key
        """
