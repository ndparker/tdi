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

#include "tdi.h"
#include "tdi_util.h"

#include "obj_avoid_gc.h"
#include "obj_text_decoder.h"


PyObject *
tdi_text_decoder_normalize(PyObject *name)
{
    return Py_INCREF(name), name;
}

#define U(c) ((Py_UNICODE)(c))

static PyObject *
decode(PyObject *value, PyObject *encoding, PyObject *errors)
{
    const char *encoding_s, *errors_s;

    if (!(encoding_s = PyString_AsString(encoding)))
        return NULL;
    if (errors) {
        if (!(errors_s = PyString_AsString(errors)))
            return NULL;
    }
    else {
        errors_s = "strict";
    }

    return PyUnicode_FromEncodedObject(value, encoding_s, errors_s);
}

static PyObject *
attribute(PyObject *value, PyObject *encoding, PyObject *errors)
{
    PyObject *result;
    Py_UNICODE *source, *sentinel, *target;
    Py_ssize_t length, olength;
    Py_UNICODE c;

    if (!(value = decode(value, encoding, errors)))
        return NULL;

    length = PyUnicode_GET_SIZE(value);
    if (length == 0)
        return value;
    source = PyUnicode_AS_UNICODE(value);
    if (*source == U('"') || *source == U('\'')) {
        if (length <=2) {
            Py_DECREF(value);
            return PyUnicode_DecodeASCII("", 0, "strict");
        }
        ++source;
        length -= 2;
    }

    if (!(result = PyUnicode_FromUnicode(NULL, length))) {
        Py_DECREF(value);
        return NULL;
    }

    sentinel = source + length;
    target = PyUnicode_AS_UNICODE(result);
    olength = length;

    while (source < sentinel) {
        if ((c = *source++) != U('\\') || !(source < sentinel)) {
            *target++ = c;
        }
        else {
            *target++ = *source++;
            --length;
        }
    }
    Py_DECREF(value);

    if (olength != length && (PyUnicode_Resize(&result, length) == -1)) {
        Py_DECREF(result);
        return NULL;
    }

    return result;
}

/* ------------------ BEGIN TDI_TextDecoderType DEFINITION ----------------- */

PyDoc_STRVAR(TDI_TextDecoderType_normalize__doc__,
"normalize(self, name)\n\
\n\
:See: `DecoderInterface`");

static PyObject *
TDI_TextDecoderType_normalize(tdi_text_decoder_t *self, PyObject *args,
                              PyObject *kwds)
{
    PyObject *name;
    static char *kwlist[] = {"name", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", kwlist,
                                     &name))
        return NULL;

    return Py_INCREF(name), name;
}


PyDoc_STRVAR(TDI_TextDecoderType_decode__doc__,
"decode(self, value, errors='strict')\n\
\n\
:See: `DecoderInterface`");

static PyObject *
TDI_TextDecoderType_decode(tdi_text_decoder_t *self, PyObject *args,
                           PyObject *kwds)
{
    PyObject *value, *errors = NULL;
    static char *kwlist[] = {"value", "errors", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|S", kwlist,
                                     &value, &errors))
        return NULL;

    return decode(value, self->encoding, errors);
}


PyDoc_STRVAR(TDI_TextDecoderType_attribute__doc__,
"attribute(self, value, errors='strict')\n\
\n\
:See: `DecoderInterface`");

static PyObject *
TDI_TextDecoderType_attribute(tdi_text_decoder_t *self, PyObject *args,
                              PyObject *kwds)
{
    PyObject *value, *errors = NULL;
    static char *kwlist[] = {"value", "errors", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|S", kwlist,
                                     &value, &errors))
        return NULL;

    return attribute(value, self->encoding, errors);
}


static struct PyMethodDef TDI_TextDecoderType_methods[] = {
    {"normalize",
     (PyCFunction)TDI_TextDecoderType_normalize,      METH_KEYWORDS,
     TDI_TextDecoderType_normalize__doc__},

    {"decode",
     (PyCFunction)TDI_TextDecoderType_decode,         METH_KEYWORDS,
     TDI_TextDecoderType_decode__doc__},

    {"attribute",
     (PyCFunction)TDI_TextDecoderType_attribute,      METH_KEYWORDS,
     TDI_TextDecoderType_attribute__doc__},

    {NULL, NULL}  /* Sentinel */
};

static int
TDI_TextDecoderType_setencoding(tdi_text_decoder_t *self, PyObject *value,
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
TDI_TextDecoderType_getencoding(tdi_text_decoder_t *self, void *closure)
{
    return Py_INCREF(self->encoding), self->encoding;
}

static PyGetSetDef TDI_TextDecoderType_getset[] = {
    {"encoding",
     (getter)TDI_TextDecoderType_getencoding,
     (setter)TDI_TextDecoderType_setencoding,
     NULL, NULL},

    {NULL}  /* Sentinel */
};

static PyObject *
TDI_TextDecoderType_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"encoding", NULL};
    PyObject *encoding;
    tdi_text_decoder_t *self;

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
TDI_TextDecoderType_traverse(tdi_text_decoder_t *self, visitproc visit,
                             void *arg)
{
    Py_VISIT(self->encoding);

    return 0;
}
#endif

static int
TDI_TextDecoderType_clear(tdi_text_decoder_t *self)
{
    if (self->weakreflist)
        PyObject_ClearWeakRefs((PyObject *)self);

    Py_CLEAR(self->encoding);

    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_TextDecoderType)

PyDoc_STRVAR(TDI_TextDecoderType__doc__,
"``TextDecoder(encoding)``\n\
\n\
Decoder for text input");

PyTypeObject TDI_TextDecoderType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".TextDecoder",                     /* tp_name */
    sizeof(tdi_text_decoder_t),                         /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_TextDecoderType_dealloc,            /* tp_dealloc */
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
    TDI_TextDecoderType__doc__,                         /* tp_doc */
    (traverseproc)TDI_IF_GC(TDI_TextDecoderType_traverse), /* tp_traverse */
    (inquiry)TDI_IF_GC(TDI_TextDecoderType_clear),      /* tp_clear */
    0,                                                  /* tp_richcompare */
    offsetof(tdi_text_decoder_t, weakreflist),          /* tp_weaklistoffset */
    0,                                                  /* tp_iter */
    0,                                                  /* tp_iternext */
    TDI_TextDecoderType_methods,                        /* tp_methods */
    0,                                                  /* tp_members */
    TDI_TextDecoderType_getset,                         /* tp_getset */
    0,                                                  /* tp_base */
    0,                                                  /* tp_dict */
    0,                                                  /* tp_descr_get */
    0,                                                  /* tp_descr_set */
    0,                                                  /* tp_dictoffset */
    0,                                                  /* tp_init */
    0,                                                  /* tp_alloc */
    TDI_TextDecoderType_new,                            /* tp_new */
};

/* ------------------- END TDI_TextDecoderType DEFINITION ------------------ */
