# -*- coding: ascii -*-
u"""
:Copyright:

 Copyright 2006 - 2014
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

    def __new__(cls, model, requiremethods=False, requirescopes=False):
        """
        Construct

        :Parameters:
          `model` : any
            User model

          `requiremethods` : ``bool``
            Require methods to exist?

          `requirescopes` : ``bool``
            Require scopes to exist?

        :Return: Render adapter
        :Rtype: `ModelAdapterInterface`
        """
        # pylint: disable = R0912
        # (too many branches)

        self = object.__new__(cls)

        requiremethods = bool(requiremethods)
        requirescopes = bool(requirescopes)
        getattr_ = getattr
        models = {'': model}

        class unset(object): # pylint: disable = C0103, C0111
            pass
        unset = unset()

        def new(model):
            """ Create adapter for a new model """
            return cls(model,
                requiremethods=requiremethods,
                requirescopes=requirescopes,
            )

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
                        model = getattr_(model, 'scope_' + part, unset)
                        if model is unset:
                            if requirescopes:
                                raise ModelMissingError(scope_part)
                            model = None
                        models[scope_part] = model

            method = getattr_(model, "%s_%s" % (prefix, name), unset)
            if method is unset:
                if requiremethods:
                    raise ModelMissingError("%s_%s" % (prefix, name))
                method = None
            return method

        self.modelmethod = modelmethod
        self.new = new
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
            attr = dict(tdi=tdi_attr, scope=scope_attr)

        def new(model):
            """ Create adapter for a new model """
            return cls(adapter.new(model), attr=attr)

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

            :Return: The method or ``None``
            :Rtype: ``callable``
            """
            try:
                method = adapter.modelmethod(prefix, name, scope, noauto)
            except ModelMissingError:
                pass
            else:
                if method is not None:
                    return method

            # These methods we only see of the model repeats a node, but
            # doesn't define a separator logic. We do not want to write out
            # the special node stuff in this case (since the separators would
            # be alone after that).
            if prefix == 'separate':
                return None

            return _PrerenderMethod(name, scope, noauto, tdi_attr, scope_attr)

        self.modelmethod = modelmethod
        self.new = new

        return self


class _PrerenderMethod(object):
    """ Prerender method """

    def __init__(self, name, scope, noauto, tdi_attr, scope_attr):
        """ Initialization """
        self._name = name
        self._scope = scope
        self._noauto = noauto
        self._tdi_attr = tdi_attr
        self._scope_attr = scope_attr

    def _repeat(self, node, item, ctx):
        """
        Repeater

        The node is repeated in order to get our hands on
        a possible separator. The second iteration of the node is simply
        removed, so we keep the node itself and its separator.

        However, by repeating the node we override an existing context
        of the node. So we pass it explicitly and override it again.
        """
        if item:
            return node.remove()
        node.ctx = ctx

    def _separate(self, node, ctx):
        """
        Separator

        :See: `_repeat`
        """
        node.ctx = ctx
        return self._render(node, sep=True)

    def _setscope(self, node):
        """ Set scope to current """
        node[self._scope_attr] = (
            '=' + (node.hiddenelement and '-' or '+') + self._scope
        )

    def _render(self, node, sep=False):
        """ Render the node (by restoring its tdi attributes) """
        try:
            toremove = node['tdi:prerender'] == 'remove-node'
            del node['tdi:prerender']
        except KeyError:
            toremove = False

        self._setscope(node)
        if not toremove:
            if self._name is not None:
                flags = node.hiddenelement and '-' or '+'
                if self._noauto:
                    flags += '*'
                if sep:
                    flags += ':'
                node[self._tdi_attr] = flags + self._name
                node.hiddenelement = False

        node.repeat(self._repeat, (0, 1), node.ctx, separate=self._separate)

    def __call__(self, node):
        """ Actual generated render method """
        if self._name is None:
            self._setscope(node)
        else:
            self._render(node)


from tdi import c
c = c.load('impl')
if c is not None:
    RenderAdapter = c.RenderAdapter
del c
