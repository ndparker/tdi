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

======================
 Node Tree Structures
======================

This module provides node tree management.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

from ._exceptions import NodeNotFoundError, NodeTreeError
from . import _finalize
from . import _nodetree
from . import _util


class RawNode(object):
    """
    Lightweight node for raw content and attribute assignment

    :IVariables:
      `_udict` : ``dict``
        The dict containing node information
    """
    __slots__ = ['content', 'encoder', 'decoder', '_udict']

    # pylint: disable = protected-access

    def __init__(self, node):
        """
        Initialization

        :Parameters:
          `node` : `Node`
            The original node
        """
        self._udict = node._udict

    @_util.Property
    def content():
        """
        Raw content

        :Type: ``str``
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = missing-docstring

        unicode_, str_, isinstance_ = unicode, str, isinstance

        def fset(self, content):
            udict = self._udict
            if isinstance_(content, unicode_):
                cont = udict['encoder'].encode(content)
            else:
                cont = str_(content)
            udict['content'] = (cont, cont)
            udict['namedict'] = {}

        def fget(self):
            return self._udict['content'][0]
        return locals()

    @_util.Property
    def encoder():
        """
        Output encoder

        :Type: `EncoderInterface`
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = missing-docstring

        def fget(self):
            return self._udict['encoder']
        return locals()

    @_util.Property
    def decoder():
        """
        Input decoder

        :Type: `DecoderInterface`
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = missing-docstring

        def fget(self):
            return self._udict['decoder']
        return locals()

    def __setitem__(self, name, value):
        """
        Set the attribute `name` to `value`

        The value is *not* encoded according to the model.
        The original case of `name` is preserved. If the attribute does not
        occur in the original template, the case of the passed `name` is
        taken over. Non-string values (including unicode, but not ``None``)
        are converted to string using ``str()``.

        :Parameters:
          `name` : ``str``
            The attribute name (case insensitive)

          `value` : ``str``
            The attribute value (may be ``None`` for short
            attributes). Objects that are not ``None`` and and not
            ``unicode`` are stored as their string representation.
        """
        udict = self._udict
        if value is not None:
            if isinstance(value, unicode):
                value = udict['encoder'].encode(value)
            else:
                value = str(value)
        attr = udict['attr']
        name = udict['encoder'].name(name)
        normname = udict['decoder'].normalize(name)
        realname = attr.get(normname, (name,))[0]
        attr[normname] = (realname, value)

    def __getitem__(self, name):
        """
        Determine the value of attribute `name`

        :Parameters:
          `name` : ``str``
            The attribute name

        :Return: The attribute (``None`` for shorttags)
        :Rtype: ``str``

        :Exceptions:
          - `KeyError` : The attribute does not exist
        """
        udict = self._udict
        return udict['attr'][
            udict['decoder'].normalize(udict['encoder'].name(name))
        ][1]

    def __delitem__(self, name):
        """
        Delete attribute `name`

        If the attribute does not exist, no exception is raised.

        :Parameters:
          `name` : ``str``
            The name of the attribute to delete (case insensitive)
        """
        udict = self._udict
        try:
            del udict['attr'][
                udict['decoder'].normalize(udict['encoder'].name(name))
            ]
        except KeyError:
            # Ignore, because this is not an error.
            pass


class Node(object):
    """
    User visible node object

    :IVariables:
      `ctx` : ``tuple``
        The node context (``None`` if there isn't one). Node contexts
        are created on repetitions for all (direct and no-direct) subnodes of
        the repeated node. The context is a ``tuple``, which contains for
        repeated nodes the position within the loop (starting with ``0``), the
        actual item and a tuple of the fixed parameters. The last two are also
        passed to the repeat callback function directly. For separator
        nodes, ``ctx[1]`` is a tuple containing the items before the separator
        and after it. Separator indices are starting with ``0``, too.

      `_model` : `ModelAdapterInterface`
        The template model object

      `_udict` : ``dict``
        The dict containing node information
    """
    _usernode = True
    __slots__ = ['content', 'raw', 'ctx', '_model', '_udict']

    # pylint: disable = protected-access

    @_util.Property
    def content():
        """
        Node content

        The property can be set to a unicode or str value, which will be
        escaped and encoded (in case of unicode). It replaces the content or
        child nodes of the node completely.

        The property can be read and will either return the *raw* content of
        the node (it may even contain markup) - or ``None`` if the node has
        subnodes.

        :Type: ``basestring`` or ``None``
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = missing-docstring

        basestring_, isinstance_, str_ = basestring, isinstance, str

        def fset(self, content):
            if not isinstance_(content, basestring_):
                content = str_(content)
            udict = self._udict
            udict['content'] = (udict['encoder'].content(content), None)
            udict['namedict'] = {}

        def fget(self):
            return self._udict['content'][0]
        return locals()

    @_util.Property
    def hiddenelement():
        """
        Hidden node markup?

        :Type: ``bool``
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = missing-docstring

        def fset(self, value):
            self._udict['noelement'] = value and True or False

        def fget(self):
            return self._udict['noelement']
        return locals()

    @_util.Property
    def closedelement():
        """
        Self-closed element? (read-only)

        :Type: ``bool``
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = missing-docstring

        def fget(self):
            return self._udict['closed']
        return locals()

    @_util.Property
    def raw():
        """
        Raw node

        :Type: `RawNode`
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = missing-docstring

        def fget(self):
            return RawNode(self)
        return locals()

    def __new__(cls, node, model, ctx=None, light=False):
        """
        Construction

        :Parameters:
          `node` : `Node` or `TemplateNode`
            The node to clone

          `model` : `ModelAdapterInterface`
            The template model instance

          `ctx` : ``tuple``
            The node context

          `light` : ``bool``
            Do a light copy? (In this case just the node context is
            updated and the *original* node is returned). Do this only if
            `node` is already a `Node` instance and you do not need another
            copy!

        :Return: The node instance
        :Rtype: `Node`
        """
        if light:
            if not node._udict.get('callback'):
                node.ctx = ctx
            return node

        self = object.__new__(cls)
        udict = node._udict.copy()
        udict['attr'] = udict['attr'].copy()
        udict['nodes'] = udict['nodes'][:]
        self._udict = udict
        self._model = model
        if udict.get('callback'):
            self.ctx = node.ctx
        else:
            self.ctx = ctx

        return self

    def __call__(self, name):
        """
        Determine direct subnodes by name

        In contrast to `__getattr__` this works for all names. Also the
        exception in case of a failed lookup is different.

        :Parameters:
          `name` : ``str``
            The name looked for

        :Return: The found node
        :Rtype: `Node`

        :Exceptions:
          - `NodeNotFoundError` : The subnode was not found
        """
        udict = self._udict
        try:
            name = str(name)
            idx = udict['namedict'][name]
        except (UnicodeError, KeyError):
            raise NodeNotFoundError(name)

        while idx < 0:  # walk through transparent "nodes"
            kind, result = udict['nodes'][-1 - idx]
            if not result._usernode:
                result = Node(result, self._model, self.ctx)
                udict['nodes'][-1 - idx] = (kind, result)
            udict = result._udict
            idx = udict['namedict'][name]

        kind, result = udict['nodes'][idx]
        if not result._usernode:
            result = Node(result, self._model, self.ctx)
            udict['nodes'][idx] = (kind, result)
        else:
            result.ctx = self.ctx

        return result

    def __getattr__(self, name):
        """
        Determine direct subnodes by name

        :Parameters:
          `name` : ``str``
            The name looked for

        :Return: The found subnode
        :Rtype: `Node`

        :Exceptions:
          - `AttributeError` : The subnode was not found
        """
        try:
            return self(name)
        except NodeNotFoundError:
            raise AttributeError("Attribute %s.%s not found" % (
                self.__class__.__name__, name
            ))

    def __setitem__(self, name, value):
        """
        Set the attribute `name` to `value`

        The value is encoded according to the model and the original case
        of `name` is preserved. If the attribute does not occur in the
        original template, the case of the passed `name` is taken over.
        Non-string values are converted to string using ``str()``. Unicode
        values are passed as-is to the model encoder.

        :Parameters:
          `name` : ``str``
            The attribute name (case insensitive)

          `value` : any
            The attribute value (may be ``None`` for short
            attributes). Objects that are not ``None`` and and not
            ``unicode`` are stored as their string representation.
        """
        udict = self._udict
        if value is not None:
            if not isinstance(value, basestring):
                value = str(value)
            value = udict['encoder'].attribute(value)

        attr = udict['attr']
        name = udict['encoder'].name(name)
        normname = udict['decoder'].normalize(name)
        realname = attr.get(normname, [name])[0]
        attr[normname] = (realname, value)

    def __getitem__(self, name):
        """
        Determine the value of attribute `name`

        :Parameters:
          `name` : ``str``
            The attribute name

        :Return: The attribute (``None`` for shorttags)
        :Rtype: ``str``

        :Exceptions:
          - `KeyError` : The attribute does not exist
        """
        udict = self._udict
        value = udict['attr'][
            udict['decoder'].normalize(udict['encoder'].name(name))
        ][1]
        if value and (value.startswith('"') or value.startswith("'")):
            value = value[1:-1]

        return value

    def __delitem__(self, name):
        """
        Delete attribute `name`

        If the attribute does not exist, no exception is raised.

        :Parameters:
          `name` : ``str``
            The name of the attribute to delete (case insensitive)
        """
        udict = self._udict
        try:
            del udict['attr'][
                udict['decoder'].normalize(udict['encoder'].name(name))
            ]
        except KeyError:
            # Ignore, because this is not an error.
            pass

    def repeat(self, callback, itemlist, *fixed, **kwargs):
        """
        Repeat the snippet ``len(list(itemlist))`` times

        The actually supported signature is::

            repeat(self, callback, itemlist, *fixed, separate=None)

        Examples::

            def render_foo(self, node):
                def callback(node, item):
                    ...
                node.repeat(callback, [1, 2, 3, 4])

            def render_foo(self, node):
                def callback(node, item):
                    ...
                def sep(node):
                    ...
                node.repeat(callback, [1, 2, 3, 4], separate=sep)

            def render_foo(self, node):
                def callback(node, item, foo, bar):
                    ...
                node.repeat(callback, [1, 2, 3, 4], "foo", "bar")

            def render_foo(self, node):
                def callback(node, item, foo, bar):
                    ...
                def sep(node):
                    ...
                node.repeat(callback, [1, 2, 3, 4], "foo", "bar",
                            separate=sep)

        :Parameters:
          `callback` : ``callable``
            The callback function

          `itemlist` : iterable
            The items to iterate over

          `fixed` : ``tuple``
            Fixed parameters to be passed to the repeat methods

        :Keywords:
          `separate` : ``callable``
            Alternative callback function for separator nodes. If omitted or
            ``None``, ``self.separate_name`` is looked up and called if it
            exists.
        """
        if 'separate' in kwargs:
            if len(kwargs) > 1:
                raise TypeError("Unrecognized keyword parameters")
            separate = kwargs['separate']
        elif kwargs:
            raise TypeError("Unrecognized keyword parameters")
        else:
            separate = None
        self._udict['repeated'] = (callback, iter(itemlist), fixed, separate)

    def remove(self):
        """
        Remove the node from the tree

        Tells the system, that the node (and all of its subnodes) should
        not be rendered.
        """
        self._udict['removed'] = True
        self._udict['namedict'] = {}

    def iterate(self, itemlist, separate=None):
        """
        Iterate over repeated nodes

        Iteration works by repeating the original node
        ``len(list(iteritems))`` times, turning the original node into a
        container node and appending the generated nodeset to that container.
        That way, the iterated nodes are virtually indented by one level, but
        the container node is completely hidden, so it won't be visible.

        All repeated nodes are marked as ``DONE``, so they (and their
        subnodes) are not processed any further (except explicit callbacks).
        If there is a separator node assigned, it's put between the
        repetitions and *not* marked as ``DONE``. The callbacks to them
        (if any) are executed when the template system gets back to control.

        :Parameters:
          `itemlist` : iterable
            The items to iterate over

          `separate` : ``callable``
            Alternative callback function for separator nodes. If omitted or
            ``None``, ``self.separate_name`` is looked up and called if it
            exists.

        :Return: The repeated nodes and items (``[(node, item), ...]``)
        :Rtype: iterable
        """
        itemlist = iter(itemlist)
        node, nodelist = self.copy(), []

        # This effectively indents the iterated nodeset by one level.
        # The original node (which was copied from before) only acts as a
        # container now.
        self._udict['content'] = (None, None)
        self._udict['nodes'] = nodelist
        self._udict['namedict'] = {}
        self._udict['masked'] = True

        return _nodetree.iterate(
            node, nodelist, itemlist, separate, Node
        )

    def replace(self, callback, other, *fixed):
        """
        Replace the node (and all subnodes) with the copy of another one

        The replacement node is deep-copied, so use it with care
        (performance-wise).

        :Parameters:
          `callback` : ``callable``
            callback function

          `other` : `Node`
            The replacement node

          `fixed` : ``tuple``
            Fixed parameters for the callback

        :Return: The replaced node (actually the node itself, but with
                 updated parameters)
        :Rtype: `Node`
        """
        udict = other._udict.copy()
        udict['attr'] = udict['attr'].copy()
        ctx, deep, TEXT = self.ctx, _nodetree.copydeep, _nodetree.TEXT_NODE
        model = self._model

        udict['nodes'] = [(
            kind,
            (kind != TEXT and node._usernode)
            and deep(node, model, ctx, Node) or node
        ) for kind, node in udict['nodes']]

        udict['name'] = self._udict['name']  # name stays the same
        udict['callback'] = callback
        udict['complete'] = fixed

        self._udict = udict
        return self

    def copy(self):
        """
        Deep copy this node

        :Return: The node copy
        :Rtype: `Node`
        """
        return _nodetree.copydeep(self, self._model, self.ctx, Node)

    def render(self, *callback, **kwargs):
        """
        render(self, callback, params, **kwargs)

        Render this node only and return the result as string

        Note that callback and params are optional positional parameters::

            render(self, decode=True, decode_errors='strict')
            # or
            render(self, callback, decode=True, decode_errors='strict')
            # or
            render(self, callback, param1, paramx, ... decode=True, ...)

        is also possible.

        :Parameters:
          `callback` : callable or ``None``
            Optional callback function and additional parameters

          `params` : ``tuple``
            Optional extra parameters for `callback`

        :Keywords:
          `decode` : ``bool``
            Decode the result back to unicode? This uses the encoding of the
            template.

          `decode_errors` : ``str``
            Error handler if decode errors happen.

          `model` : any
            New render model, if omitted or ``None``, the current model is
            applied.

          `adapter` : ``callable``
            Model adapter factory, takes the model and returns a
            `ModelAdapterInterface`. If omitted or ``None``, the current
            adapter is used. This parameter is ignored, if no ``model``
            parameter is passed.

        :Return: The rendered node, type depends on ``decode`` keyword
        :Rtype: ``basestring``
        """
        decode = kwargs.pop('decode', True)
        decode_errors = kwargs.pop('decode_errors', 'strict')
        model = kwargs.pop('model', None)
        adapter = kwargs.pop('adapter', None)
        if kwargs:
            raise TypeError("Unrecognized keyword parameters")

        if model is None:
            model = self._model
        elif adapter is None:
            model = self._model.new(model)
        else:
            model = adapter(model)

        node = _nodetree.copydeep(self, model, self.ctx, Node)
        if callback and callback[0] is not None:
            node.replace(callback[0], node, *callback[1:])
        else:
            node.replace(None, node)
        res = ''.join(_nodetree.render(node, model, Node))
        if not decode:
            return res
        return res.decode(self._udict['decoder'].encoding, decode_errors)


class TemplateNode(object):
    """
    Template node

    This is kind of a proto node. During rendering each template node is
    turned into a user visible `Node` object, which implements the user
    interface. `TemplateNode` objects provide a tree building interface
    instead.

    :IVariables:
      `_udict` : ``dict``
        The dict containing node information

      `_finalized` : ``bool``
        Was the tree finalized?
    """
    ctx = None
    _usernode = False

    # pylint: disable = protected-access

    @_util.Property
    def endtag():
        """
        End tag of the node

        :Type: ``str``
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = missing-docstring

        def fset(self, data):
            if self._finalized:
                raise NodeTreeError("Tree was already finalized")
            if self._udict['closed']:
                raise NodeTreeError(
                    "Self-closing elements cannot have an endtag"
                )
            if not isinstance(data, str):
                raise NodeTreeError("Endtag data must be a string")
            self._udict['endtag'] = data

        def fget(self):
            return self._udict.get('endtag')
        return locals()

    def __init__(self, tagname, attr, special, closed):
        """
        Initialization

        :Parameters:
          `tagname` : ``str``
            The name of the accompanying tag

          `attr` : iterable
            The attribute list (``((name, value), ...)``)

          `special` : ``dict``
            Special node information
        """
        scope = special.get('scope')
        overlay = special.get('overlay')
        tdi = special.get('attribute')
        if tdi is None:
            flags, name = '', None
        else:
            flags, name = tdi

        if overlay is None:
            overlay = False, False, False, None
        else:
            overlay = (
                '-' in overlay[0],  # is_hidden
                '>' in overlay[0],  # is_target
                '<' in overlay[0],  # is_source
                overlay[1],         # name
            )

        if scope is None:
            scope = False, False, None
        else:
            scope = (
                ('-' in scope[0]),  # is_hidden
                ('=' in scope[0]),  # is_absolute
                scope[1],           # name
            )
            if not scope[0] and not scope[1] and not scope[2]:
                scope = False, False, None

        self._udict = {
            'sep': None,
            'nodes': [],
            'content': (None, None),
            'attr_': tuple(attr),
            'removed': False,
            'repeated': None,
            'name': name or None,
            'closed': closed,
            'tagname': tagname,
            'noelement': '-' in flags or overlay[0] or scope[0],
            'noauto': '*' in flags,
            'masked': False,
            'overlay': overlay,
            'scope': scope,
        }
        self._finalized = False

    def append_text(self, content):
        """
        Append a text node

        :Parameters:
          `content` : ``str``
            The text node content

        :Exceptions:
          - `NodeTreeError` : The tree was already finalized
        """
        if self._finalized:
            raise NodeTreeError("Tree was already finalized")

        self._udict['nodes'].append((_nodetree.TEXT_NODE, (content, content)))

    def append_escape(self, escaped, content):
        """
        Append an escaped node

        :Parameters:
          `escaped` : ``str``
            The escaped string (in unescaped form, i.e. the final result)

          `content` : ``str``
            The escape string (the whole sequence)

        :Exceptions:
          - `NodeTreeError` : The tree was already finalized
        """
        if self._finalized:
            raise NodeTreeError("Tree was already finalized")

        self._udict['nodes'].append((_nodetree.TEXT_NODE, (escaped, content)))

    def append_node(self, tagname, attr, special, closed):
        """
        Append processable node

        :Parameters:
          `tagname` : ``str``
            The name of the accompanying tag

          `attr` : iterable
            The attribute list (``((name, value), ...)``)

          `special` : ``dict``
            Special attributes. If it's empty, something's wrong.

          `closed` : ``bool``
            Closed tag?

        :Return: new `TemplateNode` instance
        :Rtype: `TemplateNode`

        :Exceptions:
          - `NodeTreeError` : The tree was already finalized
          - `AssertionError` : nothing special
        """
        if self._finalized:
            raise NodeTreeError("Tree was already finalized")

        assert len(special), "Nothing special about this node."

        node = TemplateNode(tagname, attr, special, bool(closed))
        tdi = special.get('attribute')
        if tdi is not None and ':' in tdi[0]:
            kind = _nodetree.SEP_NODE
        else:
            kind = _nodetree.PROC_NODE
        self._udict['nodes'].append((kind, node))

        return node


class Root(TemplateNode):
    """
    Root Node class

    This class has to be used as the initial root of the tree.
    """
    _sources, _targets = None, None

    # pylint: disable = protected-access

    @_util.Property
    def encoder():
        """
        Output encoder

        :Type: `EncoderInterface`
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = missing-docstring

        def fget(self):
            return self._udict['encoder']
        return locals()

    @_util.Property
    def decoder():
        """
        Input decoder

        :Type: `DecoderInterface`
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = missing-docstring

        def fget(self):
            return self._udict['decoder']
        return locals()

    @_util.Property
    def source_overlay_names():
        """
        Source overlay names

        :Type: iterable
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = missing-docstring

        def fget(self):
            if self._sources is None:
                return ()
            return self._sources.iterkeys()
        return locals()

    @_util.Property
    def target_overlay_names():
        """
        Target overlay names

        :Type: iterable
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = missing-docstring

        def fget(self):
            if self._targets is None:
                return ()
            return self._targets.iterkeys()
        return locals()

    def __init__(self):
        """ Initialization """
        super(Root, self).__init__('', (), {}, False)
        self.endtag = ''
        self._udict['is_root'] = True

    def __str__(self):
        """ String representation of the tree """
        return self.to_string(verbose=True)

    def to_string(self, verbose=False):
        """
        String representation of the tree

        :Parameters:
          `verbose` : ``bool``
            Show (shortened) text node content and separator nodes?

        :Return: The string representation
        :Rtype: ``str``
        """
        if not self._finalized:
            raise NodeTreeError("Tree was not finalized yet")
        return '\n'.join(list(
            _nodetree.represent(self._udict, bool(verbose))
        )) + '\n'

    def finalize(self, encoder, decoder):
        """
        Finalize the tree

        This method assigns separator nodes to their accompanying content
        nodes, concatenates adjacent text nodes and tries to optimize
        the tree a bit.

        :Parameters:
          `encoder` : `EncoderInterface`
            Encoder instance

        :Exceptions:
          - `NodeTreeError` : The tree was already finalized or endtag was not
            set
        """
        if self._finalized:
            raise NodeTreeError("Tree was already finalized")
        self._sources, self._targets = \
            _finalize.finalize(self._udict, encoder, decoder)
        self._finalized = True

    def overlay(self, other):
        """
        Overlay this tree with another one

        :Parameters:
          `other` : `Root`
            The tree to lay over

        :Exceptions:
          - `NodeTreeError` : Finalization error
        """
        if not self._finalized:
            raise NodeTreeError("Tree was not finalized yet.")
        if not other._finalized:
            raise NodeTreeError("Overlay tree was not finalized yet.")
        return _nodetree.overlay(
            self._udict, other._sources, TemplateNode, Root
        )

    def render(self, model, startnode=None):
        """
        Render the tree into chunks, calling `model` for input

        :Parameters:
          `model` : `ModelAdapterInterface`
            The model object

          `startnode` : ``str``
            Only render this node (and all its children). The node
            is addressed via a dotted string notation, like ``a.b.c`` (this
            would render the ``c`` node.) The notation does not describe a
            strict node chain, though. Between to parts of a node chain may
            be gaps in the tree. The algorithm looks out for the first
            matching node. It does no backtracking and so does not cover all
            branches (yet?), but that works fine for realistic cases :). A
            non-working example would be (searching for a.b.c)::

              *
              +- a
              |  `- b - d
              `- a
                 `- b - c

        :Return: Rendered chunks
        :Rtype: iterable
        """
        return _nodetree.render(
            _nodetree.findnode(self, startnode), model, Node
        )


from . import c
c = c.load('impl')
if c is not None:
    Root, Node, RawNode, TemplateNode = (  # noqa
        c.Root, c.Node, c.RawNode, c.TemplateNode
    )
del c
