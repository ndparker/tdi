/*
 * Copyright 2006 - 2013
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
#include "tdi_content.h"
#include "tdi_globals.h"
#include "tdi_util.h"

#include "obj_node.h"
#include "obj_attr.h"
#include "obj_raw_node.h"
#include "obj_encoder.h"
#include "obj_decoder.h"

/*
 * Object structure for TDI_RawNodeType
 */
typedef struct {
    PyObject_HEAD
    PyObject *weakreflist;

    tdi_node_t *node;  /* Actual node object */
} rawnodeobject;


/* -------------------- BEGIN TDI_RawNodeType DEFINITION ------------------- */

#ifdef METH_COEXIST  /* Python 2.4 optimization */
PyDoc_STRVAR(TDI_RawNodeType_getitem__doc__,
"__getitem__(self, name)\n\
\n\
Determine the raw value of attribute `name`.\n\
\n\
:Return: The attribute (``None`` for shorttags)\n\
:Rtype: ``str``\n\
\n\
:Exceptions:\n\
  - `KeyError` : The attribute does not exist");

/* Forward declaration */
static PyObject *TDI_RawNodeType_getitem(rawnodeobject *, PyObject *);
#endif /* METH_COEXIST */

static struct PyMethodDef TDI_RawNodeType_methods[] = {
#ifdef METH_COEXIST
    {"__getitem__",
     (PyCFunction)TDI_RawNodeType_getitem,  METH_O | METH_COEXIST,
     TDI_RawNodeType_getitem__doc__},
#endif

    {NULL, NULL}  /* Sentinel */
};

static PyObject *
TDI_RawNodeType_getitem(rawnodeobject *self, PyObject *key)
{
    PyObject *normkey;
    tdi_attr_t *item;

    if (!(key = ENCODE_NAME(self->node, key)))
        return NULL;

    if (!PyString_CheckExact(key) && !PyString_Check(key)) {
        PyErr_SetString(TDI_E_ModelError, "attribute key must be a string");
        Py_DECREF(key);
        return NULL;
    }
    normkey = DECODER_NORMALIZE(self->node, key);
    Py_DECREF(key);
    if (!normkey)
        return NULL;

    item = (tdi_attr_t *)PyDict_GetItem(self->node->attr, normkey);
    Py_DECREF(normkey);
    if (!item) {
        PyErr_SetString(PyExc_KeyError, "Attribute not found.");
        return NULL;
    }

    Py_INCREF(item->value);
    return item->value;
}

static int
TDI_RawNodeType_setitem(rawnodeobject *self, PyObject *key, PyObject *value)
{
    PyObject *tmp, *normkey;
    tdi_attr_t *item;
    int subresult;

    if (!(key = ENCODE_NAME(self->node, key)))
        return -1;

    if (!PyString_CheckExact(key) && !PyString_Check(key)) {
        PyErr_SetString(TDI_E_ModelError, "attribute key must be a string");
        Py_DECREF(key);
        return -1;
    }
    if (!(normkey = DECODER_NORMALIZE(self->node, key))) {
        Py_DECREF(key);
        return -1;
    }

    if (!value) {
        subresult = PyDict_DelItem(self->node->attr, normkey);
        if (subresult == -1) {
            if (PyErr_ExceptionMatches(PyExc_KeyError)) {
                PyErr_Clear();
                subresult = 0;
            }
        }
        Py_DECREF(normkey);
        Py_DECREF(key);
        return subresult;
    }

    if (PyUnicode_CheckExact(value) || PyUnicode_Check(value)) {
        if (!(value = ENCODE_UNICODE(self->node, value))) {
            Py_DECREF(normkey);
            Py_DECREF(key);
            return -1;
        }
    }
    else if (!(value = PyObject_Str(value))) {
        Py_DECREF(normkey);
        Py_DECREF(key);
        return -1;
    }

    item = (tdi_attr_t *)PyDict_GetItem(self->node->attr, normkey);
    tmp = tdi_attr_new(item ? item->key : key, value);
    Py_DECREF(value);
    Py_DECREF(key);
    if (!tmp) {
        Py_DECREF(normkey);
        return -1;
    }
    subresult = PyDict_SetItem(self->node->attr, normkey, tmp);
    Py_DECREF(tmp);
    Py_DECREF(normkey);

    return subresult;
}

static PyMappingMethods TDI_RawNodeType_as_mapping = {
    0,                                       /* mp_length */
    (binaryfunc)TDI_RawNodeType_getitem,     /* mp_subscript */
    (objobjargproc)TDI_RawNodeType_setitem,  /* mp_ass_subscript */
};

static PyObject *
TDI_RawNodeType_getcontent(rawnodeobject *self, void *closure)
{
    if (self->node->content) {
        Py_INCREF(self->node->content->clean);
        return self->node->content->clean;
    }

    Py_RETURN_NONE;
}

static int
TDI_RawNodeType_setcontent(rawnodeobject *self, PyObject *value,
                           void *closure)
{
    tdi_content_t *tmp;

    if (!value) {
        PyErr_SetString(PyExc_TypeError,
                        "Cannot delete the content attribute");
        return -1;
    }

    if (PyUnicode_CheckExact(value) || PyUnicode_Check(value)) {
        if (!(value = ENCODE_UNICODE(self->node, value)))
            return -1;
    }
    else if (!(value = PyObject_Str(value))) {
        return -1;
    }

    Py_INCREF(tdi_g_empty_dict);
    Py_CLEAR(self->node->namedict);
    self->node->namedict = tdi_g_empty_dict;
    tmp = self->node->content;
    self->node->content = NULL;
    if (!tmp) {
        tmp = tdi_content_new();
    }
    else {
        Py_CLEAR(tmp->clean);
        Py_CLEAR(tmp->with_escapes);
    }
    tmp->clean = value;
    Py_INCREF(value);
    tmp->with_escapes = value;
    self->node->content = tmp;

    return 0;
}

static PyObject *
TDI_RawNodeType_getencoder(rawnodeobject *self, void *closure)
{
    tdi_encoder_t *wrapper = self->node->encoder;

    if (wrapper) {
        Py_INCREF(wrapper->encoder);
        return wrapper->encoder;
    }

    Py_RETURN_NONE;
}

static PyObject *
TDI_RawNodeType_getdecoder(rawnodeobject *self, void *closure)
{
    tdi_decoder_t *wrapper = self->node->decoder;

    if (wrapper) {
        Py_INCREF(wrapper->decoder);
        return wrapper->decoder;
    }

    Py_RETURN_NONE;
}

static PyGetSetDef TDI_RawNodeType_getset[] = {
    {"content",
     (getter)TDI_RawNodeType_getcontent,
     (setter)TDI_RawNodeType_setcontent,
     PyDoc_STR(
"Raw content\n\
\n\
:Type: ``str``"),
    NULL},

    {"encoder",
     (getter)TDI_RawNodeType_getencoder,
     NULL,
     PyDoc_STR(
"Output encoder\n\
\n\
:Type: `EncoderInterface`"),
     NULL},

    {"decoder",
     (getter)TDI_RawNodeType_getdecoder,
     NULL,
     PyDoc_STR(
"Input decoder\n\
\n\
:Type: `DecoderInterface`"),
     NULL},

    {NULL}  /* Sentinel */
};

static int
TDI_RawNodeType_traverse(rawnodeobject *self, visitproc visit, void *arg)
{
    Py_VISIT((PyObject *)self->node);
    return 0;
}

static int
TDI_RawNodeType_clear(rawnodeobject *self)
{
    if (self->weakreflist)
        PyObject_ClearWeakRefs((PyObject *)self);
    Py_CLEAR(self->node);
    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_RawNodeType)

PyDoc_STRVAR(TDI_RawNodeType__doc__,
"Lightweight node for raw content and attribute assignment");

PyTypeObject TDI_RawNodeType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".RawNode",                         /* tp_name */
    sizeof(rawnodeobject),                              /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_RawNodeType_dealloc,                /* tp_dealloc */
    0,                                                  /* tp_print */
    0,                                                  /* tp_getattr */
    0,                                                  /* tp_setattr */
    0,                                                  /* tp_compare */
    0,                                                  /* tp_repr */
    0,                                                  /* tp_as_number */
    0,                                                  /* tp_as_sequence */
    &TDI_RawNodeType_as_mapping,                        /* tp_as_mapping */
    0,                                                  /* tp_hash */
    0,                                                  /* tp_call */
    0,                                                  /* tp_str */
    0,                                                  /* tp_getattro */
    0,                                                  /* tp_setattro */
    0,                                                  /* tp_as_buffer */
    Py_TPFLAGS_HAVE_WEAKREFS                            /* tp_flags */
    | Py_TPFLAGS_HAVE_CLASS
    | Py_TPFLAGS_HAVE_GC,
    TDI_RawNodeType__doc__,                             /* tp_doc */
    (traverseproc)TDI_RawNodeType_traverse,             /* tp_traverse */
    (inquiry)TDI_RawNodeType_clear,                     /* tp_clear */
    0,                                                  /* tp_richcompare */
    offsetof(rawnodeobject, weakreflist),               /* tp_weaklistoffset */
    0,                                                  /* tp_iter */
    0,                                                  /* tp_iternext */
    TDI_RawNodeType_methods,                            /* tp_methods */
    0,                                                  /* tp_members */
    TDI_RawNodeType_getset                              /* tp_getset */
};

/* --------------------- END TDI_RawNodeType DEFINITION -------------------- */

/*
 * Allocate new TDI_RawNodeType and initialize from TDI_NodeType
 */
PyObject *
tdi_raw_node_new(tdi_node_t *node)
{
    rawnodeobject *self;

    if (!(self = GENERIC_ALLOC(&TDI_RawNodeType)))
        return NULL;

    Py_INCREF(node);
    self->node = node;

    return (PyObject *)self;
}
