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

================
 Model Adapters
================

Model adapter implementations.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

from ._exceptions import ModelMissingError
from . import interfaces as _interfaces


class RenderAdapter(object):
    """
    Regular Render-Adapter implementation

    :See: `ModelAdapterInterface`
    """
    __implements__ = [_interfaces.ModelAdapterInterface]

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
        self = object.__new__(cls)

        requiremethods = bool(requiremethods)
        requirescopes = bool(requirescopes)
        getattr_ = getattr
        models = {'': model}

        class unset(object):
            # pylint: disable = invalid-name,  missing-docstring
            pass
        unset = unset()

        def new(model):
            """ Create adapter for a new model """
            return cls(
                model,
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
        self.emit_escaped = False

        return self

    @classmethod
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


class PreRenderWrapper(object):
    """
    Pre-render wrapper adapter

    :See: `ModelAdapterInterface`
    """
    __implements__ = [_interfaces.ModelAdapterInterface]

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
        self.new = new
        self.emit_escaped = True

        return self


from . import c
c = c.load('impl')
if c is not None:
    RenderAdapter = c.RenderAdapter  # noqa
    PreRenderWrapper = c.PreRenderWrapper  # noqa
del c
