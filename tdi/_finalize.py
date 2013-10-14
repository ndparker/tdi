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
 Node Tree Finalization
========================

Node Tree Finalization.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

# pylint: disable = W0212 
# Access to a protected member _udict of a client class

import itertools as _it

from tdi._exceptions import NodeWarning, NodeTreeError
from tdi import _nodetree


def finalize(udict, encoder, decoder):
    """
    Finalize the tree

    This assigns separator nodes to their accompanying content nodes,
    concatenates adjacent text nodes, determines the parent->child
    relations and collects the (source) overlays.

    :Parameters:
      `udict` : ``dict``
        Root udict

      `encoder` : `EncoderInterface`
        Encoder instance

      `decoder` : `DecoderInterface`
        Decoder instance

    :Return: The collected overlays (name -> node_or_none)
    :Rtype: ``dict``

    :Exceptions:
      - `NodeTreeError` : An endtag was not set
    """
    finish_level, dispatch = _finish_level, _dispatch
    exhausted, separated = StopIteration, []
    sources, targets = {}, {}

    #       0           1           2          3          4      5
    # parent-udict, children, newchildren, separators, sepname, ns
    stack = [(udict, iter(udict['nodes']).next, [], {}, None, '')]

    while stack:
        try:
            kind, node = stack[-1][1]()
        except exhausted:
            separated.append(finish_level(stack, encoder, decoder))
        else:
            overlay = dispatch(stack, kind, node)
            if overlay is not None:
                oname, onode, otarget, osource = overlay
                if not otarget:
                    if oname in sources:
                        # later this will result in "ambiguous overlay"
                        sources[oname] = None
                    else:
                        sources[oname] = onode
                if not osource:
                    if oname not in targets:
                        targets[oname] = []
                    targets[oname].append(node)

    _optimize_separators(_it.chain(*separated))
    return sources, targets


def _dispatch(stack, kind, node):
    """
    Dispatch node where it belongs

    :Parameters:
      `stack` : ``list``
        Finalization stack

      `kind` : ``int``
        Node type

      `node` : any
        Node

    :Return: Overlay info (name, node, target_only, source_only) or ``None``
    :Rtype: ``tuple``
    """
    nodes = stack[-1][2]

    # if the new node is a text node, just append it to the list
    # or concatenate with the previous one (if that's also a text node)
    TEXT = _nodetree.TEXT_NODE
    if kind == TEXT:
        if not nodes or nodes[-1][0] != TEXT:
            nodes.append((TEXT, node))
        else:
            left = ''.join((nodes[-1][1][0], node[0]))
            right = ''.join((nodes[-1][1][1], node[1]))
            if left == right:
                right = left
            nodes[-1] = (TEXT, (left, right))
        return None

    # Otherwise we got a real node here.
    # 1) sanity check
    udict = node._udict
    if 'endtag' not in udict:
        if not udict['closed']:
            raise NodeTreeError(
                "endtag was not assigned for node %r" % (udict['name'],)
            )
        udict['endtag'] = ''

    # 2) Collect overlay info
    #
    # source overlays inside separators don't make any sense, so they are
    # ignored and warned about.
    overlay, (_, otarget, osource, oname) = None, udict['overlay']
    if oname is not None:
        if not otarget and stack[-1][4] is not None: # inside separator?
            NodeWarning.emit(
                "Ignoring source overlay %r in separator node %r" % (
                    oname, stack[-1][4],
                )
            )
        else:
            overlay = oname, node, otarget, osource

    # 3) Dispatch node
    #
    # If it's a separator node, it's set aside for later assignment to
    # its "parent".
    if kind == _nodetree.SEP_NODE:
        stack[-1][3][udict['name']] = node

    # Otherwise it's appended to the current node list and pushed onto the
    # stack, so its child nodes can be handled next. If the node comes with
    # a new scope, it's merged with the current one.
    else:
        nodes.append((kind, node))
        stack.append((
            udict, iter(udict['nodes']).next, [], {}, stack[-1][4],
            _merge_scope(stack[-1][5], udict['scope']),
        ))

    return overlay


def _finish_level(stack, encoder, decoder):
    """
    Finish a stack level after its child node iterator is exhausted

    :Parameters:
      `stack` : ``list``
        Finalization stack

      `encoder` : `EncoderInterface`
        Encoder

      `decoder` : `DecoderInterface`
        Decoder

    :Return: List of separator nodes on this level
    :Rtype: ``list``
    """
    # pylint: disable = R0912

    def check_seps(seps):
        """ Check and warn about lone separators """
        if seps:
            seps = seps.keys()
            seps.sort()
            NodeWarning.emit(
                "Ignoring separator node(s) without accompanying content "
                "node: %s" % (', '.join(map(repr, seps)),), stacklevel=5
            )

    udict, _, nodes, seps, _, scope = stack.pop()
    udict['namedict'] = {}
    udict['encoder'] = encoder
    udict['decoder'] = decoder
    udict['modelscope'] = scope
    if 'attr_' in udict:
        udict['attr'] = dict((decoder.normalize(key), (key, value))
            for key, value in udict['attr_']
        )
        del udict['attr_']

    # Fast exit: Optimize for text-only content
    if len(nodes) == 0:
        if udict['content'][0] is None:
            udict['content'] = ('', '')
        udict['nodes'] = []
        check_seps(seps)
        return ()
    elif len(nodes) == 1 and nodes[0][0] == _nodetree.TEXT_NODE:
        udict['content'] = nodes[0][1]
        udict['nodes'] = []
        check_seps(seps)
        return ()

    # Ok, this nodelist is real...
    udict['nodes'] = nodes
    udict['content'] = (None, None)

    # Now assign separator nodes (and push onto stack, so they can be
    # finalized) and collect nameless "ghost" nodes for later addition
    # to the namedict
    nameless, separated = [], []
    for idx, (kind, node) in enumerate(nodes):
        # Skip text nodes (SEP_NODE is not possible at this stage)
        if kind != _nodetree.PROC_NODE:
            continue

        # Record nameless node's namedict
        name = node._udict['name']
        if name is None:
            if udict['modelscope'] == node._udict['modelscope']:
                # negative indexes are reserved for nameless nodes
                nameless.append((-1 - idx, node._udict['namedict']))
            continue

        # Assign separator if found on this level and append to stack
        if name in seps:
            node._udict['sep'] = seps.pop(name)
        sep = node._udict['sep']
        if sep is not None:
            stack.append((
                sep._udict, iter(sep._udict['nodes']).next, [], {}, name,
                _merge_scope(node._udict['modelscope'], sep._udict['scope']),
            ))
            separated.append(sep._udict)

        # finally maintain namedict
        if udict['modelscope'] == node._udict['modelscope']:
            udict['namedict'][name] = idx

    check_seps(seps)

    # Now add nameless node's children to our namedict (if the names do not
    # exist yet)
    while nameless:
        idx, namedict = nameless.pop()
        for name in namedict.iterkeys():
            udict['namedict'].setdefault(name, idx)

    return separated


def _merge_scope(current, new):
    """
    Merge current and new scope

    :Parameters:
      `current` : ``str``
        Current scope

      `new` : ``tuple``
        New scope info

    :Return: final scope
    :Rtype: ``str``
    """
    if new[2] is None:
        return current
    elif new[1] or not current:
        return new[2]
    return '%s.%s' % (current, new[2])


def _optimize_separators(separated):
    """
    Optimize separator nodes

    If the nodes are simple (just unmodifiable content), the result is
    already "pre"-rendered. This will be used if there's no separator
    callback.

    :Parameters:
      `separated` : iterable
        Separator node udicts
    """
    for udict in separated:
        if udict['content'][0] is None:
            udict['complete'] = (None, None)
        elif udict['noelement']:
            udict['complete'] = udict['content']
        else:
            left = "%s%s%s" % (
                udict['encoder'].starttag(
                    udict['tagname'],
                    udict['attr'].itervalues(),
                    udict['closed'],
                ),
                udict['content'][0],
                udict['endtag'],
            )
            right = "%s%s%s" % (
                udict['encoder'].starttag(
                    udict['tagname'],
                    udict['attr'].itervalues(),
                    udict['closed'],
                ),
                udict['content'][1],
                udict['endtag'],
            )
            if left == right:
                right = left
            udict['complete'] = (left, right)
