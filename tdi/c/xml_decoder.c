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

#include "htmldecode.h"
#include "obj_avoid_gc.h"
#include "obj_xml_decoder.h"


PyObject *
tdi_xml_decoder_normalize(PyObject *name)
{
    return Py_INCREF(name), name;
}


/* ------------------- BEGIN TDI_XMLDecoderType DEFINITION ----------------- */

PyDoc_STRVAR(TDI_XMLDecoderType_normalize__doc__,
"normalize(self, name)\n\
\n\
:See: `DecoderInterface`");

static PyObject *
TDI_XMLDecoderType_normalize(tdi_xml_decoder_t *self, PyObject *args,
                             PyObject *kwds)
{
    PyObject *name;
    static char *kwlist[] = {"name", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", kwlist,
                                     &name))
        return NULL;

    return Py_INCREF(name), name;
}


PyDoc_STRVAR(TDI_XMLDecoderType_decode__doc__,
"decode(self, value, errors='strict')\n\
\n\
:See: `DecoderInterface`");

static PyObject *
TDI_XMLDecoderType_decode(tdi_xml_decoder_t *self, PyObject *args,
                          PyObject *kwds)
{
    PyObject *value, *errors = NULL;
    static char *kwlist[] = {"value", "errors", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|S", kwlist,
                                     &value, &errors))
        return NULL;

    return tdi_htmldecode(value, self->encoding, errors, NULL, 0);
}


PyDoc_STRVAR(TDI_XMLDecoderType_attribute__doc__,
"attribute(self, value, errors='strict')\n\
\n\
:See: `DecoderInterface`");

static PyObject *
TDI_XMLDecoderType_attribute(tdi_xml_decoder_t *self, PyObject *args,
                             PyObject *kwds)
{
    PyObject *value, *errors = NULL;
    static char *kwlist[] = {"value", "errors", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|S", kwlist,
                                     &value, &errors))
        return NULL;

    return tdi_htmldecode(value, self->encoding, errors, NULL, 1);
}


static struct PyMethodDef TDI_XMLDecoderType_methods[] = {
    {"normalize",
     (PyCFunction)TDI_XMLDecoderType_normalize,       METH_KEYWORDS,
     TDI_XMLDecoderType_normalize__doc__},

    {"decode",
     (PyCFunction)TDI_XMLDecoderType_decode,          METH_KEYWORDS,
     TDI_XMLDecoderType_decode__doc__},

    {"attribute",
     (PyCFunction)TDI_XMLDecoderType_attribute,       METH_KEYWORDS,
     TDI_XMLDecoderType_attribute__doc__},

    {NULL, NULL}  /* Sentinel */
};

static int
TDI_XMLDecoderType_setencoding(tdi_xml_decoder_t *self, PyObject *value,
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
TDI_XMLDecoderType_getencoding(tdi_xml_decoder_t *self, void *closure)
{
    return Py_INCREF(self->encoding), self->encoding;
}

static PyGetSetDef TDI_XMLDecoderType_getset[] = {
    {"encoding",
     (getter)TDI_XMLDecoderType_getencoding,
     (setter)TDI_XMLDecoderType_setencoding,
     NULL, NULL},

    {NULL}  /* Sentinel */
};

static PyObject *
TDI_XMLDecoderType_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"encoding", NULL};
    PyObject *encoding;
    tdi_xml_decoder_t *self;

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
TDI_XMLDecoderType_traverse(tdi_xml_decoder_t *self, visitproc visit,
                            void *arg)
{
    Py_VISIT(self->encoding);

    return 0;
}
#endif

static int
TDI_XMLDecoderType_clear(tdi_xml_decoder_t *self)
{
    if (self->weakreflist)
        PyObject_ClearWeakRefs((PyObject *)self);

    Py_CLEAR(self->encoding);

    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_XMLDecoderType)

PyDoc_STRVAR(TDI_XMLDecoderType__doc__,
"``XMLDecoder(encoding)``\n\
\n\
Decoder for XML input");

PyTypeObject TDI_XMLDecoderType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".XMLDecoder",                      /* tp_name */
    sizeof(tdi_xml_decoder_t),                          /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_XMLDecoderType_dealloc,             /* tp_dealloc */
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
    TDI_XMLDecoderType__doc__,                          /* tp_doc */
    (traverseproc)TDI_IF_GC(TDI_XMLDecoderType_traverse), /* tp_traverse */
    (inquiry)TDI_IF_GC(TDI_XMLDecoderType_clear),       /* tp_clear */
    0,                                                  /* tp_richcompare */
    offsetof(tdi_xml_decoder_t, weakreflist),           /* tp_weaklistoffset */
    0,                                                  /* tp_iter */
    0,                                                  /* tp_iternext */
    TDI_XMLDecoderType_methods,                         /* tp_methods */
    0,                                                  /* tp_members */
    TDI_XMLDecoderType_getset,                          /* tp_getset */
    0,                                                  /* tp_base */
    0,                                                  /* tp_dict */
    0,                                                  /* tp_descr_get */
    0,                                                  /* tp_descr_set */
    0,                                                  /* tp_dictoffset */
    0,                                                  /* tp_init */
    0,                                                  /* tp_alloc */
    TDI_XMLDecoderType_new,                             /* tp_new */
};

/* -------------------- END TDI_XMLDecoderType DEFINITION ------------------ */
