# -*- coding: ascii -*-
#
# Copyright 2007 - 2012
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
=====================
 HTML forms reloaded
=====================

Form helper classes.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"
__all__ = ['normalize_newlines', 'normalize_whitespaces', 'HTMLForm']

import re as _re

from tdi.tools.htmlform._adapters import NullParameterAdapter
from tdi.tools.htmlform._input_field_generator import make_input


def normalize_newlines():
    """ Make newline normalizer """
    SUB_U = _re.compile(ur'\r?\n|\r').sub
    SUB_S = _re.compile(r'\r?\n|\r').sub
    def normalize_newlines(value): # pylint: disable = W0621
        """
        Normalize the newlines of a string

        All newlines are converted to \\n.

        :Parameters:
          `value` : ``basestring``
            The text to normalize

        :Return: The normalized value, the type depends on the input type
        :Rtype: ``basestring``
        """
        if isinstance(value, unicode):
            subber, repl = SUB_U, u"\n"
        else:
            subber, repl = SUB_S, "\n"
        return subber(repl, value)
    return normalize_newlines
normalize_newlines = normalize_newlines()


def normalize_whitespaces():
    """ Make whitespace normalizer """
    SUB_U = _re.compile(ur'\s').sub
    SUB_S = _re.compile(r'\s').sub
    def normalize_whitespaces(value): # pylint: disable = W0621
        """
        Normalize the whitespaces of a string

        All whitespaces are converted to regular space.

        :Parameters:
          `value` : ``basestring``
            The text to normalize

        :Return: The normalized value, the type depends on the input type
        :Rtype: ``basestring``
        """
        if isinstance(value, unicode):
            subber, repl = SUB_U, u" "
        else:
            subber, repl = SUB_S, " "
        return subber(repl, value)
    return normalize_whitespaces
normalize_whitespaces = normalize_whitespaces()


class HTMLForm(object):
    """
    HTML form helper class

    :IVariables:
      `_action` : ``basestring``
        form action

      `_method` : ``basestring``
        form method

      `_param` : `ParameterAdapterInterface`
        Parameter adapter

      `_upload` : ``bool``
        Upload form?

      `_charset` : ``basestring``
        Accepted character set for submission

      `_xhtml` : ``bool``
        Use XHTML attributes (vs. short attributes)?

      `_pre_proc` : `PreProcInterface`
        Pre set node processing callable

      `_post_proc` : `PostProcInterface`
        Post set node processing callable
    """
    # pylint: disable = R0912, R0913

    def __init__(self, action=None, method='get', param=None, upload=False,
                 accept_charset='utf-8', xhtml=True, pre_proc=None,
                 post_proc=None):
        """
        Initialization

        If you set `upload` to ``True``, the method will be ignored and
        be set to ``post`` automatically.

        :Parameters:
          `action` : ``basestring``
            Form action URL

          `method` : ``basestring``
            form submission method

          `param` : `ParameterAdapterInterface`
            Parameter adapter. If unset or ``None``, no values
            will be taken out of the request. This is useful for initial
            requests showing empty forms as there will be no special handling
            required for this case.

          `upload` : ``bool``
            Is this an upload form?

          `accept_charset` : ``basestring``
            Accepted charset(s) for submission, if there are multiple charsets
            given, they have to be unique and space separated.

          `xhtml` : ``bool``
            Use XHTML attributes (vs. short attributes)?

          `pre_proc` : `PreProcInterface`
            Pre set node processing callable

          `post_proc` : `PostProcInterface`
            Post set node processing callable
        """
        # pylint: disable = R0913
        self._action = action
        self._method = upload and 'post' or method
        if param is None:
            param = NullParameterAdapter()
        self._param = param
        self._upload = upload
        self._charset = accept_charset
        self._xhtml = bool(xhtml)
        if pre_proc is None:
            pre_proc_ = None
        else:
            def pre_proc_(method, node, *args):
                """ Pre proc wrapper """
                node, kwargs = pre_proc(method, node, dict(args))
                return (node,) + tuple([kwargs.get(key, val)
                    for key, val in args])
        self._pre_proc = pre_proc_
        self._post_proc = post_proc

    def param(self):
        """ Parameter adapter getter """
        return self._param
    param = property(param, doc="Parameter adapter the form is using")

    def is_xhtml(self):
        """ XHTML flag getter """
        return self._xhtml
    is_xhtml = property(is_xhtml, doc="XHTML flag setting of the form")

    def is_upload(self):
        """ Upload flag getter """
        return self._upload
    is_upload = property(is_upload, doc="Upload flag setting of the form")

    def accept_charset(self):
        """ Accept-charset getter """
        return self._charset
    accept_charset = property(accept_charset,
        doc="Accepted charset of the form"
    )

    def action(self):
        """ Form action getter """
        return self._action
    action = property(action, doc="Configured form action")

    def method(self):
        """ Form method getter """
        return self._method
    method = property(method, doc="Configured form method")

    normalize_newlines = staticmethod(normalize_newlines)
    normalize_whitespaces = staticmethod(normalize_whitespaces)

    def form(self, node, hidden=None, hidden_="hidden", autocomplete=None,
             novalidate=None, raw=False):
        """
        Fill in the form starttag

        The following attributes are possibly set:
        - ``action`` (only if it's not ``None``)
        - ``method``
        - ``accept-charset`` (only if it's not ``None``)
        - ``enctype`` (only on upload forms)
        - ``autocomplete``
        - ``novalidate``

        Rendering hidden fields
        ~~~~~~~~~~~~~~~~~~~~~~~

        You can use this method to set a list of hidden fields at once.
        It iterates over `hidden` and multiplies the node named by `hidden_`
        accordingly.

        The `hidden` iterable contains tuples of variable length, namely
        from 1 to 3, like::

          [
              ('foo', 'bar'),
              ('zonk', '"plop"', True),
              ('x',),
          ]

        If `hidden` is empty, the hidden node will be deleted.

        Field item tuples
        -----------------

        The first (and maybe only) item is the name of the field. This
        is always set unconditionally.

        The second item is the value of the field. If the field does not
        have a value at all - the second and third items are left out,
        leaving the name only.
        If the value is ``None`` it's taken out of the request and filled
        into the field. The third parameter is ignored in this case. If the
        name does not appear in the request, the field is skipped (not
        rendered). If the request contains more than one value under
        that name, a hidden field is generated for each of them.
        In all other cases the value is written into the ``value`` attribute.

        The third item determines whether the value should be treated
        as raw or not. If it's unset, the `raw` parameter of the method
        applies.

        :Parameters:
          `node` : `tdi.nodetree.Node`
            The ``<form>`` node

          `hidden` : iterable
            Hidden fields to set. If unset or ``None``, no hidden
            fields are touched. If it's an empty list, the hidden node is
            removed.

          `hidden_` : ``basestring``
            Name of the hidden field node, relative to the form
            `node` (dotted notation)

          `autocomplete` : ``bool``
            Set the default autocomplete state of the form (HTML5). If omitted
            or ``None``, any autocomplete attribute present won't be touched.

          `novalidate` : ``bool``
            Set the default novalidate attribute of the form (HTML5). If
            omitted or ``None``, any novalidate attribute present won't be
            touched.

          `raw` : ``bool``
            Default "rawness" value for the hidden field list
        """
        # pylint: disable = R0912
        pre_proc = self._pre_proc
        if pre_proc is not None:
            node, hidden, hidden_, raw = pre_proc('form', node,
                ('hidden', hidden), ('hidden_', hidden_), ('raw', raw),
            )

        if self._action is not None:
            node[u'action'] = self._action
        node[u'method'] = self._method
        if self._charset is not None:
            node[u'accept-charset'] = self._charset
        if autocomplete is not None:
            node[u'autocomplete'] = autocomplete and u'on' or u'off'
        if self._upload:
            node[u'enctype'] = u'multipart/form-data'
        if novalidate is not None:
            if novalidate:
                node[u'novalidate'] = self._xhtml and u'novalidate' or None
            else:
                del node[u'novalidate']

        post_proc = self._post_proc
        if post_proc is not None:
            post_proc('form', node, dict(
                hidden=hidden, hidden_=hidden_, raw=raw
            ))

        if hidden is not None:
            partnodes = hidden_.split('.')
            partnodes.reverse()
            hiddennode = node(partnodes.pop())
            while partnodes:
                hiddennode = hiddennode(partnodes.pop())

            # hidden fields
            param = self._param
            filtered = []
            for field in hidden:
                name, value, thisraw = field[0], field[1:2], field[2:3]
                if value:
                    value = value[0]
                    if value is None:
                        rval = param.getlist(name)
                        filtered.extend([(name, val, False) for val in rval])
                    else:
                        filtered.append((name, value, (thisraw or [raw])[0]))
                else:
                    filtered.append((name, None, None))
            for subnode, param in hiddennode.iterate(filtered):
                self.hidden(subnode, *param)

    def hidden(self, node, name, value=None, raw=False):
        """
        Render a hidden field

        Hidden field values are never taken out of the request. The reason for
        that seemingly inconsistent behaviour is that hidden fields have no
        assigned semantics. In other words, the method can't know, *how* to
        correctly retrieve the value out of the request.

        :Parameters:
          `node` : `tdi.nodetree.Node`
            The hidden field node

          `name` : ``basestring``
            Name of the hidden field

          `value` : ``basestring``
            Optional value of the hidden field - if omitted or
            ``None``, the value attribute is completey removed

          `raw` : ``bool``
            Is `value` raw (not to be escaped)
        """
        pre_proc = self._pre_proc
        if pre_proc is not None:
            node, name, value, raw = pre_proc('hidden', node,
                ('name', name), ('value', value), ('raw', raw),
            )

        node[u'type'] = u'hidden'
        node[u'name'] = name
        if value is None:
            del node[u'value']
        elif raw:
            node.raw[u'value'] = value
        else:
            node[u'value'] = value

        post_proc = self._post_proc
        if post_proc is not None:
            post_proc('hidden', node, dict(name=name, value=value, raw=raw))

    text = make_input('text', '',
        'name', 'value', 'maxlength', 'readonly', 'disabled', 'required',
        'autocomplete', 'placeholder', 'list', 'pattern', 'dirname',
        'autofocus', 'raw',
    )
    search = make_input('search', '(HTML5)',
        'name', 'value', 'maxlength', 'readonly', 'disabled', 'required',
        'autocomplete', 'placeholder', 'list', 'pattern',
        'dirname', 'autofocus', 'raw',
    )
    tel = make_input('tel', '(HTML5)',
        'name', 'value', 'maxlength', 'readonly', 'disabled', 'required',
        'autocomplete', 'placeholder', 'list', 'pattern', 'autofocus', 'raw',
    )
    url = make_input('url', '(HTML5)',
        'name', 'value', 'maxlength', 'readonly', 'disabled', 'required',
        'autocomplete', 'placeholder', 'list', 'pattern', 'autofocus', 'raw',
    )
    email = make_input('email', '(HTML5)',
        'name', 'value', 'maxlength', 'readonly', 'disabled', 'required',
        'autocomplete', 'placeholder', 'list', 'pattern',
        'multiple', 'autofocus', 'raw',
    )
    password = make_input('password', '',
        'name', 'maxlength', 'readonly', 'disabled', 'required',
        'autocomplete', 'placeholder', 'pattern', 'autofocus',
    )
    datetime = make_input('datetime', '(HTML5)\n\n    '
        '(e.g. ``1979-10-14T12:00:00.001-04:00``)',
        'name', 'value', 'readonly', 'disabled', 'required', 'autocomplete',
        'list', 'max', 'min', 'step', 'autofocus', 'raw',
    )
    date = make_input('date', '(HTML5)\n\n    (e.g. ``1979-10-14``)',
        'name', 'value', 'readonly', 'disabled', 'required', 'autocomplete',
        'list', 'max', 'min', 'step', 'autofocus', 'raw',
    )
    month = make_input('month', '(HTML5)\n\n    (e.g. ``1979-10``)',
        'name', 'value', 'readonly', 'disabled', 'required', 'autocomplete',
        'list', 'max', 'min', 'step', 'autofocus', 'raw',
    )
    week = make_input('week', '(HTML5)\n\n    (e.g. ``1979-W42``)',
        'name', 'value', 'readonly', 'disabled', 'required', 'autocomplete',
        'list', 'max', 'min', 'step', 'autofocus', 'raw',
    )
    time = make_input('time', '(HTML5)\n\n    (e.g. ``12:00:00.001``)',
        'name', 'value', 'readonly', 'disabled', 'required', 'autocomplete',
        'list', 'max', 'min', 'step', 'autofocus', 'raw',
    )
    datetime_local = make_input('datetime-local', '(HTML5)\n\n    '
        '(e.g. ``1979-10-14T12:00:00.001``)',
        'name', 'value', 'readonly', 'disabled', 'required', 'autocomplete',
        'list', 'max', 'min', 'step', 'autofocus', 'raw',
    )
    number = make_input('number', '(HTML5)',
        'name', 'value', 'readonly', 'disabled', 'required', 'autocomplete',
        'placeholder', 'list', 'max', 'min', 'step', 'autofocus', 'raw',
    )
    range = make_input('range', '(HTML5)',
        'name', 'value', 'disabled', 'autocomplete', 'list', 'max',
        'autofocus', 'min', 'step', 'raw',
    )
    color = make_input('color', '(HTML5)\n\n    (e.g. ``#D4D0C8``)',
        'name', 'value', 'disabled', 'autocomplete', 'list', 'raw',
        'autofocus',
    )
    checkbox = make_input('checkbox', '',
        'name', 'value', 'disabled', 'required', 'selected', 'autofocus',
        value_default=u'1', multi_selected=True,
    )
    radio = make_input('radio', '',
        'name', 'value', 'disabled', 'required', 'selected', 'autofocus',
        value_default=None, multi_selected=False,
    )
    file = make_input('file', '',
        'name', 'accept', 'disabled', 'required', 'multiple', 'autofocus',
        assert_upload=True,
    )
    submit = make_input('submit', '',
        'name', 'value', 'disabled', 'action', 'enctype', 'method',
        'novalidate', 'target', 'autofocus',
        simple_value=True, name_optional=True,
    )
    image = make_input('image', '',
        'name', 'disabled', 'alt', 'src', 'width', 'height', 'action',
        'enctype', 'method', 'novalidate', 'target', 'autofocus',
        name_optional=True,
    )
    reset = make_input('reset', '',
        'value', 'disabled', 'autofocus',
        simple_value=True,
    )
    button = make_input('button', '',
        'name', 'value', 'disabled', 'autofocus',
        simple_value=True, name_optional=True,
    )

    def textarea(self, node, name, value=None, maxlength=None, readonly=None,
                 disabled=None, required=None, placeholder=None, dirname=None,
                 autofocus=None, raw=False):
        """
        Render a 'textarea' input control

        :Parameters:
          `node` : `tdi.nodetree.Node`
            The 'textarea' node

          `name` : ``basestring``
            The name of the 'textarea' field

          `value` : ``basestring``
            Optional value. If ``None``, it's taken out of the request. If
            it does not appear in the request, it's treated like an empty
            string. The `raw` parameter is ignored in this case.

          `maxlength` : ``int``
            Maximum length. If omitted or ``None``, the attribute is
            *deleted*.

          `readonly` : ``bool``
            Readonly field? If unset or ``None``, the attribute is left
            untouched.

          `disabled` : ``bool``
            Disabled field? If unset or ``None``, the attribute is left
            untouched.

          `required` : ``bool``
            Required field? (HTML5). If omitted or ``None``, the attribute
            is left untouched.

          `placeholder` : ``basestring``
            Placeholder value (HTML5). If omitted or ``None``, the
            attribute is left untouched.

          `dirname` : ``basestring``
            Direction submission name (HTML5). If omitted or ``None``, the
            attribute is left untouched.

          `autofocus` : ``bool``
            Set autofocus? (HTML5). If omitted or ``None``, the attribute
            is left untouched.

          `raw` : ``bool``
            Is the value to be treated raw?
        """
        pre_proc = self._pre_proc
        if pre_proc is not None:
            (
                node, name, value, maxlength, readonly, disabled,
                required, placeholder, dirname, autofocus, raw
            ) = pre_proc('textarea', node,
                ('name', name), ('value', value), ('maxlength',
                maxlength), ('readonly', readonly), ('disabled',
                disabled), ('required', required), ('placeholder',
                placeholder), ('dirname', dirname), ('autofocus',
                autofocus), ('raw', raw)
            )

        if name is not None:
            node[u'name'] = name
        if readonly is not None:
            if readonly:
                node[u'readonly'] = self._xhtml and u'readonly' or None
            else:
                del node[u'readonly']
        if disabled is not None:
            if disabled:
                node[u'disabled'] = self._xhtml and u'disabled' or None
            else:
                del node[u'disabled']
        if required is not None:
            if required:
                node[u'required'] = self._xhtml and u'required' or None
            else:
                del node[u'required']
        if autofocus is not None:
            if autofocus:
                node[u'autofocus'] = self._xhtml and u'autofocus' or None
            else:
                del node[u'autofocus']
        if placeholder is not None:
            node[u'placeholder'] = placeholder
        if dirname is not None:
            node[u'dirname'] = dirname
        if value is None:
            value, raw = self._param.getfirst(name, u''), False
        if not raw:
            value = self.normalize_newlines(value).rstrip()
        if maxlength is not None:
            value = value[:int(maxlength)]
            node[u'maxlength'] = unicode(maxlength)
        else:
            del node[u'maxlength']
        if raw:
            node.raw.content = value
        else:
            node.content = value

        post_proc = self._post_proc
        if post_proc is not None:
            post_proc('textarea', node, dict(
                name=name, value=value, maxlength=maxlength,
                readonly=readonly, disabled=disabled, required=required,
                placeholder=placeholder, dirname=dirname,
                autofocus=autofocus, raw=raw
            ))

    def select(self, node, name, options=None, selected=None, option="option",
               disabled=None, required=None, autofocus=None, multiple=False):
        r"""
        Render a 'select' input control

        This method actually renders two nodes, namely the ``select``
        element and the ``option`` element::

            <select tdi="node">
                 <option tdi="*option">foo</option>
            </select>

        The option node is repeated as necessary (matching the entries of
        the `options` parameter). If `options` is empty, the whole ``select``
        node is emptied. The option is usually flagged with an asterisk, so
        it doesn't trigger an automatic render-method call.

        :Parameters:
          `node` : `tdi.nodetree.Node`
            The 'select' input node

          `name` : ``basestring``
            The name of the 'select' field

          `options` : iterable
            The list of option values. Each item is expected to
            be a 2-tuple of the option value and its description. The value
            is what's put into the option's ``value`` attribute and submitted
            by the browser if the option is selected. The description is the
            visible part of the option. If the value is ``None``, it's treated
            unset and the description is submitted as selected value instead.
            If `options` is ``None``, only the ``select`` element will be
            touched.

          `selected` : ``basestring`` or iterable
            The pre-selected value. If it's unset or ``None``, it's
            taken out of the request. If it does not appear in the request,
            there just won't be any pre-selected option. If `multiple` is
            true, `selected` is expected to be an *iterable* of
            ``basestring``\s.

          `option` : ``str``
            The node of the ``option`` node, relative to the
            ``select`` node. The parameter is expected in dotted notation.

          `disabled` : ``bool``
            Disabled field? If unset or ``None``, the attribute is left
            untouched.

          `required` : ``bool``
            Required field? (HTML5). If omitted or ``None``, the attribute
            is left untouched.

          `autofocus` : ``bool``
            Set autofocus? (HTML5). If omitted or ``None``, the attribute
            is left untouched.

          `multiple` : ``bool``
            Is it a multiselect box? `selected` is expected to
            be an ``iterable`` containing multiple selected values in this
            case.
        """
        # pylint: disable = R0914
        # (too many local variables. well.)

        pre_proc = self._pre_proc
        if pre_proc is not None:
            (
                node, name, options, selected, option, disabled,
                required, autofocus, multiple
            ) = pre_proc('select', node,
                ('name', name), ('options', options), ('selected',
                selected), ('option', option), ('disabled',
                disabled), ('required', required), ('autofocus',
                autofocus), ('multiple', multiple)
            )

        if name is not None:
            node[u'name'] = name
        if disabled is not None:
            if disabled:
                node[u'disabled'] = self._xhtml and u'disabled' or None
            else:
                del node[u'disabled']
        if required is not None:
            if required:
                node[u'required'] = self._xhtml and u'required' or None
            else:
                del node[u'required']
        if autofocus is not None:
            if autofocus:
                node[u'autofocus'] = self._xhtml and u'autofocus' or None
            else:
                del node[u'autofocus']

        if options is not None:
            options = list(options)
            partnodes = option.split('.')
            partnodes.reverse()
            optnode = node(partnodes.pop())
            while partnodes:
                optnode = optnode(partnodes.pop())
        if multiple:
            node[u'multiple'] = self._xhtml and u'multiple' or None
            if options is not None:
                if selected is None:
                    selected = self._param.getlist(name)
                selected_ = dict([(item, None) for item in selected])
        else:
            del node[u'multiple'] # just in case
            if options is not None:
                if selected is None:
                    selected = self._param.getfirst(name)
                selected_ = {selected: None}

        post_proc = self._post_proc
        if post_proc is not None:
            post_proc('select', node, dict(
                name=name, options=options, selected=selected,
                option=option, disabled=disabled, required=required,
                autofocus=autofocus, multiple=multiple
            ))

        if options is not None:
            for subnode, tup in optnode.iterate(options):
                value, desc, disabled = tup[0], tup[1], tup[2:]
                if value is not None:
                    is_selected = unicode(value) in selected_
                else:
                    is_selected = unicode(desc) in selected_
                self.option(subnode, value,
                    description=desc,
                    selected=is_selected,
                    disabled=disabled and disabled[0] or None,
                )

    def multiselect(self, node, name, options=None, selected=None,
                    option="option", disabled=None, required=None,
                    autofocus=None):
        """
        :Deprecated: Use ``select`` with a true ``multiple`` argument instead.
        """
        pre_proc = self._pre_proc
        if pre_proc is not None:
            (
                node, name, options, selected, option, disabled,
                required, autofocus
            ) = pre_proc('multiselect', node,
                ('name', name), ('options', options), ('selected',
                selected), ('option', option), ('disabled',
                disabled), ('required', required), ('autofocus',
                autofocus)
            )

        if name is not None:
            node[u'name'] = name
        if disabled is not None:
            if disabled:
                node[u'disabled'] = self._xhtml and u'disabled' or None
            else:
                del node[u'disabled']
        if required is not None:
            if required:
                node[u'required'] = self._xhtml and u'required' or None
            else:
                del node[u'required']
        if autofocus is not None:
            if autofocus:
                node[u'autofocus'] = self._xhtml and u'autofocus' or None
            else:
                del node[u'autofocus']

        if options is not None:
            options = list(options)
            partnodes = option.split('.')
            partnodes.reverse()
            optnode = node(partnodes.pop())
            while partnodes:
                optnode = optnode(partnodes.pop())
        node[u'multiple'] = self._xhtml and u'multiple' or None
        if options is not None:
            if selected is None:
                selected = self._param.getlist(name)
            selected_ = dict([(item, None) for item in selected])

        post_proc = self._post_proc
        if post_proc is not None:
            post_proc('multiselect', node, dict(
                name=name, options=options, selected=selected,
                option=option, disabled=disabled, required=required,
                autofocus=autofocus
            ))

        if options is not None:
            for subnode, tup in optnode.iterate(options):
                value, desc, disabled = tup[0], tup[1], tup[2:]
                if value is not None:
                    is_selected = unicode(value) in selected_
                else:
                    is_selected = unicode(desc) in selected_
                self.option(subnode, value,
                    description=desc,
                    selected=is_selected,
                    disabled=disabled and disabled[0] or None,
                )

    def datalist(self, node, id=None, options=None, option="option"):
        """
        Render a 'datalist' element (especially its options)

        This method actually renders two nodes, namely the ``datalist``
        element and the ``option`` element::

            <datalist tdi="node">
                 <option tdi="*option" />
            </datalist>

        The option node is repeated as necessary (matching the entries of
        the `options` parameter). If `options` is empty, the whole
        ``datalist`` node is emptied. The option is usually flagged with an
        asterisk, so it doesn't trigger an automatic render-method call.

        :Parameters:
          `node` : `tdi.nodetree.Node`
            The 'datalist' node

          `id` : ``basestring``
            The ``id`` attribute of the 'datalist' field. If omitted or
            ``None``, the attribute is left untouched.

          `options` : iterable
            The list of option values. Each item is expected to
            be a 2-tuple of the option value and its description. The value
            is what's put into the option's ``value`` attribute. The
            description is the visible part of the option and put into the
            'label' attribute. If the value is ``None``, it's treated as
            unset. If `options` is ``None``, only the ``datalist`` element
            will be touched.

          `option` : ``str``
            The node of the ``option`` node, relative to the
            ``select`` node. The parameter is expected in dotted notation.
        """
        # pylint: disable = C0103, W0622

        pre_proc = self._pre_proc
        if pre_proc is not None:
            (
                node, id, options, option
            ) = pre_proc('datalist', node,
                ('id', id), ('options', options), ('option', option)
            )

        if id is not None:
            node[u'id'] = id

        if options is not None:
            options = list(options)
            partnodes = option.split('.')
            partnodes.reverse()
            optnode = node(partnodes.pop())
            while partnodes:
                optnode = optnode(partnodes.pop())

        post_proc = self._post_proc
        if post_proc is not None:
            post_proc('datalist', node, dict(
                id=id, options=options, option=option
            ))

        if options is not None:
            for subnode, tup in optnode.iterate(options):
                value, desc, disabled = tup[0], tup[1], tup[2:]
                self.option(subnode, value,
                    label=desc,
                    disabled=disabled and disabled[0] or None
                )

    def option(self, node, value, description=None, selected=None,
               disabled=None, label=None):
        """
        Render a single option

        :Parameters:
          `node` : `tdi.nodetree.Node`
            The option node

          `value` : ``basestring``
            The option value, if ``None``, the attribute will be
            removed.

          `description` : ``basestring``
            The visible part of the option. If omitted or ``None``, the
            element's content is left untouched.

          `selected` : ``bool``
            Is the option selected? If unset or ``None`` the
            attribute will be left untouched.

          `disabled` : ``bool``
            Is this option disabled? If unset or ``None``, the
            attribute will be left untouched.

          `label` : ``basestring``
            Label attribute (HTML5). If omitted or ``None``, any existing
            attribute is deleted.
        """
        pre_proc = self._pre_proc
        if pre_proc is not None:
            (
                node, value, description, selected, disabled, label
            ) = pre_proc('option', node,
                ('value', value), ('description', description),
                ('selected', selected), ('disabled', disabled), ('label',
                label)
            )

        if value is None:
            del node[u'value']
        else:
            node[u'value'] = value
        if label is None:
            del node[u'label']
        else:
            node[u'label'] = label
        if selected is not None:
            if selected:
                node[u'selected'] = self._xhtml and u'selected' or None
            else:
                del node[u'selected']
        if disabled is not None:
            if disabled:
                node[u'disabled'] = self._xhtml and u'disabled' or None
            else:
                del node[u'disabled']
        if description is not None:
            node.content = description

        post_proc = self._post_proc
        if post_proc is not None:
            post_proc('option', node, dict(
                value=value, description=description, selected=selected,
                disabled=disabled, label=label,
            ))

    def keygen(self, node, name, keytype=None, challenge=None, disabled=None,
               autofocus=None):
        """
        Render a 'keygen' input control

        :Parameters:
          `node` : `tdi.nodetree.Node`
            The 'keygen' node

          `name` : ``basestring``
            The name of the 'keygen' field

          `keytype` : ``basestring``
            Optional keytype. If omitted or ``None``, the attribute is left
            untouched.

          `challenge` : ``basestring``
            Optional challenge value. If omitted or ``None``, the attribute is
            left untouched.

          `disabled` : ``bool``
            Disabled field? If unset or ``None``, the attribute is left
            untouched.

          `autofocus` : ``bool``
            Set autofocus? (HTML5). If omitted or ``None``, the attribute
            is left untouched.
        """
        pre_proc = self._pre_proc
        if pre_proc is not None:
            (
                node, name, keytype, challenge, disabled, autofocus
            ) = pre_proc('keygen', node,
                ('name', name), ('keytype', keytype), ('challenge',
                challenge), ('disabled', disabled), ('autofocus',
                autofocus)
            )

        if name is not None:
            node[u'name'] = name
        if disabled is not None:
            if disabled:
                node[u'disabled'] = self._xhtml and u'disabled' or None
            else:
                del node[u'disabled']
        if autofocus is not None:
            if autofocus:
                node[u'autofocus'] = self._xhtml and u'autofocus' or None
            else:
                del node[u'autofocus']
        if keytype is not None:
            node[u'keytype'] = keytype
        if challenge is not None:
            node[u'challenge'] = challenge

        post_proc = self._post_proc
        if post_proc is not None:
            post_proc('keygen', node, dict(
                name=name, keytype=keytype, challenge=challenge,
                disabled=disabled, autofocus=autofocus
            ))
