# -*- coding: ascii -*-
#
# Copyright 2006 - 2012
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
================
 Model Adapters
================

Model adapter implementations.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

from tdi import ModelMissingError
from tdi import interfaces as _interfaces


class RenderAdapter(object):
    """
    Regular Render-Adapter implementation

    :See: `ModelAdapterInterface`
    """
    __implements__ = [_interfaces.ModelAdapterInterface]

    emit_escaped = False

    def __new__(cls, model, requiremethods=False):
        """
        Construct

        :Parameters:
          `model` : any
            User model

          `requiremethods` : ``bool``
            Require methods to exist?

        :Return: Render adapter
        :Rtype: `ModelAdapterInterface`
        """
        self = object.__new__(cls)

        require = bool(requiremethods)
        models = {'': model}
        def modelmethod(prefix, name, scope, noauto):
            """
            Build the method name from prefix and node name and resolve

            This implements the default look up.

            :Parameters:
              `prefix` : ``str``
                The method prefix (``render``, or ``separate``)

              `name` : ``str``
                The node name

              `scope` : ``str``
                Scope

              `noauto` : ``bool``
                No automatic method calling?

            :Return: The method or ``None``
            :Rtype: ``callable``

            :Exceptions:
              - `ModelMissingError` : The method was not found, but all
                methods are required
            """
            if name is None or noauto:
                return None
            if scope in models:
                model = models[scope]
            else:
                model = models['']
                scope_part = None
                for part in scope.split('.'):
                    if not scope_part:
                        scope_part = part
                    else:
                        scope_part = '%s.%s' % (scope_part, part)
                    if scope_part in models:
                        model = models[scope_part]
                    else:
                        model = getattr(model, 'scope_' + part, None)
                        models[scope_part] = model

            method = getattr(model, "%s_%s" % (prefix, name), None)
            if method is None and require:
                raise ModelMissingError(name)
            return method

        self.modelmethod = modelmethod
        return self

    def for_prerender(cls, model, attr=None):
        """
        Create prerender adapter from model

        :Parameters:
          `model` : any
            User model

          `attr` : ``dict``
            Attribute name mapping. The keys 'scope' and 'tdi' are recognized.
            If omitted or ``None``, the default attribute names are applied
            ('tdi:scope' and 'tdi').

        :Return: Prerender adapter
        :Rtype: `ModelAdapterInterface`
        """
        return PreRenderWrapper(cls(model), attr=attr)
    for_prerender = classmethod(for_prerender)


class PreRenderWrapper(object):
    """
    Pre-render wrapper adapter

    :See: `ModelAdapterInterface`
    """
    __implements__ = [_interfaces.ModelAdapterInterface]

    emit_escaped = True

    def __new__(cls, adapter, attr=None):
        """
        Construct

        :Parameters:
          `adapter` : `ModelAdapterInterface`
            model adapter for resolving methods

          `attr` : ``dict``
            Attribute name mapping. The keys 'scope' and 'tdi' are recognized.
            If omitted or ``None``, the default attribute names are applied
            ('tdi:scope' and 'tdi').

        :Return: Render adapter
        :Rtype: `ModelAdapterInterface`
        """
        # pylint: disable = R0912
        self = object.__new__(cls)

        scope_attr = 'tdi:scope'
        tdi_attr = 'tdi'
        if attr is not None:
            scope_attr = attr.get('scope', scope_attr)
            tdi_attr = attr.get('tdi', tdi_attr)

        omethod = adapter.modelmethod
        def modelmethod(prefix, name, scope, noauto):
            """
            Build the method name from prefix and node name and resolve

            This asks the passed adapter and if the particular method is not
            found it generates its own, which restores the tdi attributes
            (but not tdi:overlay).

            :Parameters:
              `prefix` : ``str``
                The method prefix (``render``, or ``separate``)

              `name` : ``str``
                The node name

              `scope` : ``str``
                Scope

              `noauto` : ``bool``
                No automatic method calling?

            :Return: The method
            :Rtype: ``callable``
            """
            method = omethod(prefix, name, scope, noauto)
            if method is not None:
                return method

            # These methods we only see of the model repeats a node, but
            # doesn't define a separator logic. We do not want to write out
            # the special node stuff in this case (since the separators would
            # be alone after that).
            if prefix == 'separate':
                return None

            # The node is repeated in order to get our hands on
            # a possible separator. The second iteration of the node is simply
            # removed, so we keep the node itself and its separator.

            # However, by repeating the node we override an existing context
            # of the node. So we pass it explicitly and override it again.
            def repeat(node, item, ctx):
                """ Repeater """
                if item:
                    return node.remove()
                node.ctx = ctx

            def setscope(node, scope=scope):
                """ Special attribute helper """
                node[scope_attr] = (
                    '=' + (node.hiddenelement and '-' or '+') + scope
                )

            def render(node, name=name, sep=False):
                """ Generated render method """
                try:
                    toremove = node['tdi:prerender'] == 'remove-node'
                    del node['tdi:prerender']
                except KeyError:
                    toremove = False

                setscope(node)
                if not toremove:
                    if name is not None:
                        flags = node.hiddenelement and '-' or '+'
                        if noauto:
                            flags += '*'
                        if sep:
                            flags += ':'
                        node[tdi_attr] = flags + name
                        node.hiddenelement = False

                def separate(node, ctx):
                    """ Separator """
                    node.ctx = ctx
                    return render(node, sep=True)

                node.repeat(repeat, (0, 1), node.ctx, separate=separate)

            if name is None:
                return setscope
            return render

        self.modelmethod = modelmethod
        return self


from tdi import c
c = c.load('impl')
if c is not None:
    RenderAdapter = c.RenderAdapter
del c
