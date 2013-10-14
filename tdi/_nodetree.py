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
======================
 Node Tree Structures
======================

This module provides node tree management.

:Groups:
  - `Node Kinds` : `TEXT_NODE`, `PROC_NODE`, `SEP_NODE`, `CB_NODE`,
    `DONE_NODE`

:Variables:
  `TEXT_NODE` : ``int``
    Text node type

  `PROC_NODE` : ``int``
    Processable node type

  `SEP_NODE` : ``int``
    Separator node type

  `CB_NODE` : ``int``
    Callback node

  `DONE_NODE` : ``int``
    Already processed node
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

# pylint: disable = W0212 
# Access to a protected member _udict of a client class

import itertools as _it

from tdi._exceptions import NodeNotFoundError, NodeTreeError


TEXT_NODE, PROC_NODE, SEP_NODE, CB_NODE, DONE_NODE = xrange(5)


def overlay(udict, oindex, template, root):
    """
    Overlay udict to result using overlays stored in oindex

    :Parameters:
      `udict` : ``dict``
        Original root udict

      `oindex` : ``dict``
        Overlay index

      `template` : ``type``
        Template node type

      `root` : ``type``
        Root node type

    :Return: The result node again, fully overlayed
    :Rtype: `nodetree.Root`
    """
    exhausted, TEXT = StopIteration, TEXT_NODE
    _iter, _dict = iter, dict
    result, nodes, in_overlay = root(), [], False
    result._udict = _dict(udict, nodes=nodes)
    stack = [(nodes, _iter(udict['nodes']).next, in_overlay)]
    push, pop = stack.append, stack.pop

    def transfer(node, in_overlay, append):
        """ Transfer the subnode to the new tree """
        if node is None:
            return None, in_overlay
        nodes, newnode = [], template('', (), {}, node._udict['closed'])
        (_, _, osource, oname), old_io = node._udict['overlay'], in_overlay

        tdi = node._udict['name']
        tdiscope = node._udict['scope']
        if not in_overlay and not osource and oname in oindex:
            node = oindex[oname]
            if node is None:
                raise NodeTreeError("Ambiguous overlay %r" % (oname,))
            in_overlay = True
            if tdi is None:
                tdi = node._udict['name']
            if tdiscope[2] is None:
                tdiscope = node._udict['scope']
        newnode._udict = _dict(
            node._udict, nodes=nodes, name=tdi, scope=tdiscope,
        )
        if append is not None:
            stack[-1][0].append((append, newnode))
        push((nodes, _iter(node._udict['nodes']).next, old_io))
        newnode._udict['sep'], in_overlay = transfer(
            newnode._udict['sep'], in_overlay, None
        )
        return newnode, in_overlay

    while stack:
        try:
            kind, node = stack[-1][1]()
        except exhausted:
            _, _, in_overlay = pop()
        else:
            if kind == TEXT:
                stack[-1][0].append((kind, node))
            else:
                _, in_overlay = transfer(node, in_overlay, kind)

    result.finalize(result._udict['encoder'], result._udict['decoder'])
    return result


def _repeat(node, user_node, model, callback, itemlist, fixed, separate):
    """
    Repeat a node

    :Parameters:
      `node` : `nodetree.Node`
        The node to repeat (it will be copied, but not touched)

      `user_node` : ``type``
        User node type

      `model` : `ModelAdapterInterface`
        The model object

      `callback` : ``callable``
        The callback function

      `itemlist` : iterable
        The items to iterate over

      `fixed` : ``tuple``
        Fixed parameters for the callback function

      `separate` : ``callable``
        Alternative separator callback or ``None``

    :Return: The repeated nodes (``[(kind, node), ...]``)
    :Rtype: iterable
    """
    itemlist = enumerate(itemlist)
    idx, item = itemlist.next()
    udict, CB = node._udict, CB_NODE
    try:
        del udict['callback'] # just make sure
    except KeyError:
        pass
    udict['repeated'] = None
    sep = udict['sep']
    if sep is not None:
        if separate is None and udict['name'] is not None:
            sepcall = model.modelmethod(
                'separate', udict['name'], sep._udict['modelscope'],
                sep._udict['noauto'],
            )
        else:
            sepcall = separate

    deep = copydeep
    repeated_node = deep(node, model, (0, item, fixed), user_node)
    repeated_node._udict['callback'] = callback
    repeated_node._udict['complete'] = (item,) + fixed
    yield (CB, repeated_node)

    if sep is None:
        for idx, item in itemlist:
            repeated_node = deep(node, model, (idx, item, fixed), user_node)
            repeated_node._udict['callback'] = callback
            repeated_node._udict['complete'] = (item,) + fixed
            yield (CB, repeated_node)
    else:
        if sepcall is None and sep._udict['complete'][0] is not None:
            sep_node = (TEXT_NODE, sep._udict['complete'])
            for idx, item in itemlist:
                yield sep_node
                repeated_node = deep(
                    node, model, (idx, item, fixed), user_node
                )
                repeated_node._udict['callback'] = callback
                repeated_node._udict['complete'] = (item,) + fixed
                yield (CB, repeated_node)
        else:
            last_item = item
            for idx, item in itemlist:
                repeated_sep = deep(
                    sep, model, (idx - 1, (last_item, item), fixed), user_node
                )
                repeated_sep._udict['callback'] = sepcall
                repeated_sep._udict['complete'] = fixed
                yield (CB, repeated_sep)
                repeated_node = deep(
                    node, model, (idx, item, fixed), user_node
                )
                repeated_node._udict['callback'] = callback
                repeated_node._udict['complete'] = (item,) + fixed
                yield (CB, repeated_node)
                last_item = item


def copydeep(node, model, ctx, user_node):
    """
    Deep-copy a node

    :Note: Template nodes are just taken over.

    :Parameters:
      `node` : `nodetree.Node` or `nodetree.TemplateNode`
        The node to deep-copy

      `model` : `ModelAdapterInterface`
        The model object

      `ctx` : any
        The desired node context (applied to all subnodes, too)

      `user_node` : ``type``
        user node class

    :Return: The copied node
    :Rtype: `nodetree.Node`
    """
    nodecopy = user_node(node, model, ctx)
    udict = nodecopy._udict
    if udict['content'][0] is None:
        TEXT, deep = TEXT_NODE, copydeep
        udict['nodes'] = [(kind, (kind != TEXT and node._usernode) and
            deep(node, model, ctx, user_node) or node
        ) for kind, node in udict['nodes']]

    return nodecopy


def represent(udict, verbose):
    """
    Create a string representation of the tree

    :Parameters:
      `udict` : ``dict``
        Startnode's dict

      `verbose` : ``bool``
        Include (shortened) text content and separator nodes?

    :Return: List of string lines
    :Rtype: ``list``
    """
    # pylint: disable = R0912
    _len, _iter, exhausted = len, iter, StopIteration
    TEXT, SEP = TEXT_NODE, SEP_NODE
    stack = []
    push, pop = stack.append, stack.pop

    def push_children(udict):
        """ Push a node """
        if udict['content'][0] is not None:
            nodes = [(TEXT, udict['content'])]
        else:
            nodes = udict['nodes']
            if verbose and udict['sep'] is not None:
                nodes = [(SEP, udict['sep'])] + nodes
        push(_iter(nodes).next)

    push_children(udict)

    def repr_content(content):
        """ prepare content line """
        content = repr(content)
        if _len(content) > 34:
            content = "%s...%s" % (content[:16], content[-16:])
        return '  ' * _len(stack) + content

    def repr_node(kind, udict):
        """ Prepare node line """
        content = udict['name'] or ''
        if kind == SEP:
            content = ":" + content
        if not verbose and udict['sep'] is not None:
            content += " (:)"
        if verbose and udict['overlay'][3]: # [3] == oname
            oresult = udict['overlay'][3]
            if udict['overlay'][0]:
                oresult = '-%s' % oresult
            if udict['overlay'][1]:
                oresult = '>%s' % oresult
            if udict['overlay'][2]:
                oresult = '<%s' % oresult
            content += " (<<< %s)" % oresult
        return '  ' * _len(stack) + content

    yield "/"
    while stack:
        try:
            kind, node = stack[-1]()
        except exhausted:
            pop()
            continue

        if kind == TEXT:
            if verbose:
                yield repr_content(node[0])
            continue

        udict = node._udict
        yield repr_node(kind, udict)
        push_children(udict)
    yield "\\"


def iterate(node, nodelist, itemlist, separate, user_node):
    """
    Actually iterate a node

    :Parameters:
      `node` : `nodetree.Node`
        Node to iterate

      `nodelist` : ``list``
        Node collector

      `itemlist` : iterable
        Item iterable

      `separate` : ``callable``
        Alternative separator callback or ``None``

      `user_node` : ``type``
        user node type

    :Return: (node, item) iterable
    :Rtype: iterable
    """
    item, DONE = itemlist.next(), DONE_NODE
    udict, model, push = node._udict, node._model, nodelist.append
    deep = copydeep
    sep = udict['sep']
    if sep is not None:
        if separate is None and udict['name'] is not None:
            sepcall = model.modelmethod(
                'separate', udict['name'], sep._udict['modelscope'],
                sep._udict['noauto'],
            )
        else:
            sepcall = separate

    repeated_node = deep(node, model, None, user_node)
    push((DONE, repeated_node))
    yield repeated_node, item

    if sep is None:
        for item in itemlist:
            repeated_node = deep(node, model, None, user_node)
            push((DONE, repeated_node))
            yield repeated_node, item
    else:
        if sepcall is None and sep._udict['complete'][0] is not None:
            sep_node = (TEXT_NODE, sep._udict['complete'])
            for item in itemlist:
                repeated_node = deep(node, model, None, user_node)
                push(sep_node)
                push((DONE, repeated_node))
                yield repeated_node, item
        else:
            fixed, CB, last_item = (), CB_NODE, item
            for idx, item in enumerate(itemlist):
                repeated_node = deep(node, model, None, user_node)
                repeated_sep = deep(
                    sep, model, (idx, (last_item, item), fixed), user_node
                )
                repeated_sep._udict['callback'] = sepcall
                repeated_sep._udict['complete'] = fixed
                last_item = item
                push((CB, repeated_sep))
                push((DONE, repeated_node))
                yield repeated_node, item


def findnode(current, nodestring):
    """
    Find a node by loose name

    :Parameters:
      `current` : `nodetree.Root`
        Node to start with

      `nodestring` : ``str``
        Node address. The node is addressed via a dotted string notation, like
        ``a.b.c`` (this would find the ``c`` node.) The notation does not
        describe a strict node chain, though. Between to parts of a node chain
        may be gaps in the tree. The algorithm looks out for the first
        matching node. It does no backtracking and so does not cover all
        branches (yet?), but that works fine for realistic cases :). A
        non-working example would be (searching for a.b.c)::

          *
          +- a
          |  `- b - d
          `- a
             `- b - c


    :Return: Found node
    :Rtype: `nodetree.TemplateNode`

    :Exceptions:
      - `NodeNotFoundError` : Node not found
    """
    # pylint: disable = R0912
    if nodestring is None:
        return current
    names = nodestring.split('.')
    names.reverse()
    while names:
        name = names.pop()

        # if name occurs within current children, resolve the node and
        # continue with next name
        idx = current._udict['namedict'].get(name)
        if idx is None:
            for idx, (kind, node) in enumerate(current._udict['nodes']):
                if kind != PROC_NODE:
                    continue
                if node._udict['name'] == name:
                    break
            else:
                idx = None
        if idx is not None:
            # resolve nameless pass-through
            while idx < 0:
                current = current._udict['nodes'][-1 - idx][1]
                idx = current._udict['namedict'][name]
            current = current._udict['nodes'][idx][1]
            continue

        # The name was not found directly. Walk the tree now (breadth-first)
        # and look it up. If that doesn't work: die.
        next_ = []
        if current._udict['nodes']:
            next_.append(current._udict['nodes'])
        while next_:
            # process: contains all nodes of the current level
            # next_: collects all nodes for the next level
            process, next_ = _it.chain(*next_), []
            for kind, current in process:
                if kind != PROC_NODE:
                    continue

                # if name occurs within current children, resolve the node and
                # continue with next name (we need to break out of two loops
                # before and jump after the while/else block)
                idx = current._udict['namedict'].get(name)
                if idx is None:
                    for idx, (kind, node) in \
                            enumerate(current._udict['nodes']):
                        if kind != PROC_NODE:
                            continue
                        if node._udict['name'] == name:
                            break
                    else:
                        idx = None
                if idx is not None:
                    while idx < 0:
                        current = current._udict['nodes'][-1 - idx][1]
                        idx = current._udict['namedict'][name]
                    current = current._udict['nodes'][idx][1]
                    break
                if current._udict['nodes']:
                    next_.append(current._udict['nodes'])
            else:
                continue
            break
        else:
            # re-add the unresolved name (prepare to die)
            names.append(name)
            break
        # continue # with next name

    if names:
        raise NodeNotFoundError(nodestring)
    return current


def render(startnode, model, user_node):
    """
    Render beginning with startnode

    :Parameters:
      `startnode` : `nodetree.TemplateNode`
        Node to begin with

      `model` : `ModelAdapterInterface`
        The model object

      `user_node` : ``type``
        User node type

    :Return: Iterable over rendered chunks
    :Rtype: iterable
    """
    # pylint: disable = R0912, R0914, R0915

    udict, escaped = startnode._udict, bool(model.emit_escaped)
    if udict.get('is_root') and udict['content'][0] is not None:
        yield udict['content'][escaped]
    else:
        _iter, exhausted = iter, StopIteration
        CB, DONE, TEXT = CB_NODE, DONE_NODE, TEXT_NODE,
        repeat, modelmethod = _repeat, model.modelmethod
        if udict.get('is_root'):
            rootnodes = [
                (kind, kind != TEXT and user_node(node, model) or node)
                for kind, node in udict['nodes']
            ]
        else:
            rootnodes = [(PROC_NODE, user_node(startnode, model))]
        #        done, nodes, endtag
        stack = [(False, _iter(rootnodes).next, None)]
        push, pop = stack.append, stack.pop

        depth_done = False
        while stack:
            try:
                kind, tnode = stack[-1][1]()
            except exhausted:
                depth_done, _, endtag = pop()
                if endtag:
                    yield endtag
                continue

            if kind == TEXT:
                yield tnode[escaped]
                continue

            udict = tnode._udict
            if udict['removed']:
                continue

            if kind == DONE and not 'callback' in udict:
                done = True
            else:
                next_node = False
                while 1:
                    user_control = False
                    if kind == CB or 'callback' in udict:
                        callback = udict.pop('callback')
                        if callback is None:
                            done = False
                        else:
                            done = callback(tnode, *udict['complete'])
                            user_control = True
                    elif depth_done:
                        done = True
                    else:
                        method = modelmethod(
                            'render', udict['name'], udict['modelscope'],
                            udict['noauto'],
                        )
                        if method is None:
                            done = False
                        else:
                            done = method(tnode)
                            user_control = True

                    # might have been changed in the meantime.
                    udict = tnode._udict
                    if udict['removed']:
                        next_node = True
                        break

                    elif udict['repeated'] is not None:
                        push((depth_done, _iter(repeat(
                            tnode, user_node, model, *udict['repeated']
                        )).next, None))
                        depth_done = False
                        next_node = True # Ignore original node.
                        break

                    elif user_control and 'callback' in udict:
                        continue

                    break

                if next_node:
                    continue

            if not udict['noelement'] and not udict['masked']:
                yield udict['encoder'].starttag(
                    udict['tagname'], udict['attr'].itervalues(),
                    udict['closed']
                )
                endtag = udict['endtag']
            else:
                endtag = None

            content = udict['content']
            if content[0] is not None:
                if escaped:
                    cont = content[1]
                    if cont is None:
                        cont = udict['encoder'].escape(content[0])
                    yield cont
                else:
                    yield content[0]
                if endtag:
                    yield endtag
                continue

            ctx = tnode.ctx
            nodes = [
                (subkind, subkind != TEXT
                    and user_node(subnode, model, ctx,
                                  subnode._usernode)
                    or subnode
                )
                for subkind, subnode in udict['nodes']
            ]
            push((depth_done, _iter(nodes).next, endtag))
            depth_done = done or depth_done
