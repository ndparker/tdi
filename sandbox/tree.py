#!/usr/bin/env python
# -*- coding: ascii -*-
#
# Copyright 2007, 2008, 2009, 2010
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

from tdi import html

template = html.Template.fromstring("""
<ul tdi="nested">
<li tdi="outer">
    <span tdi="-text">p1</span>
    <span tdi="-inner"></span>
</li><li tdi=":-outer">
</li>
</ul>
""")

class Model(object):
    def __init__(self, tree):
        self.tree = tree

    def render_nested(self, node):
        self.nest = node.copy()
        # ctx is inherited by the children
        node.ctx = (0, [0] + self.tree, ())

    def render_outer(self, node):
        def repeater(node, item, nest):
            this, children = item[0], item[1:]
            node.text.content = str(this)
            node['style'] = 'font-size: %spx;' % (this * 4)
            if children:
                node.inner.replace(None, nest, children)
            else:
                node.inner.remove()
        return node.repeat(repeater, node.ctx[1][1:], self.nest)


tree = [
    [1,
        [2],
        [3,
            [4, [5]],
            [6],
            [7],
        ],
    ],
    [8],
    [9,
        [10,
            [11],
        ],
        [12],
    ],
]
class Null(object):
    def write(self, str):
        pass

m = Model(tree)
s = Null()
#for x in xrange(1000):
#    template.render(m, s)
template.render(m)
