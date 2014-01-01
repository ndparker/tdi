/*
 * Copyright 2013
 * Andr\xe9 Malo or his licensors, as applicable
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "cext.h"
#include "tdi_exceptions.h"

#include "obj_attribute_analyzer.h"

#define FLAG_REMOVE (1 << 0)
#define FLAG_HIDDEN (1 << 1)


typedef struct attribute_analyzer {
    PyObject_HEAD
    PyObject *weakreflist;

    PyObject *attribute;
    PyObject *overlay;
    PyObject *scope;
    PyObject *decoder;
    PyObject *decode_attr;
    PyObject *normalize;
    int flags;
} attribute_analyzer;

typedef struct special_s {
    PyObject *attribute;
    PyObject *overlay;
    PyObject *scope;
} special_s;

typedef struct parsed_special_s {
    PyObject *flags;
    PyObject *name;
} parsed_special_s;

/* --------------------------- END DECLARATIONS -------------------------- */

#define U(c) ((Py_UNICODE)(c))

static PyObject *
bare_attr(attribute_analyzer *self, PyObject *name, PyObject *value)
{
    PyObject *decoded, *result, *format, *args, *err;
    Py_UNICODE *o, *os, *p, *ps;

    if (!(decoded = PyObject_CallFunction(self->decode_attr, "O", value)))
        return NULL;

    if (!PyUnicode_Check(decoded)) {
        PyErr_SetString(PyExc_ValueError,
                        "decoder.attribute did not return unicode.");
        goto error_decoded;
    }

    o = p = PyUnicode_AS_UNICODE(decoded);
    os = ps = p + PyUnicode_GET_SIZE(decoded);

    while (p < ps) {switch (*p++) {
    case U(' '): case U('\t'): case U('\r'): case U('\n'): case U('\f'):
        continue;
    default:
        --p; break;
    } break;}

    while (p < ps) {switch (*--ps) {
    case U(' '): case U('\t'): case U('\r'): case U('\n'): case U('\f'):
        continue;
    default:
        ++ps; break;
    } break;}

    if (!(p < ps))
        goto error_empty;

    if (!(o == p && os == ps)) {
        if (!(result = PyUnicode_FromUnicode(p, ps - p)))
            goto error_decoded;
        Py_DECREF(decoded);
    }
    else
        result = decoded;

    return result;

error_empty:
    if (!(format = PyString_FromString("Empty %s attribute")))
        goto error_decoded;
    if (!(args = PyTuple_New(1)))
        goto error_format;
    Py_INCREF(name);
    PyTuple_SET_ITEM(args, 0, name);
    if (!(err = PyString_Format(format, args)))
        goto error_args;
    PyErr_SetObject(TDI_E_TemplateAttributeEmptyError, err);
    Py_DECREF(err);
error_args:
    Py_DECREF(args);
error_format:
    Py_DECREF(format);
error_decoded:
    Py_DECREF(decoded);
    return NULL;
}

/*
 * Scope matcher
 */
static Py_ssize_t
match_scope(PyObject *scope)
{
    Py_UNICODE *o, *p, *ps, *name;
    int plusminus = 0, equals = 0;
    Py_UNICODE c;

    o = p = PyUnicode_AS_UNICODE(scope);
    name = ps = p + PyUnicode_GET_SIZE(scope);

    while (p < ps) {switch (*p++) {
    case U('+'): case U('-'): if (plusminus++) return -1; continue;
    case U('='):              if (equals++) return -1; continue;
    default:                  name = --p; break;
    } break;}

    while (p < ps) {c = *p++;
        if ((c >= U('a') && c <= U('z')) || (c >= U('A') && c <= U('Z')))
            continue;

        if ((c >= U('0') && c <= U('9')) || c == U('_') || c == U('.')) {
            if (!(p - 1 > name))
                return -1;
            if (*(p - 2) == U('.'))
                return -1;
            continue;
        }

        return -1;
    }

    if (name < ps && *(ps - 1) == U('.'))
        return -1;

    return (name - o);
}

/*
 * Overlay matcher
 */
static Py_ssize_t
match_overlay(PyObject *overlay)
{
    Py_UNICODE *o, *p, *ps, *name;
    int plusminus = 0, ltgt = 0;
    Py_UNICODE c;

    o = p = PyUnicode_AS_UNICODE(overlay);
    name = ps = p + PyUnicode_GET_SIZE(overlay);

    while (p < ps) {switch (c = *p++) {
    case U('+'): case U('-'): if (plusminus++) return -1; continue;
    case U('<'): case U('>'): if (ltgt++) return -1; continue;
    default:
        if ((c >= U('a') && c <= U('z')) || (c >= U('A') && c <= U('Z')))
            name = p - 1; break;
        return -1;
    } break;}

    if (!(name < ps))
        return -1;

    while (p < ps) {c = *p++;
        if (!((c >= U('a') && c <= U('z')) || (c >= U('A') && c <= U('Z'))
            || (c >= U('0') && c <= U('9')) || c == U('_')))
            return -1;
    }

    return (name - o);
}

/*
 * Attribute Matcher
 */
static Py_ssize_t
match_attribute(PyObject *attribute)
{
    Py_UNICODE *o, *p, *ps, *name;
    int plusminus = 0, colon = 0, star = 0;
    Py_UNICODE c;

    o = p = PyUnicode_AS_UNICODE(attribute);
    name = ps = p + PyUnicode_GET_SIZE(attribute);

    while (p < ps) {switch (c = *p++) {
    case U('+'): case U('-'): if (plusminus++) return -1; continue;
    case U(':'):              if (colon++) return -1; continue;
    case U('*'):              if (star++) return -1; continue;
    default:
        if ((c >= U('a') && c <= U('z')) || (c >= U('A') && c <= U('Z')))
            name = p - 1; break;
        return -1;
    } break;}

    if (!(name < ps)) {
        if ((name - o) == 1 && *o == U('-'))
            return 1;
        return -1;
    }

    while (p < ps) {c = *p++;
        if (!((c >= U('a') && c <= U('z')) || (c >= U('A') && c <= U('Z'))
            || (c >= U('0') && c <= U('9')) || c == U('_')))
            return -1;
    }

    return (name - o);
}

#undef U

static void
raise_invalid_attribute(PyObject *name, PyObject *value)
{
    PyObject *format, *args, *err;

    if (!(format = PyString_FromString("Invalid %s attribute %r")))
        return;
    if (!(args = PyTuple_New(2)))
        goto error_format;
    Py_INCREF(name);
    PyTuple_SET_ITEM(args, 0, name);
    Py_INCREF(value);
    PyTuple_SET_ITEM(args, 1, value);
    if (!(err = PyString_Format(format, args)))
        goto error_args;
    PyErr_SetObject(TDI_E_TemplateAttributeError, err);
    Py_DECREF(err);

error_args:
    Py_DECREF(args);
error_format:
    Py_DECREF(format);
}

static int
fixup_flags(attribute_analyzer *self, PyObject **flags_)
{
    PyObject *flags = *flags_, *result;
    const char *p, *ps;
    int minus = 0;

    p = PyString_AS_STRING(flags);
    ps = p + PyString_GET_SIZE(flags);

    while (p < ps) {switch (*p++) {
        case '+':
            result = PyObject_CallMethod(flags, "replace", "ss", "+", "");
            if (!result)
                return -1;
            Py_DECREF(flags);
            *flags_ = result;
            return 0;

        case '-':
            ++minus;
    }}

    if (!minus && (self->flags & FLAG_HIDDEN)) {
        if (!(result = PyString_FromString("-")))
            return -1;
        PyString_ConcatAndDel(&flags, result);
        if (!flags)
            return -1;
        *flags_ = flags;
    }

    return 0;
}

static int
load_parsed(attribute_analyzer *self, PyObject *value, Py_ssize_t split,
            parsed_special_s *parsed)
{
    PyObject *flags, *name, *encoding_o;
    Py_UNICODE *p, *p1;
    const char *encoding;

    if (!(encoding_o = PyObject_GetAttrString(self->decoder, "encoding")))
        return -1;
    if (!(encoding = PyString_AsString(encoding_o)))
        goto error_encoding;

    p = PyUnicode_AS_UNICODE(value);
    p1 = p + split;

    if (!(flags = PyUnicode_Encode(p, p1 - p, encoding, "strict")))
        goto error_encoding;

    if (fixup_flags(self, &flags) == -1)
        goto error_flags;

    p += PyUnicode_GET_SIZE(value);
    if (!(name = PyUnicode_Encode(p1, p - p1, encoding, "strict")))
        goto error_flags;

    parsed->flags = flags;
    parsed->name = name;

    return 0;

error_flags:
    Py_DECREF(flags);
error_encoding:
    Py_DECREF(encoding_o);

    return -1;
}

static int
parse_scope(attribute_analyzer *self, PyObject *scope,
            parsed_special_s *parsed)
{
    PyObject *decoded;
    Py_ssize_t split;

    if (!(decoded = bare_attr(self, self->scope, scope)))
        return -1;

    if ((split = match_scope(decoded)) == -1) {
        raise_invalid_attribute(self->scope, decoded);
        goto error_decoded;
    }

    if (load_parsed(self, decoded, split, parsed) == -1)
        goto error_decoded;

    return 0;

error_decoded:
    Py_DECREF(decoded);
    return -1;
}

static int
parse_overlay(attribute_analyzer *self, PyObject *overlay,
              parsed_special_s *parsed)
{
    PyObject *decoded;
    Py_ssize_t split;

    if (!(decoded = bare_attr(self, self->overlay, overlay)))
        return -1;

    if ((split = match_overlay(decoded)) == -1) {
        raise_invalid_attribute(self->overlay, decoded);
        goto error_decoded;
    }

    if (load_parsed(self, decoded, split, parsed) == -1)
        goto error_decoded;

    return 0;

error_decoded:
    Py_DECREF(decoded);
    return -1;
}

static int
parse_attribute(attribute_analyzer *self, PyObject *attribute,
                parsed_special_s *parsed)
{
    PyObject *decoded;
    Py_ssize_t split;

    if (!(decoded = bare_attr(self, self->attribute, attribute)))
        return -1;

    if ((split = match_attribute(decoded)) == -1) {
        raise_invalid_attribute(self->attribute, decoded);
        goto error_decoded;
    }

    if (load_parsed(self, decoded, split, parsed) == -1)
        goto error_decoded;

    if (PyString_GET_SIZE(parsed->name) == 0) {
        Py_INCREF(Py_None);
        Py_CLEAR(parsed->name);
        parsed->name = Py_None;
    }

    return 0;

error_decoded:
    Py_DECREF(decoded);
    return -1;
}

static int
parse_name(attribute_analyzer *self, PyObject *name,
           parsed_special_s *parsed)
{
    PyObject *decoded;
    Py_ssize_t split;

    if (!(decoded = PyObject_CallMethod(self->decoder, "decode", "O", name)))
        return -1;
    if (!PyUnicode_Check(decoded)) {
        PyErr_SetString(PyExc_ValueError,
                        "name.decode() did not return unicode.");
        goto error_decoded;
    }

    if ((split = match_attribute(decoded)) == -1) {
        raise_invalid_attribute(self->attribute, decoded);
        goto error_decoded;
    }

    if (load_parsed(self, decoded, split, parsed) == -1)
        goto error_decoded;

    if (PyString_GET_SIZE(parsed->name) == 0) {
        Py_INCREF(Py_None);
        Py_CLEAR(parsed->name);
        parsed->name = Py_None;
    }

    return 0;

error_decoded:
    Py_DECREF(decoded);
    return -1;
}

static PyObject *
parse_special(attribute_analyzer *self, special_s *special, PyObject *name)
{
    PyObject *result, *tup, *format, *args, *err;
    parsed_special_s parsed_special, parsed_name;
    int res, cmp, use_name = 0;

    if (!(result = PyDict_New()))
        return NULL;

    if (special->scope) {
        if (parse_scope(self, special->scope, &parsed_special) == -1)
            goto error_result;
        if (!(tup = PyTuple_New(2)))
            goto error_parsed;
        PyTuple_SET_ITEM(tup, 0, parsed_special.flags);
        PyTuple_SET_ITEM(tup, 1, parsed_special.name);
        res = PyDict_SetItemString(result, "scope", tup);
        Py_DECREF(tup);
        if (res == -1)
            goto error_result;
    }

    if (special->overlay) {
        if (parse_overlay(self, special->overlay, &parsed_special) == -1)
            goto error_result;
        if (!(tup = PyTuple_New(2)))
            goto error_parsed;
        PyTuple_SET_ITEM(tup, 0, parsed_special.flags);
        PyTuple_SET_ITEM(tup, 1, parsed_special.name);
        res = PyDict_SetItemString(result, "overlay", tup);
        Py_DECREF(tup);
        if (res == -1)
            goto error_result;
    }

    if (name && name != Py_None && PyString_Check(name)
        && PyString_GET_SIZE(name) > 0) {
        use_name = 1;
        if (parse_name(self, name, &parsed_name) == -1)
            goto error_result;
    }
    if (special->attribute) {
        if (parse_attribute(self, special->attribute, &parsed_special) == -1)
            goto error_result;
        if (use_name) {
            res = PyObject_Cmp(parsed_name.flags, parsed_special.flags, &cmp);
            if (res == -1) {
                goto error_parsed;
            }
            else if (!cmp) {
                res = PyObject_Cmp(parsed_name.name, parsed_special.name,
                                   &cmp);
                if (res == -1) {
                    goto error_parsed;
                }
            }
            if (cmp)
                goto error_not_equal;
            Py_DECREF(parsed_name.flags);
            Py_DECREF(parsed_name.name);
            use_name = 0; /* no longer needed. Fixes up error path */
        }
        if (!(tup = PyTuple_New(2)))
            goto error_parsed;
        PyTuple_SET_ITEM(tup, 0, parsed_special.flags);
        PyTuple_SET_ITEM(tup, 1, parsed_special.name);
        res = PyDict_SetItemString(result, "attribute", tup);
        Py_DECREF(tup);
        if (res == -1)
            goto error_result;
    }
    else if (use_name) {
        if (!(tup = PyTuple_New(2)))
            goto error_name;
        PyTuple_SET_ITEM(tup, 0, parsed_name.flags);
        PyTuple_SET_ITEM(tup, 1, parsed_name.name);
        res = PyDict_SetItemString(result, "attribute", tup);
        Py_DECREF(tup);
        if (res == -1)
            goto error_result;
    }

    return result;

error_not_equal:
    format = PyString_FromString("%s attribute value %r must equal name");
    if (!format)
        goto error_parsed;
    if (!(args = PyTuple_New(2)))
        goto error_format;
    Py_INCREF(self->attribute);
    PyTuple_SET_ITEM(args, 0, self->attribute);
    Py_INCREF(name);
    PyTuple_SET_ITEM(args, 1, name);
    if (!(err = PyString_Format(format, args)))
        goto error_args;
    PyErr_SetObject(TDI_E_TemplateAttributeError, err);
    Py_DECREF(err);
error_args:
    Py_DECREF(args);
error_format:
    Py_DECREF(format);
error_parsed:
    Py_DECREF(parsed_special.flags);
    Py_DECREF(parsed_special.name);
error_name:
    if (use_name) {
        Py_DECREF(parsed_name.flags);
        Py_DECREF(parsed_name.name);
    }
error_result:
    Py_DECREF(result);

    return NULL;
}

static int
find_special(attribute_analyzer *self, PyObject *attr, PyObject **reduced_,
             special_s *special)
{
    PyObject *tup, *iter, *key, *value, *reduced, *args, *format, *err;
    int found = 0, cmp;

    /* 1st pass: search for specials */
    if (!(iter = PyObject_GetIter(attr)))
        return -1;
    while ((tup = PyIter_Next(iter))) {
        if (PyArg_Parse(tup, "(OO)", &key, &value) == -1)
            goto error1_tup;
        if (!(key = PyObject_CallFunction(self->normalize, "O", key)))
            goto error1_tup;
        if (PyObject_Cmp(key, self->attribute, &cmp) == -1)
            goto error1_key;
        if (cmp) {
            if (PyObject_Cmp(key, self->overlay, &cmp) == -1)
                goto error1_key;
            if (cmp) {
                if (PyObject_Cmp(key, self->scope, &cmp) == -1)
                    goto error1_key;
            }
        }
        Py_DECREF(key);
        Py_DECREF(tup);
        if (!cmp) {
            found = 1;
            break;
        }
    }
    if (PyErr_Occurred())
        goto error1_iter;
    Py_DECREF(iter);

    special->attribute = special->overlay = special->scope = NULL;
    if (!found) {
        *reduced_ = (Py_INCREF(attr), attr);
        return 0;
    }

    /* 2nd pass: assign specials */
    if (!(self->flags & FLAG_REMOVE))
        reduced = (Py_INCREF(attr), attr);
    else if (!(reduced = PyList_New(0)))
        return -1;
    if (!(iter = PyObject_GetIter(attr)))
        goto error2_reduced;
    while ((tup = PyIter_Next(iter))) {
        if (PyArg_Parse(tup, "(OO)", &key, &value) == -1)
            goto error2_tup;
        if (!(key = PyObject_CallFunction(self->normalize, "O", key)))
            goto error2_tup;
        if (PyObject_Cmp(key, self->attribute, &cmp) == -1)
            goto error2_key;
        if (!cmp) {
            if (value == Py_None)
                goto error2_none;
            if (!(special->attribute = PyObject_Str(value)))
                goto error2_key;
        }
        else {
            if (PyObject_Cmp(key, self->overlay, &cmp) == -1)
                goto error2_key;
            if (!cmp) {
                if (value == Py_None)
                    goto error2_none;
                if (!(special->overlay = PyObject_Str(value)))
                    goto error2_key;
            }
            else {
                if (PyObject_Cmp(key, self->scope, &cmp) == -1)
                    goto error2_key;
                if (!cmp) {
                    if (value == Py_None)
                        goto error2_none;
                    if (!(special->scope = PyObject_Str(value)))
                        goto error2_key;
                }
            }
        }
        Py_DECREF(key);
        if (cmp && (self->flags & FLAG_REMOVE)) {
            if (PyList_Append(reduced, tup) == -1)
                goto error2_tup;
        }
        Py_DECREF(tup);
    }
    if (PyErr_Occurred())
        goto error2_iter;
    Py_DECREF(iter);

    *reduced_ = reduced;
    return 0;

error1_key:
    Py_DECREF(key);
error1_tup:
    Py_DECREF(tup);
error1_iter:
    Py_DECREF(iter);

    return -1;

error2_none:
    if (!(format = PyString_FromString("Invalid short %s attribute")))
        goto error2_key;
    if (!(args = PyTuple_New(1)))
        goto error2_format;
    Py_INCREF(key);
    PyTuple_SET_ITEM(args, 0, key);
    if (!(err = PyString_Format(format, args)))
        goto error2_args;
    PyErr_SetObject(TDI_E_TemplateAttributeError, err);
    Py_DECREF(err);
error2_args:
    Py_DECREF(args);
error2_format:
    Py_DECREF(format);
error2_key:
    Py_DECREF(key);
error2_tup:
    Py_DECREF(tup);
error2_iter:
    Py_DECREF(iter);
error2_reduced:
    Py_DECREF(reduced);

    Py_XDECREF(special->attribute);
    Py_XDECREF(special->overlay);
    Py_XDECREF(special->scope);
    return -1;
}

/* -------------- BEGIN TDI_AttributeAnalyzerType DEFINITION ------------- */

static PyObject *
TDI_AttributeAnalyzerType_call(attribute_analyzer *self, PyObject *args,
                               PyObject *kwds)
{
    static char *kwlist[] = {"attr", "name", NULL};
    PyObject *final, *result, *reduced, *attr, *name = NULL;
    special_s special;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O", kwlist,
                                     &attr, &name))
        return NULL;

    if (find_special(self, attr, &reduced, &special) == -1)
        return NULL;

    if (!(result = parse_special(self, &special, name)))
        goto error_reduced;

    Py_XDECREF(special.attribute);
    Py_XDECREF(special.overlay);
    Py_XDECREF(special.scope);

    if (!(final = PyTuple_New(2)))
        goto error_result;
    PyTuple_SET_ITEM(final, 0, reduced);
    PyTuple_SET_ITEM(final, 1, result);

    return final;

error_result:
    Py_DECREF(result);
error_reduced:
    Py_DECREF(reduced);

    Py_XDECREF(special.attribute);
    Py_XDECREF(special.overlay);
    Py_XDECREF(special.scope);

    return NULL;
}

static PyObject *
TDI_AttributeAnalyzerType_getattribute(attribute_analyzer *self,
                                       void *closure)
{
    if (!self->attribute) {
        PyErr_SetString(PyExc_AttributeError, "attribute");
        return NULL;
    }
    return (Py_INCREF(self->attribute), self->attribute);
}

static PyObject *
TDI_AttributeAnalyzerType_getscope(attribute_analyzer *self, void *closure)
{
    if (!self->scope) {
        PyErr_SetString(PyExc_AttributeError, "scope");
        return NULL;
    }
    return (Py_INCREF(self->scope), self->scope);
}

static PyGetSetDef TDI_AttributeAnalyzerType_getset[] = {
    {"attribute",
     (getter)TDI_AttributeAnalyzerType_getattribute,
     NULL,
     NULL, NULL},

    {"scope",
     (getter)TDI_AttributeAnalyzerType_getscope,
     NULL,
     NULL, NULL},

    {NULL}  /* Sentinel */
};

static int
TDI_AttributeAnalyzerType_traverse(attribute_analyzer *self,
                                   visitproc visit, void *arg)
{
    Py_VISIT(self->attribute);
    Py_VISIT(self->overlay);
    Py_VISIT(self->scope);
    Py_VISIT(self->decoder);
    Py_VISIT(self->decode_attr);
    Py_VISIT(self->normalize);

    return 0;
}

static int
TDI_AttributeAnalyzerType_clear(attribute_analyzer *self)
{
    if (self->weakreflist)
        PyObject_ClearWeakRefs((PyObject *)self);

    Py_CLEAR(self->attribute);
    Py_CLEAR(self->overlay);
    Py_CLEAR(self->scope);
    Py_CLEAR(self->decoder);
    Py_CLEAR(self->decode_attr);
    Py_CLEAR(self->normalize);

    return 0;
}

static int
TDI_AttributeAnalyzerType_init(attribute_analyzer *self, PyObject *args,
                               PyObject *kwds)
{
    static char *kwlist[] = {"decoder", "attribute", "overlay", "scope",
                             "removeattribute", "hidden", NULL};
    PyObject *decoder, *attribute = NULL, *overlay = NULL, *scope = NULL,
             *removeattribute = NULL, *hidden = NULL;
    PyObject *tmp, *tmp2;
    int res;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OOOOO", kwlist,
                                     &decoder, &attribute, &overlay, &scope,
                                     &removeattribute, &hidden))
        return -1;

    self->decoder = (Py_INCREF(decoder), decoder);
    if (!(self->normalize = PyObject_GetAttrString(decoder, "normalize")))
        return -1;
    if (!(self->decode_attr = PyObject_GetAttrString(decoder, "attribute")))
        return -1;

    if (!attribute || attribute == Py_None) {
        if (!(tmp = PyString_FromString("tdi")))
            return -1;
        tmp2 = PyObject_CallMethod(decoder, "normalize", "O", tmp);
        Py_DECREF(tmp);
        if (!tmp2)
            return -1;
        self->attribute = PyObject_Str(tmp2);
        Py_DECREF(tmp2);
        if (!self->attribute)
            return -1;
    }
    else {
        tmp = PyObject_CallMethod(decoder, "normalize", "O", attribute);
        if (!tmp)
            return -1;
        self->attribute = PyObject_Str(tmp);
        Py_DECREF(tmp);
        if (!self->attribute)
            return -1;
    }

    if (!overlay || overlay == Py_None) {
        if (!(tmp = PyString_FromString("tdi:overlay")))
            return -1;
        tmp2 = PyObject_CallMethod(decoder, "normalize", "O", tmp);
        Py_DECREF(tmp);
        if (!tmp2)
            return -1;
        self->overlay = PyObject_Str(tmp2);
        Py_DECREF(tmp2);
        if (!self->overlay)
            return -1;
    }
    else {
        tmp = PyObject_CallMethod(decoder, "normalize", "O", overlay);
        if (!tmp)
            return -1;
        self->overlay = PyObject_Str(tmp);
        Py_DECREF(tmp);
        if (!self->overlay)
            return -1;
    }

    if (!scope || scope == Py_None) {
        if (!(tmp = PyString_FromString("tdi:scope")))
            return -1;
        tmp2 = PyObject_CallMethod(decoder, "normalize", "O", tmp);
        Py_DECREF(tmp);
        if (!tmp2)
            return -1;
        self->scope = PyObject_Str(tmp2);
        Py_DECREF(tmp2);
        if (!self->scope)
            return -1;
    }
    else {
        tmp = PyObject_CallMethod(decoder, "normalize", "O", scope);
        if (!tmp)
            return -1;
        self->scope = PyObject_Str(tmp);
        Py_DECREF(tmp);
        if (!self->scope)
            return -1;
    }

    self->flags = 0;
    if (!removeattribute || removeattribute == Py_None)
        self->flags |= FLAG_REMOVE;
    else if ((res = PyObject_IsTrue(removeattribute)) == -1)
        return -1;
    else if (res)
        self->flags |= FLAG_REMOVE;

    if (hidden && hidden != Py_None) {
        if ((res = PyObject_IsTrue(hidden)) == -1)
            return -1;
        if (res)
            self->flags |= FLAG_HIDDEN;
    }

    return 0;
}

static PyObject *
TDI_AttributeAnalyzerType_new(PyTypeObject *type, PyObject *args,
                              PyObject *kwds)
{
    return (PyObject *)GENERIC_ALLOC(type);
}

DEFINE_GENERIC_DEALLOC(TDI_AttributeAnalyzerType)

PyDoc_STRVAR(TDI_AttributeAnalyzerType__doc__,
"Attribute analyzer\n\
\n\
:IVariables:\n\
  `attribute` : ``str``\n\
    The attribute name\n\
\n\
  `scope` : ``str``\n\
    The scope attribute name");

PyTypeObject TDI_AttributeAnalyzerType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".AttributeAnalyzer",               /* tp_name */
    sizeof(attribute_analyzer),                         /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_AttributeAnalyzerType_dealloc,      /* tp_dealloc */
    0,                                                  /* tp_print */
    0,                                                  /* tp_getattr */
    0,                                                  /* tp_setattr */
    0,                                                  /* tp_compare */
    0,                                                  /* tp_repr */
    0,                                                  /* tp_as_number */
    0,                                                  /* tp_as_sequence */
    0,                                                  /* tp_as_mapping */
    0,                                                  /* tp_hash */
    (ternaryfunc)TDI_AttributeAnalyzerType_call,        /* tp_call */
    0,                                                  /* tp_str */
    0,                                                  /* tp_getattro */
    0,                                                  /* tp_setattro */
    0,                                                  /* tp_as_buffer */
    Py_TPFLAGS_HAVE_WEAKREFS                            /* tp_flags */
    | Py_TPFLAGS_HAVE_CLASS
    | Py_TPFLAGS_BASETYPE
    | Py_TPFLAGS_HAVE_GC,
    TDI_AttributeAnalyzerType__doc__,                   /* tp_doc */
    (traverseproc)TDI_AttributeAnalyzerType_traverse,   /* tp_traverse */
    (inquiry)TDI_AttributeAnalyzerType_clear,           /* tp_clear */
    0,                                                  /* tp_richcompare */
    offsetof(attribute_analyzer, weakreflist),          /* tp_weaklistoffset */
    0,                                                  /* tp_iter */
    0,                                                  /* tp_iternext */
    0,                                                  /* tp_methods */
    0,                                                  /* tp_members */
    TDI_AttributeAnalyzerType_getset,                   /* tp_getset */
    0,                                                  /* tp_base */
    0,                                                  /* tp_dict */
    0,                                                  /* tp_descr_get */
    0,                                                  /* tp_descr_set */
    0,                                                  /* tp_dictoffset */
    (initproc)TDI_AttributeAnalyzerType_init,           /* tp_init */
    0,                                                  /* tp_alloc */
    TDI_AttributeAnalyzerType_new,                      /* tp_new */
};

/* --------------- END TDI_AttributeAnalyzerType DEFINITION -------------- */
