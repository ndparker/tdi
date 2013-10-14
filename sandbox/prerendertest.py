#!/usr/bin/env python
# -*- coding: ascii -*-
#
# Copyright 2010
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

from tdi import template as _template

template = _template.html.from_string("""
<div tdi="master">
  <ul class="subcat" tdi="categories">
    <li tdi="item"><a href="" tdi="link">Kategorie</a>
      <ul class="flyout" tdi="subcategories">
        <li tdi="item"><a href="" tdi="link">unterkategorie</a></li>
      </ul>
    </li>
  </ul>
</div>
""")

class ModelAdapter(_template.ModelAdapter):
    """ Extended model adapter """

    def model_method(self, prefix, name):
        """ Model method resolver """
        method = super(ModelAdapter, self).model_method(prefix, name)
        if method is None:
            def repeat(node, item):
                """ Repeater """
                if item:
                    node.remove()
            def render(node, prefix=prefix, name=name, repeat=repeat):
                """ Renderer """
                if not name.startswith('.'):
                    try:
                        toremove = node['tdi:prerender'] == 'remove-node'
                    except KeyError:
                        toremove = False

                    if toremove:
                        del node['tdi:prerender']
                    else:
                        if prefix == 'separate':
                            name = ':' + name
                        if node.hiddenelement:
                            name = '-' + name
                            node.hiddenelement = False
                        node['tdi'] = name
                    return node.repeat(repeat, (0, 1))
            method = render
        return method


def cat(id, name, *children):
    return dict(id=id, name=name, children=children)


class Model(object):
    def _render_item(self, node):
        pass

    def render_master(self, node):
        root_cats = [cat(1, 'foo'), cat(2, 'bar'), cat(3, 'baz')]
        for subnode, c in node.categories.item.iterate(root_cats):
            subnode.link['href'] = '/'.join(
                map(str, ('category', c['id'], c['name']))
            )
            subnode.link.content = c.get('name_short', c['name'])
            if c['children']:
                for subcat_node, subcat in subnode.subcategories.item.iterate(c['children']):
                    if subcat['id'] == c['children'][0]['id']:
                        subcat_node['class'] = 'first'
                    if subcat['id'] == c['children'][-1]['id']:
                        subcat_node['class'] = 'last'
                    subcat_node.link['href'] = self.pagedata.url('category', subcat['id'], subcat['name'])
                    subcat_node.link.content = subcat.get('name_short', subcat['name'])
            else:
                subnode.subcategories.remove()
        node.categories.item['tdi:prerender'] = 'remove-node'


template.render(Model(), adapter=ModelAdapter)
