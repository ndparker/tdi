# -*- coding: ascii -*-
r"""
:Copyright:

 Copyright 2014 - 2015
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
 Tests for tdi._graph
======================

Tests for tdi._graph
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

from nose.tools import assert_equals

from tdi import _graph


def test_resolve():
    """ DependencyGraph resolves properly """
    graph = _graph.DependencyGraph()
    graph.add(2, 1)
    graph.add(3, 1)
    graph.add(4, 5)
    graph.add(1, 4)
    assert_equals(graph.resolve(), [3, 2, 1, 4, 5])


def test_cycle():
    """ DependencyGraph detects cycle """
    graph = _graph.DependencyGraph()
    graph.add(2, 1)
    graph.add(3, 1)
    graph.add(1, 4)
    try:
        graph.add(4, 2)
    except _graph.DependencyCycle, e:
        assert_equals(e.args[0], [2, 1, 4])
    else:
        assert False, "Did not raise exception"
