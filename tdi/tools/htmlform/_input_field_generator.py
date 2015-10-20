# -*- coding: ascii -*-
r"""
:Copyright:

 Copyright 2007 - 2015
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

=======================
 Input field generator
=======================

Generate input field functions.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

import textwrap as _textwrap


def make_input(type_, doc_extra, *keywords, **kwargs):
    """ Make <input> control method """
    # pylint: disable = too-many-branches
    # pylint: disable = bad-continuation

    type_id = type_.replace('-', '_')
    keywords = dict([(word, True) for word in keywords])
    if kwargs.get('assert_upload'):
        doc_extra += ('\n\n'
            # noqa
            r'''    :Note: This is only possible if the class '''
                r'''was initialized''' '\n'
            r'''           with ``upload=True``.'''
        )
    if doc_extra and not doc_extra.startswith('\n'):
        doc_extra = ' ' + doc_extra
    if kwargs.get('simple_value'):
        valdoc = (
            '''The value of the control. If unset or ``None``, '''
            '''it's left untouched'''
        )
    else:
        value_extra = 'raw' in keywords and \
            ''' The `raw` parameter is ignored in this case.''' or ''
        valdoc = (
            '''Optional value. If ``None``, it's taken out of the '''
            '''request. If it does not appear in the request, it's '''
            '''treated like an empty string.''' + value_extra
        )
    candidates = [
        ('name', '``basestring``',
            '''The name of the %s field''' % type_),
        ('value', '``basestring``', valdoc),
        ('maxlength', '``int``',
            '''Maximum length. If omitted or ``None``, the attribute '''
            '''is *deleted*.'''),
        ('accept', 'iterable',
            '''The list of accepted mime-types, if it's ``None``, the '''
            '''corresponding attribute won't be touched '''
            '''(``[u'type', ...]``)'''),
        ('selected', '``bool``',
            '''This option is used to determine whether the control '''
            '''is checked or not. It's a three-way-boolean: yes, no, '''
            '''maybe :-). If unset or ``None`` it's "maybe" and taken '''
            '''out of the request. Otherwise the boolean value '''
            '''determines the initial state of the control.'''),
        ('src', '``basestring``',
            '''Image source URL. If unset or ``None``, it's left '''
            '''untouched.'''),
        ('alt', '``basestring``',
            '''Alternative text for the image. If unset or ``None``, '''
            '''it's left untouched.'''),
        ('width', '``int``',
            '''Width of the image. If unset or ``None``, the '''
            '''attribute is left untouched.'''),
        ('height', '``int``',
            '''Height of the image. If unset or ``None``, the '''
            '''attribute is left untouched.'''),
        ('readonly', '``bool``',
            '''Readonly field? If unset or ``None``, the attribute is '''
            '''left untouched.'''),
        ('disabled', '``bool``',
            '''Disabled field? If unset or ``None``, the attribute is '''
            '''left untouched.'''),
        ('required', '``bool``',
            '''Required field? (HTML5). If omitted or ``None``, the '''
            '''attribute is left untouched.'''),
        ('autocomplete', '``bool``',
            '''Allow autocompletion? (HTML5). If omitted or ``None``, '''
            '''the attribute is left untouched.'''),
        ('placeholder', '``basestring``',
            'Placeholder value (HTML5). If omitted or ``None``, the '''
            '''attribute is left untouched.'''),
        ('list', '``basestring``',
            '''Datalist ID (HTML5). If omitted or ``None``, the '''
            '''attribute is left untouched.'''),
        ('min', '``basestring``',
            '''Minimum value. If omitted or ``None``, the attribute '''
            '''is left untouched.'''),
        ('max', '``basestring``',
            '''Maximum value. If omitted or ``None``, the attribute '''
            '''is left untouched.'''),
        ('step', '``basestring``',
            '''Step value. If omitted or ``None``, the attribute '''
            '''is left untouched.'''),
        ('pattern', '``basestring``',
            '''Validation pattern (HTML5). If omitted or ``None``, '''
            '''the attribute is left untouched.'''),
        ('dirname', '``basestring``',
            '''Direction submission name (HTML5). If omitted or '''
            '''``None``, the attribute is left untouched.'''),
        ('multiple', '``bool``',
            '''Multiple items allowed? (HTML5) If omitted or '''
            '''``None``, the attribute is left untouched.'''),
        ('action', '``basestring``',
            '''formaction modifier of the control (HTML5). If omitted '''
            '''or ``None``, the attribute is left untouched.'''),
        ('enctype', '``basestring``',
            '''formenctype modifier of the control (HTML5). If omitted '''
            '''or ``None``, the attribute is left untouched.'''),
        ('method', '``basestring``',
            '''formmethod modifier of the control (HTML5). If omitted '''
            '''or ``None``, the attribute is left untouched.'''),
        ('novalidate', '``bool``',
            '''formnovalidate modifier of the control (HTML5). If '''
            '''omitted or ``None``, the attribute is left untouched.'''),
        ('target', '``basestring``',
            '''formtarget modifier of the control (HTML5). If omitted '''
            '''or ``None``, the attribute is left untouched.'''),
        ('autofocus', '``bool``',
            '''Set autofocus? (HTML5). If omitted or ``None``, '''
            '''the attribute is left untouched.'''),
        ('raw', '``bool``',
            '''Is the value to be treated raw?'''),
    ]
    doc = [
        ('node', '`tdi.nodetree.Node`',
            '''The %s input node''' % type_),
    ]
    param = ['self', 'node']
    words = []
    for word, wtype, docstring in candidates:
        if keywords.pop(word, False):
            if word == 'raw':
                param.append('raw=False')
            elif word == 'name':
                if kwargs.get('name_optional'):
                    param.append('%s=None' % word)
                else:
                    param.append(word)
            elif word == 'value' and 'value_default' in kwargs:
                default = kwargs['value_default']
                if default is None:
                    param.append(word)
                else:
                    param.append('%s=%r' % (word, default))
            else:
                param.append('%s=None' % word)
            doc.append((word, wtype, docstring))
            words.append(word)
    if keywords:  # pragma: no cover
        raise AssertionError("Unrecognized keywords: %s" % ', '.join(
            keywords.keys()
        ))
    elif 'value' not in words and 'raw' in words:  # pragma: no cover
        raise AssertionError("Unexpected keyword: raw (no value)")

    s8, s12 = ' ' * 8, ' ' * 12  # pylint: disable = invalid-name
    code = _textwrap.dedent(r'''
    def %(ti)s(%(p)s):
        """
        Render a %(t)r input control%(doc_extra)s

        :Parameters:
    %(d)s
        """%(ass)s
        pre_proc = self._pre_proc
        if pre_proc is not None:
            (
    %(v)s
            ) = pre_proc(%(vt)s)

        node[u'type'] = u%(t)r
    %(name)s%(readonly)s%(disabled)s%(required)s%(autocomplete)s'''
        # noqa
        '''%(autofocus)s'''
        '''%(placeholder)s%(pattern)s%(list)s%(dirname)s%(mul)s'''
        '''%(min)s%(max)s%(step)s'''
        '''%(simpval)s%(rawlenval)s%(rawval)s%(lenval)s%(val)s%(noval)s'''
        '''%(lennoval)s%(mulselected)s%(selected)s%(accept)s'''
        '''%(src)s%(alt)s%(width)s%(height)s'''
        '''%(action)s%(enctype)s%(method)s%(novalidate)s%(target)s
        post_proc = self._post_proc
        if post_proc is not None:
            post_proc(%(t)r, node, dict(%(vd)s))
    '''.rstrip() + '\n') % dict(
        t=type_,
        ti=type_id,
        doc_extra=doc_extra,
        p=_textwrap.fill(', '.join(param), 73 - len(type_),
            subsequent_indent='     ' + ' ' * len(type_),
        ),
        d='\n\n'.join([
            "      `%s` : %s\n%s" % (word, wtype, _textwrap.fill(
            docstring, initial_indent=s8, subsequent_indent=s8,
        )) for word, wtype, docstring in doc]),
        v=_textwrap.fill(', '.join([word for word, _, _ in doc]),
            initial_indent=s12, subsequent_indent=s12
        ),
        vt='%r, node,\n%s\n%s' % (type_, _textwrap.fill(
            ', '.join([
                '(%r, %s)' % (word, word) for word, _, _ in doc[1:]
            ]),
            initial_indent=s12, subsequent_indent=s12
        ), s8),
        vd='\n%s\n%s' % (_textwrap.fill(
            ', '.join([
                '%s=%s' % (word, word) for word, _, _ in doc[1:]
            ]),
            initial_indent=s12, subsequent_indent=s12
        ), s8),
        ass=kwargs.get('assert_upload') and
            '\n'
            r'''    assert self._upload, "Form not initialized with '''
                r'''upload=True"''' '\n'
            or '',
        name='name' in words and
            r'''    if name is not None:''' '\n'
            r'''        node[u'name'] = name''' '\n'
            or '',
        readonly='readonly' in words and
            r'''    if readonly is not None:''' '\n'
            r'''        if readonly:''' '\n'
            r'''            node[u'readonly'] = self._xhtml and '''
                r'''u'readonly' or None''' '\n'
            r'''        else:''' '\n'
            r'''            del node[u'readonly']''' '\n'
            or '',
        disabled='disabled' in words and
            r'''    if disabled is not None:''' '\n'
            r'''        if disabled:''' '\n'
            r'''            node[u'disabled'] = self._xhtml and '''
                r'''u'disabled' or None''' '\n'
            r'''        else:''' '\n'
            r'''            del node[u'disabled']''' '\n'
            or '',
        required='required' in words and
            r'''    if required is not None:''' '\n'
            r'''        if required:''' '\n'
            r'''            node[u'required'] = self._xhtml and '''
                r'''u'required' or None''' '\n'
            r'''        else:''' '\n'
            r'''            del node[u'required']''' '\n'
            or '',
        autocomplete='autocomplete' in words and
            r'''    if autocomplete is not None:''' '\n'
            r'''        node[u'autocomplete'] = autocomplete and '''
                r'''u'on' or u'off''' '\'\n'
            or '',
        autofocus='autofocus' in words and
            r'''    if autofocus is not None:''' '\n'
            r'''        if autofocus:''' '\n'
            r'''            node[u'autofocus'] = self._xhtml and '''
                r'''u'autofocus' or None''' '\n'
            r'''        else:''' '\n'
            r'''            del node[u'autofocus']''' '\n'
            or '',
        placeholder='placeholder' in words and
            r'''    if placeholder is not None:''' '\n'
            r'''        node[u'placeholder'] = placeholder''' '\n'
            or '',
        pattern='pattern' in words and
            r'''    if pattern is not None:''' '\n'
            r'''        node[u'pattern'] = pattern''' '\n'
            or '',
        list='list' in words and
            r'''    if list is not None:''' '\n'
            r'''        node[u'list'] = list''' '\n'
            or '',
        min='min' in words and
            r'''    if min is not None:''' '\n'
            r'''        node[u'min'] = uniode(min)''' '\n'
            or '',
        max='max' in words and
            r'''    if max is not None:''' '\n'
            r'''        node[u'max'] = unicode(max)''' '\n'
            or '',
        step='step' in words and
            r'''    if step is not None:''' '\n'
            r'''        node[u'step'] = unicode(step)''' '\n'
            or '',
        dirname='dirname' in words and
            r'''    if dirname is not None:''' '\n'
            r'''        node[u'dirname'] = dirname''' '\n'
            or '',
        mul='multiple' in words and
            r'''    if multiple is not None:''' '\n'
            r'''        node[u'multiple'] = self._xhtml and '''
                r'''u'multiple' or None''' '\n'
            or '',
        simpval='value' in words and kwargs.get('simple_value') and
            r'''    if value is not None:''' '\n'
            r'''        node[u'value'] = value''' '\n'
            or '',
        rawlenval='raw' in words and 'maxlength' in words and
            not kwargs.get('simple_value') and
            r'''    if value is None:''' '\n'
            r'''        value, raw = self._param.getfirst(name, '''
                r'''u''), False''' '\n'
            r'''    if maxlength is not None:''' '\n'
            r'''        value = value[:int(maxlength)]''' '\n'
            r'''        node[u'maxlength'] = unicode(maxlength)''' '\n'
            r'''    else:''' '\n'
            r'''        del node[u'maxlength']''' '\n'
            r'''    if raw:''' '\n'
            r'''        node.raw[u'value'] = value''' '\n'
            r'''    else:''' '\n'
            r'''        node[u'value'] = self.normalize_whitespaces'''
                r'''(value)''' '\n'
            or '',
        rawval='raw' in words and 'maxlength' not in words and
            not kwargs.get('simple_value') and
            r'''    if value is None:''' '\n'
            r'''        value, raw = self._param.getfirst(name, '''
                r'''u''), False''' '\n'
            r'''    if raw:''' '\n'
            r'''        node.raw[u'value'] = value''' '\n'
            r'''    else:''' '\n'
            r'''        node[u'value'] = self.normalize_whitespaces'''
                r'''(value)''' '\n'
            or '',
        lenval='raw' not in words and 'maxlength' in words and
            'value' in words and not kwargs.get('simple_value') and
            r'''    if value is None:''' '\n'
            r'''        value = self._param.getfirst(name, u'')''' '\n'
            r'''    if maxlength is not None:''' '\n'
            r'''        value = value[:int(maxlength)]''' '\n'
            r'''        node[u'maxlength'] = unicode(maxlength) ''' '\n'
            r'''    else:''' '\n'
            r'''        del node[u'maxlength']''' '\n'
            r'''    node[u'value'] = self.normalize_whitespaces'''
                r'''(value)''' '\n'
            or '',
        val='raw' not in words and 'maxlength' not in words and
            'value' in words and not kwargs.get('simple_value') and
            r'''    if value is None:''' '\n'
            r'''        value = self._param.getfirst(name, u'')''' '\n'
            r'''    node[u'value'] = self.normalize_whitespaces'''
                r'''(value)''' '\n'
            or '',
        lennoval='value' not in words and 'maxlength' in words and
            r'''    del node[u'value']''' '\n'
            r'''    if maxlength is not None:''' '\n'
            r'''        node[u'maxlength'] = unicode(maxlength) ''' '\n'
            r'''    else:''' '\n'
            r'''        del node[u'maxlength']''' '\n'
            or '',
        noval='value' not in words and 'maxlength' not in words and
            r'''    del node[u'value']''' '\n'
            or '',
        mulselected='selected' in words and kwargs.get('multi_selected')
            and
            r'''    if selected is None:''' '\n'
            r'''        selected = value in self._param.getlist'''
                r'''(name)''' '\n'
            r'''    if selected:''' '\n'
            r'''        node[u'checked'] = self._xhtml and '''
                r'''u'checked' or None''' '\n'
            r'''    else:''' '\n'
            r'''        del node[u'checked']''' '\n'
            or '',
        selected='selected' in words and not kwargs.get('multi_selected')
            and
            r'''    if selected is None:''' '\n'
            r'''        selected = value == self._param.getfirst'''
                r'''(name, u'')''' '\n'
            r'''    if selected:''' '\n'
            r'''        node[u'checked'] = self._xhtml and '''
                r'''u'checked' or None''' '\n'
            r'''    else:''' '\n'
            r'''        del node[u'checked']''' '\n'
            or '',
        accept='accept' in words and
            r'''    if accept is not None:''' '\n'
            r'''        node[u'accept'] = u', '.join(accept)''' '\n'
            or '',
        action='action' in words and
            r'''    if action is not None:''' '\n'
            r'''        node[u'formaction'] = action''' '\n'
            or '',
        enctype='enctype' in words and
            r'''    if enctype is not None:''' '\n'
            r'''        node[u'formenctype'] = enctype''' '\n'
            or '',
        method='method' in words and
            r'''    if method is not None:''' '\n'
            r'''        node[u'formmethod'] = method''' '\n'
            or '',
        novalidate='novalidate' in words and
            r'''    if novalidate is not None:''' '\n'
            r'''        if novalidate:''' '\n'
            r'''            node[u'formnovalidate'] = self._xhtml and '''
                r'''u'formnovalidate' or None''' '\n'
            r'''        else:''' '\n'
            r'''            del node[u'formnovalidate']''' '\n'
            or '',
        target='target' in words and
            r'''    if target is not None:''' '\n'
            r'''        node[u'formtarget'] = target''' '\n'
            or '',
        src='src' in words and
            r'''    if src is not None:''' '\n'
            r'''        node[u'src'] = src''' '\n'
            or '',
        alt='alt' in words and
            r'''    if alt is not None:''' '\n'
            r'''        node[u'alt'] = alt''' '\n'
            or '',
        width='width' in words and
            r'''    if width is not None:''' '\n'
            r'''        node[u'width'] = unicode(width)''' '\n'
            or '',
        height='height' in words and
            r'''    if height is not None:''' '\n'
            r'''        node[u'height'] = unicode(height)''' '\n'
            or '',
    )
    exec code  # pylint: disable = exec-used
    return locals()[type_id]
