/*
 * Copyright 2006 - 2014
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
#include "tdi_overlay.h"
#include "tdi_scope.h"
#include "tdi_util.h"

#include "obj_avoid_gc.h"
#include "obj_node.h"
#include "obj_template_node.h"
#include "obj_attr.h"


/* ----------------- BEGIN TDI_TemplateNodeType DEFINITION ----------------- */

PyDoc_STRVAR(TDI_TemplateNodeType_append_text__doc__,
"append_text(self, content)\n\
\n\
Append a text node\n\
\n\
:Parameters:\n\
  `content` : ``str``\n\
    The text node content\n\
\n\
:Exceptions:\n\
  - `NodeTreeError` : The tree was already finalized");

static PyObject *
TDI_TemplateNodeType_append_text(tdi_node_t *self, PyObject *args,
                                 PyObject *kwds)
{
    static char *kwlist[] = {"content", NULL};
    PyObject *content, *node;
    int subresult;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "S", kwlist, &content))
        return NULL;

    if (self->flags & NODE_FINALIZED) {
        PyErr_SetString(TDI_E_NodeTreeError, "Tree was already finalized");
        return NULL;
    }

    if (!(node = tdi_template_node_text_new(content)))
        return NULL;
    subresult = PyList_Append(self->nodes, node);
    Py_DECREF(node);
    if (subresult == -1)
        return NULL;

    Py_RETURN_NONE;
}

PyDoc_STRVAR(TDI_TemplateNodeType_append_escape__doc__,
"append_escape(self, escaped, content)\n\
\n\
Append an escaped node\n\
\n\
:Parameters:\n\
  `escaped` : ``str``\n\
    The escaped string (in unescaped form, i.e. the final result)\n\
\n\
  `content` : ``str``\n\
    The escape string (the whole sequence)\n\
\n\
:Exceptions:\n\
  - `NodeTreeError` : The tree was already finalized");

static PyObject *
TDI_TemplateNodeType_append_escape(tdi_node_t *self, PyObject *args,
                                   PyObject *kwds)
{
    static char *kwlist[] = {"escaped", "content", NULL};
    PyObject *escaped, *content, *node;
    int subresult;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "SS", kwlist,
                                     &escaped, &content))
        return NULL;

    if (self->flags & NODE_FINALIZED) {
        PyErr_SetString(TDI_E_NodeTreeError, "Tree was already finalized");
        return NULL;
    }

    if (!(node = tdi_template_node_escaped_text_new(escaped, content)))
        return NULL;
    subresult = PyList_Append(self->nodes, node);
    Py_DECREF(node);
    if (subresult == -1)
        return NULL;

    Py_RETURN_NONE;
}

PyDoc_STRVAR(TDI_TemplateNodeType_append_node__doc__,
"append_node(tagname, attr, special)\n\
\n\
Append processable node\n\
\n\
:Parameters:\n\
  `tagname` : ``str``\n\
    The name of the accompanying tag\n\
\n\
  `attr` : iterable\n\
    The attribute list (``((name, value), ...)``)\n\
\n\
  `special` : ``dict``\n\
    Special attributes. If it's empty, something's wrong.\n\
\n\
:Return: new `TemplateNode` instance\n\
:Rtype: `TemplateNode`\n\
\n\
:Exceptions:\n\
  - `NodeTreeError` : The tree was already finalized\n\
  - `AssertionError` : nothing special\n");

static PyObject *
TDI_TemplateNodeType_append_node(tdi_node_t *self, PyObject *args,
                                 PyObject *kwds)
{
    static char *kwlist[] = {"tagname", "attr", "special", "closed", NULL};
    PyObject *tagname, *attr, *special, *closed;
    tdi_node_t *node;
    Py_ssize_t size;
    int is_closed;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "SOOO", kwlist,
                                     &tagname, &attr, &special, &closed))
        return NULL;

    if (self->flags & NODE_FINALIZED) {
        PyErr_SetString(TDI_E_NodeTreeError, "Tree was already finalized");
        return NULL;
    }

    if ((size = PyObject_Length(special)) == -1)
        return NULL;
    if (size == 0) {
        PyErr_SetString(PyExc_AssertionError,
                        "Nothing special about this node.");
        return NULL;
    }
    if ((is_closed = PyObject_IsTrue(closed)) == -1) {
        return NULL;
    }

    node = (tdi_node_t *)tdi_template_node_template_new(tagname, attr,
                                                        special, is_closed);
    if (!node)
        return NULL;

    if (PyList_Append(self->nodes, (PyObject *)node) == -1) {
        Py_DECREF(node);
        return NULL;
    }

    return (PyObject *)node;
}

static struct PyMethodDef TDI_TemplateNodeType_methods[] = {
    {"append_text",
     (PyCFunction)TDI_TemplateNodeType_append_text, METH_KEYWORDS,
     TDI_TemplateNodeType_append_text__doc__},

    {"append_escape",
     (PyCFunction)TDI_TemplateNodeType_append_escape, METH_KEYWORDS,
     TDI_TemplateNodeType_append_escape__doc__},

    {"append_node",
     (PyCFunction)TDI_TemplateNodeType_append_node, METH_KEYWORDS,
     TDI_TemplateNodeType_append_node__doc__},

    {NULL, NULL}  /* Sentinel */
};

static PyObject *
TDI_TemplateNodeType_getendtag(tdi_node_t *self, void *closure)
{
    if (self->endtag) {
        Py_INCREF(self->endtag);
        return self->endtag;
    }

    Py_RETURN_NONE;
}

static int
TDI_TemplateNodeType_setendtag(tdi_node_t *self, PyObject *value,
                               void *closure)
{
    if (!value) {
        PyErr_SetString(PyExc_TypeError,
                        "Cannot delete the endtag attribute");
        return -1;
    }

    if (self->flags & NODE_FINALIZED) {
        PyErr_SetString(TDI_E_NodeTreeError, "Tree was already finalized");
        return -1;
    }
    if (self->flags & NODE_CLOSED) {
        PyErr_SetString(TDI_E_NodeTreeError, "Self-closing elements cannot "
                                             "have an endtag");
        return -1;
    }
    if (!PyString_CheckExact(value) && !PyString_Check(value)) {
        PyErr_SetString(TDI_E_NodeTreeError, "Endtag data must be a string");
        return -1;
    }

    Py_INCREF(value);
    Py_CLEAR(self->endtag);
    self->endtag = value;

    return 0;
}

static PyGetSetDef TDI_TemplateNodeType_getset[] = {
    {"endtag",
     (getter)TDI_TemplateNodeType_getendtag,
     (setter)TDI_TemplateNodeType_setendtag,
     PyDoc_STR(
"End tag of the node\n\
\n\
:Type: ``str``"),
     NULL},

    {NULL}  /* Sentinel */
};

#ifndef TDI_AVOID_GC
static int
TDI_TemplateNodeType_traverse(tdi_node_t *self, visitproc visit,
                              void *arg)
{
    TDI_CONTENT_VISIT(self->content);
    if (self->kind != TEXT_NODE) {
        Py_VISIT(self->sep);
        Py_VISIT(self->nodes);
        Py_VISIT(self->namedict);
        Py_VISIT(self->tagname);
        Py_VISIT(self->attr);
        Py_VISIT(self->endtag);
        Py_VISIT(self->name);
        Py_VISIT(self->modelscope);
        Py_VISIT((PyObject *)self->encoder);
        Py_VISIT((PyObject *)self->decoder);
        Py_VISIT(self->complete);
        TDI_SCOPE_VISIT(self->scope);
        TDI_OVERLAY_VISIT(self->overlay);
    }

    return 0;
}
#endif

static int
TDI_TemplateNodeType_clear(tdi_node_t *self)
{
    if (self->weakreflist)
        PyObject_ClearWeakRefs((PyObject *)self);
    TDI_CONTENT_CLEAR(self->content);
    if (self->kind != TEXT_NODE) {
        Py_CLEAR(self->sep);
        Py_CLEAR(self->nodes);
        Py_CLEAR(self->namedict);
        Py_CLEAR(self->tagname);
        Py_CLEAR(self->attr);
        Py_CLEAR(self->endtag);
        Py_CLEAR(self->name);
        Py_CLEAR(self->modelscope);
        Py_CLEAR(self->encoder);
        Py_CLEAR(self->decoder);
        Py_CLEAR(self->complete);
        TDI_SCOPE_CLEAR(self->scope);
        TDI_OVERLAY_CLEAR(self->overlay);
    }

    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_TemplateNodeType)

PyDoc_STRVAR(TDI_TemplateNodeType__doc__,
"Template node\n\
\n\
This is kind of a proto node. During rendering each template node is\n\
turned into a user visible `Node` object, which implements the user\n\
interface. `TemplateNode` objects provide a tree building interface\n\
instead.\n\
\n\
Template nodes cannot be created directly, you have to use\n\
`Root.append_node` or `TemplateNode.append_node`.");

PyTypeObject TDI_TemplateNodeType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".TemplateNode",                    /* tp_name */
    sizeof(tdi_node_t),                                 /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_TemplateNodeType_dealloc,           /* tp_dealloc */
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
    TDI_TemplateNodeType__doc__,                        /* tp_doc */
    (traverseproc)TDI_IF_GC(TDI_TemplateNodeType_traverse), /* tp_traverse */
    (inquiry)TDI_IF_GC(TDI_TemplateNodeType_clear),     /* tp_clear */
    0,                                                  /* tp_richcompare */
    offsetof(tdi_node_t, weakreflist),                  /* tp_weaklistoffset */
    0,                                                  /* tp_iter */
    0,                                                  /* tp_iternext */
    TDI_TemplateNodeType_methods,                       /* tp_methods */
    0,                                                  /* tp_members */
    TDI_TemplateNodeType_getset                         /* tp_getset */
};

/* ------------------ END TDI_TemplateNodeType DEFINITION ------------------ */


static int
load_attributes(tdi_node_t *self, PyObject *attr)
{
    PyObject *item, *tuple, *key, *value, *cobject;
    int res;

    if (!(self->attr = PyList_New(0)))
        return -1;
    self->flags |= NODE_NEWATTR;

    if (!(attr = PyObject_GetIter(attr)))
        return -1;

    for (; (item = PyIter_Next(attr));) {
        tuple = PyObject_GetIter(item);
        Py_DECREF(item);
        if (!tuple)
            goto error_attr;
        if (!(key = PyIter_Next(tuple)))
            goto error_tuple;
        if (!(value = PyIter_Next(tuple))) {
            Py_DECREF(key);
            goto error_tuple;
        }
        if ((item = PyIter_Next(tuple))) {
            Py_DECREF(value);
            Py_DECREF(key);
            Py_DECREF(item);
            goto error_tuple;
        }
        Py_DECREF(tuple);
        if (PyErr_Occurred()) {
            Py_DECREF(value);
            Py_DECREF(key);
            goto error_attr;
        }

        if (!PyString_CheckExact(key) && !PyString_Check(key)) {
            PyErr_SetString(PyExc_TypeError,
                            "attribute keys must be strings");
            Py_DECREF(value);
            Py_DECREF(key);
            goto error_attr;
        }
        if (value != Py_None && !PyString_CheckExact(value) &&
            !PyString_Check(value)) {
            PyErr_SetString(PyExc_TypeError,
                            "attribute values must be strings or None");
            Py_DECREF(value);
            Py_DECREF(key);
            goto error_attr;
        }

        cobject = tdi_attr_new(key, value);
        Py_DECREF(value);
        Py_DECREF(key);
        if (!cobject)
            goto error_attr;

        res = PyList_Append(self->attr, cobject);
        Py_DECREF(cobject);
        if (res == -1)
            goto error_attr;
    }
    if (PyErr_Occurred())
        goto error_attr;
    Py_DECREF(attr);
    return 0;

error_tuple:
    if (!PyErr_Occurred())
        PyErr_SetString(PyExc_TypeError,
                        "attr should be a sequence of 2-tuples");
    Py_DECREF(tuple);
error_attr:
    Py_DECREF(attr);
    return -1;
}


/*
 * Parse special attribute
 */
static int
special_attribute(PyObject *special, PyObject **name, int *noelement,
                  int *sep, int *noauto)
{
    PyObject *tmp, *tuple, *item;
    Py_ssize_t size;

    if (!(tmp = PyString_FromString("attribute")))
        goto error;
    tuple = PyObject_GetItem(special, tmp);
    Py_DECREF(tmp);
    if (!tuple) {
        if (PyErr_Occurred()) {
            if (!PyErr_ExceptionMatches(PyExc_KeyError))
                return -1;
            PyErr_Clear();
        }
        *name = NULL;
        *noelement = 0;
        *sep = 0;
        *noauto = 0;
        return 0;
    }
    else if (tuple == Py_None) {
        Py_DECREF(tuple);
        *name = NULL;
        *noelement = 0,
        *sep = 0;
        *noauto = 0;
        return 0;
    }

    tmp = PyObject_GetIter(tuple);
    Py_DECREF(tuple);
    if (!tmp)
        return -1;
    tuple = tmp;
    if (!(item = PyIter_Next(tuple))) {
        if (!PyErr_Occurred())
            PyErr_SetString(PyExc_ValueError, "Expected a 2-tuple");
        goto error_tuple;
    }
    if (!(tmp = PyString_FromString("-")))
        goto error_item;
    if ((*noelement = PySequence_Contains(item, tmp)) == -1)
        goto error_tmp;
    Py_DECREF(tmp);

    if (!(tmp = PyString_FromString(":")))
        goto error_item;
    if ((*sep = PySequence_Contains(item, tmp)) == -1)
        goto error_tmp;
    Py_DECREF(tmp);

    if (!(tmp = PyString_FromString("*")))
        goto error_item;
    if ((*noauto = PySequence_Contains(item, tmp)) == -1)
        goto error_tmp;
    Py_DECREF(tmp);
    Py_DECREF(item);

    if (!(item = PyIter_Next(tuple))) {
        if (!PyErr_Occurred())
            PyErr_SetString(PyExc_ValueError, "Expected a 2-tuple");
        goto error_tuple;
    }

    if (item == Py_None) {
        Py_DECREF(item);
        *name = NULL;
    }
    else {
        if ((size = PyString_Size(item)) == -1)
            goto error_item;
        else if (size == 0) {
            Py_DECREF(item);
            *name = NULL;
        }
        else {
            if (!(*name = PyObject_Str(item)))
                goto error_item;
            Py_DECREF(item);
        }
    }

    item = PyIter_Next(tuple);
    Py_DECREF(tuple);
    if (item) {
        PyErr_SetString(PyExc_ValueError, "Expected a 2-tuple");
        Py_XDECREF(*name);
        Py_DECREF(item);
        goto error;
    }
    else if (PyErr_Occurred()) {
        Py_XDECREF(*name);
        goto error;
    }

    return 0;

error_tmp:
    Py_DECREF(tmp);
error_item:
    Py_DECREF(item);
error_tuple:
    Py_DECREF(tuple);
error:
    return -1;
}


/*
 * Parse special overlay
 */
static int
special_overlay(PyObject *special, tdi_overlay_t **overlay)
{
    PyObject *tmp, *tuple, *item, *name;
    Py_ssize_t size;
    int noelement, source, target;

    if (!(tmp = PyString_FromString("overlay")))
        goto error;
    tuple = PyObject_GetItem(special, tmp);
    Py_DECREF(tmp);
    if (!tuple) {
        if (PyErr_Occurred()) {
            if (!PyErr_ExceptionMatches(PyExc_KeyError))
                return -1;
            PyErr_Clear();
        }
        *overlay = NULL;
        return 0;
    }
    else if (tuple == Py_None) {
        Py_DECREF(tuple);
        *overlay = NULL;
        return 0;
    }

    tmp = PyObject_GetIter(tuple);
    Py_DECREF(tuple);
    if (!tmp)
        return -1;
    tuple = tmp;
    if (!(item = PyIter_Next(tuple))) {
        if (!PyErr_Occurred())
            PyErr_SetString(PyExc_ValueError, "Expected a 2-tuple");
        goto error_tuple;
    }
    if (!(tmp = PyString_FromString("-")))
        goto error_item;
    if ((noelement = PySequence_Contains(item, tmp)) == -1)
        goto error_tmp;
    Py_DECREF(tmp);

    if (!(tmp = PyString_FromString("<")))
        goto error_item;
    if ((source = PySequence_Contains(item, tmp)) == -1)
        goto error_tmp;
    Py_DECREF(tmp);

    if (!(tmp = PyString_FromString(">")))
        goto error_item;
    if ((target = PySequence_Contains(item, tmp)) == -1)
        goto error_tmp;
    Py_DECREF(tmp);
    Py_DECREF(item);

    if (!(item = PyIter_Next(tuple))) {
        if (!PyErr_Occurred())
            PyErr_SetString(PyExc_ValueError, "Expected a 2-tuple");
        goto error_tuple;
    }

    if (!PyString_Check(item)) {
        PyErr_SetString(PyExc_TypeError, "Expected str overlay name");
        goto error_item;
    }
    if ((size = PyString_Size(item)) == -1)
        goto error_item;
    else if (size == 0) {
        PyErr_SetString(PyExc_TypeError,
                        "Expected non-empty str overlay name");
        goto error_item;
    }
    if (!(name = PyObject_Str(item)))
        goto error_item;
    Py_DECREF(item);

    item = PyIter_Next(tuple);
    Py_DECREF(tuple);
    if (item) {
        PyErr_SetString(PyExc_ValueError, "Expected a 2-tuple");
        Py_DECREF(name);
        Py_DECREF(item);
        goto error;
    }
    else if (PyErr_Occurred()) {
        Py_DECREF(name);
        goto error;
    }

    if (!(*overlay = tdi_overlay_new(name, noelement, source, target)))
        return -1;
    return 0;

error_tmp:
    Py_DECREF(tmp);
error_item:
    Py_DECREF(item);
error_tuple:
    Py_DECREF(tuple);
error:
    return -1;
}


/*
 * Parse special scope
 */
static int
special_scope(PyObject *special, tdi_scope_t **scope)
{
    PyObject *tmp, *tuple, *item, *name;
    Py_ssize_t size;
    int noelement, absolute;

    if (!(tmp = PyString_FromString("scope")))
        goto error;
    tuple = PyObject_GetItem(special, tmp);
    Py_DECREF(tmp);
    if (!tuple) {
        if (PyErr_Occurred()) {
            if (!PyErr_ExceptionMatches(PyExc_KeyError))
                return -1;
            PyErr_Clear();
        }
        *scope = NULL;
        return 0;
    }
    else if (tuple == Py_None) {
        Py_DECREF(tuple);
        *scope = NULL;
        return 0;
    }

    tmp = PyObject_GetIter(tuple);
    Py_DECREF(tuple);
    if (!tmp)
        return -1;
    tuple = tmp;
    if (!(item = PyIter_Next(tuple))) {
        if (!PyErr_Occurred())
            PyErr_SetString(PyExc_ValueError, "Expected a 2-tuple");
        goto error_tuple;
    }
    if (!(tmp = PyString_FromString("-")))
        goto error_item;
    if ((noelement = PySequence_Contains(item, tmp)) == -1)
        goto error_tmp;
    Py_DECREF(tmp);

    if (!(tmp = PyString_FromString("=")))
        goto error_item;
    if ((absolute = PySequence_Contains(item, tmp)) == -1)
        goto error_tmp;
    Py_DECREF(tmp);
    Py_DECREF(item);

    if (!(item = PyIter_Next(tuple))) {
        if (!PyErr_Occurred())
            PyErr_SetString(PyExc_ValueError, "Expected a 2-tuple");
        goto error_tuple;
    }

    if (!PyString_Check(item)) {
        PyErr_SetString(PyExc_TypeError, "Expected str scope name");
        goto error_item;
    }
    if ((size = PyString_Size(item)) == -1)
        goto error_item;
    if (!(name = PyObject_Str(item)))
        goto error_item;
    Py_DECREF(item);

    item = PyIter_Next(tuple);
    Py_DECREF(tuple);
    if (item) {
        PyErr_SetString(PyExc_ValueError, "Expected a 2-tuple");
        Py_DECREF(name);
        Py_DECREF(item);
        goto error;
    }
    else if (PyErr_Occurred()) {
        Py_DECREF(name);
        goto error;
    }
    if (size == 0 && !noelement && !absolute) {
        Py_DECREF(name);
        *scope = NULL;
        return 0;
    }

    if (!(*scope = tdi_scope_new(name, noelement, absolute)))
        return -1;
    return 0;

error_tmp:
    Py_DECREF(tmp);
error_item:
    Py_DECREF(item);
error_tuple:
    Py_DECREF(tuple);
error:
    *scope = NULL;
    return -1;
}


/*
 * Allocate new TDI_TemplateNodeType and initialize as proc node
 */
PyObject *
tdi_template_node_template_new(PyObject *tagname, PyObject *attr,
                               PyObject *special, int is_closed)
{
    PyObject *name;
    tdi_node_t *self;
    tdi_overlay_t *overlay;
    tdi_scope_t *scope = NULL;
    int res, noelement, separator, noauto;

    Py_INCREF(special);
    res = special_attribute(special, &name, &noelement, &separator, &noauto);
    if (res == -1) {
        Py_DECREF(special);
        return NULL;
    }

    res = special_overlay(special, &overlay);
    if (res == -1) {
        Py_DECREF(special);
        Py_XDECREF(name);
        return NULL;
    }

    res = special_scope(special, &scope);
    Py_DECREF(special);
    if (res == -1) {
        TDI_OVERLAY_CLEAR(overlay);
        Py_XDECREF(name);
        return NULL;
    }

    if (!(tagname = PyObject_Str(tagname))) {
        TDI_SCOPE_CLEAR(scope);
        TDI_OVERLAY_CLEAR(overlay);
        Py_XDECREF(name);
        return NULL;
    }

    if (!(self = GENERIC_ALLOC(&TDI_TemplateNodeType))) {
        TDI_SCOPE_CLEAR(scope);
        TDI_OVERLAY_CLEAR(overlay);
        Py_XDECREF(name);
        Py_DECREF(tagname);
        return NULL;
    }

    self->kind = separator ? SEP_NODE : PROC_NODE;
    if (noelement
            || (overlay && overlay->is_hidden)
            || (scope && scope->is_hidden))
        self->flags |= NODE_NOELEMENT;
    if (noauto)
        self->flags |= NODE_NOAUTO;
    if (is_closed)
        self->flags |= NODE_CLOSED;
    self->name = name;
    self->tagname = tagname;
    self->overlay = overlay;
    self->scope = scope;

    if (!(self->nodes = PyList_New(0))) {
        goto error;
    }
    if (load_attributes(self, attr) == -1)
        goto error;

    return (PyObject *)self;

error:
    Py_DECREF(self);
    return NULL;
}

/*
 * Allocate new TDI_TemplateNodeType and initialize as text node
 */
PyObject *
tdi_template_node_text_new(PyObject *content)
{
    tdi_node_t *self;

    if (!(self = GENERIC_ALLOC(&TDI_TemplateNodeType)))
         return NULL;

    self->kind = TEXT_NODE;
    if (!(self->content = tdi_content_new())) {
        Py_DECREF(self);
        return NULL;
    }
    Py_INCREF(content);
    self->content->clean = content;
    Py_INCREF(content);
    self->content->with_escapes = content;

    return (PyObject *)self;
}


/*
 * Allocate new TDI_TemplateNodeType and initialize as escaped text node
 */
PyObject *
tdi_template_node_escaped_text_new(PyObject *escaped, PyObject *content)
{
    tdi_node_t *self;

    if (!(self = GENERIC_ALLOC(&TDI_TemplateNodeType)))
         return NULL;

    self->kind = TEXT_NODE;
    if (!(self->content = tdi_content_new())) {
        Py_DECREF(self);
        return NULL;
    }
    Py_INCREF(escaped);
    self->content->clean = escaped;
    Py_INCREF(content);
    self->content->with_escapes = content;

    return (PyObject *)self;
}
