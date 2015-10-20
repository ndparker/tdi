# -*- coding: ascii -*-
r"""
:Copyright:

 Copyright 2013 - 2015
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

===========================
 Dependency Graph Resolver
===========================

Dependency Graph Resolver.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

import collections as _collections
import operator as _op

from ._exceptions import DependencyCycle


class DependencyGraph(object):
    """
    Dependency Graph Container

    This is a simple directed acyclic graph. The graph starts empty, and new
    nodes (and edges) are added using the `add` method. If the newly added
    create a cycle, an exception is thrown.

    Finally, the graph is resolved using the `resolve` method. The method will
    return topologically ordered nodes and destroy the graph. The topological
    order is *stable*, meaning, the same graph will always produce the same
    output.

    :IVariables:
      `_outgoing` : ``defaultdict``
        Mapping of outgoing nodes (node -> set(outgoing neighbours))

      `_incoming` : ``defaultdict``
        Mapping of incoming nodes (node -> set(incoming neighbours))
    """
    __slots__ = ('_outgoing', '_incoming')

    def __init__(self):
        """ Initialization """
        self._outgoing = _collections.defaultdict(set)
        self._incoming = _collections.defaultdict(set)

    def add(self, start, end):
        """
        Add a new nodes with edge to the graph

        The edge is directed from `start` to `end`.

        :Parameters:
          `start` : ``str``
            Node

          `end` : ``str``
            Node
        """
        self._outgoing[start].add(end)
        self._incoming[end].add(start)
        self._check_cycle(end)

    def resolve(self):
        """
        Resolve graph and return nodes in topological order

        The graph is defined by outgoing and incoming dicts (mapping nodes to
        their outgoing or incoming neighbours). The graph is destroyed in the
        process.

        :Return: Sorted node list. The output is stable, because nodes on
                 the same level are sorted alphabetically. Furthermore all
                 leaf nodes are put at the end.
        :Rtype: ``list``
        """
        result, outgoing, incoming = [], self._outgoing, self._incoming
        roots = list(set(outgoing.iterkeys()) - set(incoming.iterkeys()))
        leaves = set(incoming.iterkeys()) - set(outgoing.iterkeys())

        roots.sort()  # ensure stable output
        roots = _collections.deque(roots)
        roots_push, roots_pop = roots.appendleft, roots.pop
        result_push, opop, ipop = result.append, outgoing.pop, incoming.pop
        while roots:
            node = roots_pop()
            if node not in leaves:
                result_push(node)
            children = list(opop(node, ()))
            children.sort()  # ensure stable output
            for child in children:
                parents = incoming[child]
                parents.remove(node)
                if not parents:
                    roots_push(child)
                    ipop(child)

        if outgoing or incoming:  # pragma: no cover
            raise AssertionError("Graph not resolved (this is a bug).")

        leaves = list(leaves)
        leaves.sort()  # ensure stable output
        return result + leaves

    def _check_cycle(self, node):
        """
        Find a cycle containing `node`

        This assumes, that there's no other possible cycle in the graph. This
        assumption is valid, because the graph is checked whenever a new
        edge is added.

        :Parameters:
          `node` : ``str``
            Node which may be part of a cycle.

        :Exceptions:
          - `DependencyCycle` : Raised, if there is, indeed, a cycle in the
            graph. The cycling nodes are passed as a list to the exception.
        """
        # run a DFS for each child node until we find
        # a) a leaf (then backtrack)
        # b) node (cycle)
        outgoing = self._outgoing
        if node in outgoing:
            iter_ = iter
            stack = [(node, iter_(outgoing[node]).next)]
            exhausted, push, pop = StopIteration, stack.append, stack.pop

            while stack:
                try:
                    child = stack[-1][1]()
                except exhausted:
                    pop()
                else:
                    if child == node:
                        raise DependencyCycle(map(_op.itemgetter(0), stack))
                    elif child in outgoing:
                        push((child, iter_(outgoing[child]).next))
