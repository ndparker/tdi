/*
 * Copyright 2013 - 2014
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
#include "tdi_globals.h"

#include "obj_avoid_gc.h"
#include "obj_encoder.h"
#include "obj_text_encoder.h"
#include "obj_node.h"
#include "obj_attr.h"


/*
 * Text starttag builder
 */
PyObject *
tdi_text_encode_starttag(tdi_node_t *node)
{
    PyObject *result, *attr;
    tdi_attr_t *item;
    char *cresult;
    Py_ssize_t j, length, size;

    /* 1st pass: count result bytes */
    size = PyString_GET_SIZE(node->tagname) + 2;  /* <> */
    if (node->flags & NODE_CLOSED)
        size += 2;  /* '[]' */

    if (!(attr = PyDict_Values(node->attr)))
        return NULL;
    length = PyList_GET_SIZE(attr);
    for (j = 0; j < length; ++j) {
        if (!(item = (tdi_attr_t *)PyList_GetItem(attr, j))) {
            Py_DECREF(attr);
            return NULL;
        }
        if (item->value == Py_None)
            size += PyString_GET_SIZE(item->key) + 1;  /* ' ' */
        else
            size += PyString_GET_SIZE(item->key)
                + PyString_GET_SIZE(item->value) + 2;  /* ' =' */
    }

    /* 2nd pass: assemble result */
    if (!(result = PyString_FromStringAndSize(NULL, size))) {
        Py_DECREF(attr);
        return NULL;
    }
    cresult = PyString_AS_STRING(result);
    *cresult++ = '[';
    if (node->flags & NODE_CLOSED) *cresult++ = '[';

    size = PyString_GET_SIZE(node->tagname);
    (void)memcpy(cresult, PyString_AS_STRING(node->tagname), (size_t)size);
    cresult += size;

    for (j = 0; j < length; ++j) {
        if (!(item = (tdi_attr_t *)PyList_GetItem(attr, j))) {
            Py_DECREF(result);
            Py_DECREF(attr);
            return NULL;
        }

        *cresult++ = ' ';

        size = PyString_GET_SIZE(item->key);
        (void)memcpy(cresult, PyString_AS_STRING(item->key), (size_t)size);
        cresult += size;

        if (item->value != Py_None) {
            *cresult++ = '=';
            size = PyString_GET_SIZE(item->value);
            (void)memcpy(cresult, PyString_AS_STRING(item->value),
                         (size_t)size);
            cresult += size;
        }
    }
    Py_DECREF(attr);

    if (node->flags & NODE_CLOSED) *cresult++ = ']';
    *cresult = ']';

    return result;
}

/*
 * Text endtag encoder
 */
PyObject *
tdi_text_encode_endtag(tdi_node_t *node)
{
    PyObject *result;
    char *cresult;
    Py_ssize_t size;

    size = PyString_GET_SIZE(node->tagname);
    if (!(result = PyString_FromStringAndSize(NULL, size + 3))) /* [/] */
        return NULL;

    cresult = PyString_AS_STRING(result);
    *cresult++ = '[';
    *cresult++ = '/';
    (void)memcpy(cresult, PyString_AS_STRING(node->tagname), (size_t)size);
    *cresult = ']';

    return result;
}

/*
 * Text name encoder
 */
PyObject *
tdi_text_encode_name(PyObject *name, PyObject *encoding)
{
    if (!(PyUnicode_CheckExact(name) || PyUnicode_Check(name))) {
        Py_INCREF(name);
    }
    else {
        const char *cencoding;

        if (!(cencoding = PyString_AsString(encoding)))
            return NULL;
        name = PyUnicode_AsEncodedString(name, cencoding, "strict");
    }
    return name;
}

/*
 * Text content encoder
 */
PyObject *
tdi_text_encode_content(PyObject *value, PyObject *encoding)
{
    if (PyUnicode_CheckExact(value) || PyUnicode_Check(value)) {
        const char *cencoding = PyString_AsString(encoding);

        if (!cencoding)
            return NULL;
        return PyUnicode_AsEncodedString(value, cencoding, "strict");
    }
    else if (!PyString_CheckExact(value) && !PyString_Check(value)) {
        PyErr_SetString(TDI_E_TemplateEncodingError,
                        "Content encoder takes string or unicode");
        return NULL;
    }

    Py_INCREF(value);
    return value;
}

/*
 * Text attribute encoder
 */
PyObject *
tdi_text_encode_attribute(PyObject *value, PyObject *encoding)
{
    PyObject *tmp;
    Py_ssize_t size, length;
    char *cvalue, *ctmp;
    int is_unicode = (PyUnicode_CheckExact(value) || PyUnicode_Check(value));
    char c;

    if (is_unicode) {
        if (!(value = PyUnicode_AsUTF8String(value)))
            return NULL;
    }
    else {
        if (!PyString_CheckExact(value) && !PyString_Check(value)) {
            PyErr_SetString(TDI_E_TemplateEncodingError,
                            "Attribute encoder takes string or unicode");
            return NULL;
        }
        Py_INCREF(value);
    }

    length = size = PyString_GET_SIZE(value);
    cvalue = PyString_AS_STRING(value);
    while (length--) {
        if (*cvalue++ == '"') ++size;  /* '\\' */
    }
    /* +2 = surrounding quotes */
    if (!(tmp = PyString_FromStringAndSize(NULL, size + 2))) {
        Py_DECREF(value);
        return NULL;
    }
    ctmp = PyString_AS_STRING(tmp);
    cvalue = PyString_AS_STRING(value);
    length = PyString_GET_SIZE(value);
    *ctmp++ = '"';
    while (length--) {
        if ((c = *cvalue++) == '"') *ctmp++ = '\\';
        *ctmp++ = c;
    }
    *ctmp = '"';
    Py_DECREF(value);

    if (is_unicode) {
        const char *cencoding = PyString_AsString(encoding);
        if (!cencoding) {
            Py_DECREF(tmp);
            return NULL;
        }
        value = PyUnicode_DecodeUTF8(PyString_AS_STRING(tmp),
                                     PyString_GET_SIZE(tmp), "strict");
        Py_DECREF(tmp);
        if (!value)
            return NULL;
        tmp = PyUnicode_AsEncodedString(value, cencoding, "strict");
        Py_DECREF(value);
        if (!tmp)
            return NULL;
    }

    return tmp;
}

/*
 * Charset encoder
 */
PyObject *
tdi_text_encode_unicode(PyObject *value, PyObject *encoding)
{
    const char *cencoding;

    if (!PyUnicode_CheckExact(value) && !PyUnicode_Check(value)) {
        PyErr_SetString(TDI_E_TemplateEncodingError,
                        "Charset encoder takes unicode.");
        return NULL;
    }
    if (!(cencoding = PyString_AsString(encoding)))
        return NULL;

    return PyUnicode_AsEncodedString(value, cencoding, "strict");
}


/*
 * Escaper
 */
PyObject *
tdi_text_encode_escape(PyObject *value)
{
    PyObject *tmp;
    char *cvalue, *cp;
    Py_ssize_t length, size, diff = 0;
    char c;

    if (!PyString_CheckExact(value) && !PyString_Check(value)) {
        PyErr_SetString(TDI_E_TemplateEncodingError,
                        "Escaper takes str.");
        return NULL;
    }

    length = size = PyString_GET_SIZE(value);
    cvalue = PyString_AS_STRING(value);
    while (length--) {
        if (*cvalue++ == '[') ++diff;
    }
    if (!diff) {
        Py_INCREF(value);
        return value;
    }

    if (!(tmp = PyString_FromStringAndSize(NULL, size + diff))) {
        return NULL;
    }
    cp = PyString_AS_STRING(tmp);
    cvalue = PyString_AS_STRING(value);
    length = PyString_GET_SIZE(value);
    while (length--) {
        *cp++ = c = *cvalue++;
        if (c == '[') *cp++ = ']';
    }

    return tmp;
}


/* ------------------ BEGIN TDI_TextEncoderType DEFINITION ----------------- */

PyDoc_STRVAR(TDI_TextEncoderType_starttag__doc__,
"starttag(self, name, attr, closed)\n\
\n\
:See: `EncoderInterface`");

static PyObject *
TDI_TextEncoderType_starttag(tdi_text_encoder_t *self, PyObject *args)
{
    PyObject *name, *attr, *closed, *newattr, *attiter, *tmp, *item, *result;
    tdi_attr_t *attritem;
    char *cresult;
    Py_ssize_t size, j, length;
    int res, is_closed;

    if (!(PyArg_ParseTuple(args, "SOO", &name, &attr, &closed)))
        return NULL;

    /* 1st pass - fixup parameters and count result bytes */
    if (!PyString_CheckExact(name)) {
        if (!(name = PyObject_Str(name)))
            return NULL;
    }
    else
        Py_INCREF(name);
    size = PyString_GET_SIZE(name) + 2; /* [] */

    if ((is_closed = PyObject_IsTrue(closed)) == -1) {
        Py_DECREF(name);
        return NULL;
    }
    else if (is_closed) {
        size += 2;
    }

    if (!(attiter = PyObject_GetIter(attr))) {
        Py_DECREF(name);
        return NULL;
    }

    newattr = PyList_New(0);
    while ((tmp = PyIter_Next(attiter))) {
        item = PySequence_Tuple(tmp);
        Py_DECREF(tmp);
        if (!item)
            break;
        if (PyTuple_GET_SIZE(item) != 2) {
            Py_DECREF(item);
            PyErr_SetString(PyExc_TypeError, "Expected Sequence of length 2");
            break;
        }
        tmp = PyTuple_GET_ITEM(item, 0);
        if (PyString_CheckExact(tmp))
            Py_INCREF(tmp);
        else if (PyString_Check(tmp)) {
            if (!(tmp = PyObject_Str(tmp))) {
                Py_DECREF(item);
                break;
            }
        }
        else {
            Py_DECREF(item);
            PyErr_SetString(PyExc_ValueError, "Attribute key is not a string");
            break;
        }
        size += PyString_GET_SIZE(tmp) + 1; /* ' ' */
        attritem = (tdi_attr_t *)tdi_attr_new(tmp, Py_None);
        Py_DECREF(tmp);
        if (!attritem) {
            Py_DECREF(item);
            break;
        }
        tmp = PyTuple_GET_ITEM(item, 1);
        if (tmp != Py_None) {
            if (PyString_CheckExact(tmp)) {
                Py_INCREF(tmp);
                Py_DECREF(Py_None);
                attritem->value = tmp;
            }
            else if (PyString_Check(tmp)) {
                if (!(attritem->value = PyObject_Str(tmp))) {
                    attritem->value = Py_None;
                    break;
                }
                Py_DECREF(Py_None);
            }
            else {
                Py_DECREF(item);
                PyErr_SetString(PyExc_ValueError,
                    "Attribute value is neither a string nor None");
                break;
            }
            size += PyString_GET_SIZE(attritem->value) + 1; /* '=' */
        }
        Py_DECREF(item);
        res = PyList_Append(newattr, (PyObject *)attritem);
        Py_DECREF(attritem);
        if (res == -1)
            break;
    }
    Py_DECREF(attiter);
    if (PyErr_Occurred()) {
        Py_DECREF(newattr);
        Py_DECREF(name);
        return NULL;
    }

    /* 2nd pass: assemble result */
    if (!(result = PyString_FromStringAndSize(NULL, size))) {
        Py_DECREF(newattr);
        Py_DECREF(name);
        return NULL;
    }
    cresult = PyString_AS_STRING(result);
    *cresult++ = '[';
    if (is_closed) *cresult++ = '[';

    size = PyString_GET_SIZE(name);
    (void)memcpy(cresult, PyString_AS_STRING(name), (size_t)size);
    cresult += size;
    Py_DECREF(name);

    length = PyList_GET_SIZE(newattr);
    for (j = 0; j < length; ++j) {
        attritem = (tdi_attr_t *)PyList_GET_ITEM(newattr, j);
        *cresult++ = ' ';

        size = PyString_GET_SIZE(attritem->key);
        (void)memcpy(cresult, PyString_AS_STRING(attritem->key), (size_t)size);
        cresult += size;

        if (attritem->value != Py_None) {
            *cresult++ = '=';
            size = PyString_GET_SIZE(attritem->value);
            (void)memcpy(cresult, PyString_AS_STRING(attritem->value),
                         (size_t)size);
            cresult += size;
        }
    }
    Py_DECREF(newattr);

    if (is_closed) *cresult++ = ']';
    *cresult = ']';

    return result;
}

PyDoc_STRVAR(TDI_TextEncoderType_endtag__doc__,
"endtag(self, name)\n\
\n\
:See: `EncoderInterface`");

static PyObject *
TDI_TextEncoderType_endtag(tdi_text_encoder_t *self, PyObject *args)
{
    PyObject *name, *result;
    char *cresult;
    Py_ssize_t size;

    if (!(PyArg_ParseTuple(args, "S", &name)))
        return NULL;

    if (!PyString_CheckExact(name)) {
        if (!(name = PyObject_Str(name)))
            return NULL;
    }
    else
        Py_INCREF(name);

    size = PyString_GET_SIZE(name);
    if (!(result = PyString_FromStringAndSize(NULL, size + 3))) { /* [/] */
        Py_DECREF(name);
        return NULL;
    }
    cresult = PyString_AS_STRING(result);
    *cresult++ = '[';
    *cresult++ = '/';
    (void)memcpy(cresult, PyString_AS_STRING(name), (size_t)size);
    Py_DECREF(name);
    cresult += size;
    *cresult = ']';

    return result;
}

PyDoc_STRVAR(TDI_TextEncoderType_name__doc__,
"name(self, name)\n\
\n\
:See: `EncoderInterface`");

static PyObject *
TDI_TextEncoderType_name(tdi_text_encoder_t *self, PyObject *args)
{
    PyObject *name;

    if (!(PyArg_ParseTuple(args, "O", &name)))
        return NULL;

    return tdi_text_encode_name(name, self->encoding);
}

PyDoc_STRVAR(TDI_TextEncoderType_content__doc__,
"content(self, value)\n\
\n\
:See: `EncoderInterface`");

static PyObject *
TDI_TextEncoderType_content(tdi_text_encoder_t *self, PyObject *args)
{
    PyObject *value;

    if (!(PyArg_ParseTuple(args, "O", &value)))
        return NULL;

    return tdi_text_encode_content(value, self->encoding);
}

PyDoc_STRVAR(TDI_TextEncoderType_attribute__doc__,
"attribute(self, value)\n\
\n\
:See: `EncoderInterface`");

static PyObject *
TDI_TextEncoderType_attribute(tdi_text_encoder_t *self, PyObject *args)
{
    PyObject *value;

    if (!(PyArg_ParseTuple(args, "O", &value)))
        return NULL;

    return tdi_text_encode_attribute(value, self->encoding);
}

PyDoc_STRVAR(TDI_TextEncoderType_encode__doc__,
"encode(self, value)\n\
\n\
:See: `EncoderInterface`");

static PyObject *
TDI_TextEncoderType_encode(tdi_text_encoder_t *self, PyObject *args)
{
    PyObject *value;

    if (!(PyArg_ParseTuple(args, "O", &value)))
        return NULL;

    return tdi_text_encode_unicode(value, self->encoding);
}

PyDoc_STRVAR(TDI_TextEncoderType_escape__doc__,
"escape(self, value)\n\
\n\
:See: `EncoderInterface`");

static PyObject *
TDI_TextEncoderType_escape(tdi_text_encoder_t *self, PyObject *args)
{
    PyObject *value;

    if (!(PyArg_ParseTuple(args, "O", &value)))
        return NULL;

    return tdi_text_encode_escape(value);
}

static struct PyMethodDef TDI_TextEncoderType_methods[] = {
    {"starttag",
     (PyCFunction)TDI_TextEncoderType_starttag,       METH_VARARGS,
     TDI_TextEncoderType_starttag__doc__},

    {"endtag",
     (PyCFunction)TDI_TextEncoderType_endtag,         METH_VARARGS,
     TDI_TextEncoderType_endtag__doc__},

    {"name",
     (PyCFunction)TDI_TextEncoderType_name,           METH_VARARGS,
     TDI_TextEncoderType_name__doc__},

    {"content",
     (PyCFunction)TDI_TextEncoderType_content,        METH_VARARGS,
     TDI_TextEncoderType_content__doc__},

    {"attribute",
     (PyCFunction)TDI_TextEncoderType_attribute,      METH_VARARGS,
     TDI_TextEncoderType_attribute__doc__},

    {"encode",
     (PyCFunction)TDI_TextEncoderType_encode,         METH_VARARGS,
     TDI_TextEncoderType_encode__doc__},

    {"escape",
     (PyCFunction)TDI_TextEncoderType_escape,         METH_VARARGS,
     TDI_TextEncoderType_escape__doc__},

    {NULL, NULL}  /* Sentinel */
};

static int
TDI_TextEncoderType_setencoding(tdi_text_encoder_t *self, PyObject *value,
                                void *closure)
{
    PyObject *encoding = PyObject_Str(value);
    if (!encoding)
        return -1;

    Py_CLEAR(self->encoding);
    self->encoding = encoding;

    return 0;
}

static PyObject *
TDI_TextEncoderType_getencoding(tdi_text_encoder_t *self, void *closure)
{
    return Py_INCREF(self->encoding), self->encoding;
}

static PyGetSetDef TDI_TextEncoderType_getset[] = {
    {"encoding",
     (getter)TDI_TextEncoderType_getencoding,
     (setter)TDI_TextEncoderType_setencoding,
     NULL, NULL},

    {NULL}  /* Sentinel */
};

static PyObject *
TDI_TextEncoderType_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"encoding", NULL};
    PyObject *encoding;
    tdi_text_encoder_t *self;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "S", kwlist, &encoding))
        return NULL;

    if (!(encoding = PyObject_Str(encoding)))
        return NULL;

    if (!(self = GENERIC_ALLOC(type))) {
        Py_DECREF(encoding);
        return NULL;
    }
    self->encoding = encoding;

    return (PyObject *)self;
}

#ifndef TDI_AVOID_GC
static int
TDI_TextEncoderType_traverse(tdi_text_encoder_t *self, visitproc visit,
                             void *arg)
{
    Py_VISIT(self->encoding);

    return 0;
}
#endif

static int
TDI_TextEncoderType_clear(tdi_text_encoder_t *self)
{
    if (self->weakreflist)
        PyObject_ClearWeakRefs((PyObject *)self);

    Py_CLEAR(self->encoding);

    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_TextEncoderType)

PyDoc_STRVAR(TDI_TextEncoderType__doc__,
"``TextEncoder(encoding)``\n\
\n\
Encoder for Text output");

PyTypeObject TDI_TextEncoderType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".TextEncoder",                     /* tp_name */
    sizeof(tdi_text_encoder_t),                         /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_TextEncoderType_dealloc,            /* tp_dealloc */
    0,                                                  /* tp_print */
    0,                                                  /* tp_getattr */
    0,                                                  /* tp_setattr */
    0,                                                  /* tp_compare */
    0,                                                  /* tp_repr */
    0,                                                  /* tp_as_number */
    0,                                                  /* tp_as_sequence */
    0,                                                  /* tp_as_mapping */
    0,                                                  /* tp_hash */
    0,                                                  /* tp_call */
    0,                                                  /* tp_str */
    0,                                                  /* tp_getattro */
    0,                                                  /* tp_setattro */
    0,                                                  /* tp_as_buffer */
    Py_TPFLAGS_HAVE_WEAKREFS                            /* tp_flags */
    | Py_TPFLAGS_HAVE_CLASS
    | Py_TPFLAGS_BASETYPE
    | TDI_IF_GC(Py_TPFLAGS_HAVE_GC),
    TDI_TextEncoderType__doc__,                         /* tp_doc */
    (traverseproc)TDI_IF_GC(TDI_TextEncoderType_traverse), /* tp_traverse */
    (inquiry)TDI_IF_GC(TDI_TextEncoderType_clear),      /* tp_clear */
    0,                                                  /* tp_richcompare */
    offsetof(tdi_text_encoder_t, weakreflist),          /* tp_weaklistoffset */
    0,                                                  /* tp_iter */
    0,                                                  /* tp_iternext */
    TDI_TextEncoderType_methods,                        /* tp_methods */
    0,                                                  /* tp_members */
    TDI_TextEncoderType_getset,                         /* tp_getset */
    0,                                                  /* tp_base */
    0,                                                  /* tp_dict */
    0,                                                  /* tp_descr_get */
    0,                                                  /* tp_descr_set */
    0,                                                  /* tp_dictoffset */
    0,                                                  /* tp_init */
    0,                                                  /* tp_alloc */
    TDI_TextEncoderType_new,                            /* tp_new */
};

/* ------------------- END TDI_TextEncoderType DEFINITION ------------------ */
