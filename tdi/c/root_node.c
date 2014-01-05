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

#include "tdi_content.h"
#include "tdi_exceptions.h"
#include "tdi_finalize.h"
#include "tdi_overlay.h"
#include "tdi_repr.h"

#include "obj_avoid_gc.h"
#include "obj_decoder.h"
#include "obj_encoder.h"
#include "obj_model_adapters.h"
#include "obj_node.h"
#include "obj_render_iter.h"
#include "obj_root_node.h"
#include "obj_template_node.h"


/* ------------------- BEGIN TDI_RootNodeType DEFINITION ------------------- */

static PyObject *
findnode__parse_nodespec(PyObject *nodename)
{
    PyObject *names, *name;
    const char *cp, *cstring, *sentinel;
    Py_ssize_t length;
    int res;

    if (!(names = PyList_New(0)))
        return NULL;
    cstring = PyString_AS_STRING(nodename);
    sentinel = cstring + PyString_GET_SIZE(nodename);
    for (cp = cstring; cp < sentinel; ++cp) {
        if (*cp == '.') {
            length = cp - cstring;
            name = PyString_FromStringAndSize(cstring, length);
            if (!name)
                goto error;
            res = PyList_Append(names, name);
            Py_DECREF(name);
            if (res == -1)
                goto error;
            cstring = cp + 1;
        }
    }
    if (cp > cstring) {
        length = cp - cstring;
        name = PyString_FromStringAndSize(cstring, length);
        if (!name)
            goto error;
        res = PyList_Append(names, name);
        Py_DECREF(name);
        if (res == -1)
            goto error;
    }

    if (PyList_GET_SIZE(names) == 0)
        goto notfound;
    return names;

notfound:
    PyErr_SetObject(TDI_E_NodeNotFoundError, nodename);
error:
    Py_DECREF(names);
    return NULL;
}

/*
 * possibly resolve name in current node
 */
static int
findnode__resolve(PyObject *name, tdi_node_t **current)
{
    PyObject *idx;
    tdi_node_t *tmp;
    Py_ssize_t node_idx;
    int res;

    do {
        if (!(idx = PyDict_GetItem((*current)->namedict, name))) {
            if (PyErr_Occurred())
                return -1;
            for (node_idx = 0; node_idx < PyList_GET_SIZE((*current)->nodes);
                                                                ++node_idx) {
                tmp = (tdi_node_t *)PyList_GET_ITEM((*current)->nodes,
                                                     node_idx);
                if (tmp->kind != PROC_NODE || !tmp->name)
                    continue;
                if (PyObject_Cmp(tmp->name, name, &res) == -1)
                    return -1;
                if (res == 0) {
                    Py_INCREF(tmp);
                    Py_CLEAR(*current);
                    *current = tmp;
                    return 1;
                }
            }
            return 0;
        }
        node_idx = PyInt_AsSsize_t(idx);
        if (PyErr_Occurred())
            return -1;
        tmp = (tdi_node_t *)PyList_GET_ITEM((*current)->nodes,
                                            node_idx < 0
                                                ? (-1 - node_idx): node_idx);
        Py_INCREF(tmp);
        Py_CLEAR(*current);
        *current = tmp;
    } while (node_idx < 0);

    return 1;
}

/*
 * Find a node by string (x.y.z). The chain is only loosely bound.
 */
static tdi_node_t *
findnode(tdi_node_t *current, PyObject *nodename)
{
    PyObject *names, *name, *next, *process;
    Py_ssize_t name_idx, names_len, process_len, process_idx, j, jlen;
    int res;

    if (!(names = findnode__parse_nodespec(nodename)))
        return NULL;
    names_len = PyList_GET_SIZE(names);
    Py_INCREF(current);
    for (name_idx = 0; name_idx < names_len; ++name_idx) {
        name = PyList_GET_ITEM(names, name_idx);
        if ((res = findnode__resolve(name, &current)) == -1)
            goto error_current;
        else if (res)
            continue;

        next = PyList_New(0);
        if (PyList_GET_SIZE(current->nodes) > 0) {
            if (PyList_Append(next, current->nodes) == -1)
                goto error_next;
        }
        Py_CLEAR(current);
        while ((process_len = PyList_GET_SIZE(next)) > 0) {
            process = next;
            if (!(next = PyList_New(0)))
                goto error_process;
            for (process_idx = 0; process_idx < process_len; ++process_idx) {
                jlen = PyList_GET_SIZE(PyList_GET_ITEM(process, process_idx));
                for (j = 0; j < jlen; ++j) {
                    current = (tdi_node_t *)PyList_GET_ITEM(
                                    PyList_GET_ITEM(process, process_idx), j);
                    if (current->kind != PROC_NODE)
                        continue;
                    Py_INCREF(current);
                    if ((res = findnode__resolve(name, &current)) == -1)
                        goto error_process;
                    else if (res) {
                        Py_DECREF(process);
                        goto next_name;
                    }
                    else if (PyList_GET_SIZE(current->nodes) > 0) {
                        if (PyList_Append(next, current->nodes) == -1)
                            goto error_process;
                    }
                    Py_CLEAR(current);
                }
            }
            /* no clearing needed, reassigned right away */
            Py_DECREF(process);
        }
        Py_DECREF(next);
        --name_idx;
        break;

    next_name:
        Py_DECREF(next);
    }

    if (name_idx != names_len) {
        PyErr_SetObject(TDI_E_NodeNotFoundError, nodename);
        goto error_current;
    }
    Py_DECREF(names);
    return current;

error_process:
    Py_DECREF(process);
error_next:
    Py_XDECREF(next);
error_current:
    Py_XDECREF(current);
    Py_DECREF(names);
    return NULL;
}


PyDoc_STRVAR(TDI_RootNodeType_render__doc__,
"render(self, model, startnode=None)\n\
\n\
Render the tree into chunks, calling `model` for input\n\
\n\
:Parameters:\n\
  `model` : `ModelAdapterInterface`\n\
    The model object\n\
\n\
  `startnode` : ``str``\n\
    Only render this node (and all its children). The node\n\
    is addressed via a dotted string notation, like ``a.b.c`` (this\n\
    would render the ``c`` node.) The notation does not describe a\n\
    strict node chain, though. Between to parts of a node chain may\n\
    be gaps in the tree. The algorithm looks out for the first\n\
    matching node. It does no backtracking and so does not cover all\n\
    branches (yet?), but that works fine for realistic cases :). A\n\
    non-working example would be (searching for a.b.c)::\n\
\n\
      *\n\
      +- a\n\
      |  `- b - d\n\
      `- a\n\
         `- b - c\n\
\n\
:Return: Rendered chunks\n\
:Rtype: iterable");

static PyObject *
TDI_RootNodeType_render(tdi_node_t *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"model", "startnode", NULL};
    PyObject *result, *model, *startnode = NULL;
    tdi_node_t *rootnode;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O", kwlist,
                                     &model, &startnode))
        return NULL;

    if (!(self->flags & NODE_FINALIZED)) {
        PyErr_SetString(TDI_E_NodeTreeError,
                        "The tree was not finalized yet");
        return NULL;
    }

    Py_INCREF(model);
    if (!(model = (PyObject *)tdi_adapter_adapt(model)))
        return NULL;

    if (startnode == Py_None)
        startnode = NULL;
    if (startnode) {
        if (!(startnode = PyObject_Str(startnode))) {
            Py_DECREF(model);
            return NULL;
        }
        rootnode = findnode(self, startnode);
        Py_DECREF(startnode);
        if (!rootnode) {
            Py_DECREF(model);
            return NULL;
        }
    }
    else {
        rootnode = self;
        Py_INCREF(rootnode);
    }
    result = tdi_render_iterator_new(rootnode, (tdi_adapter_t *)model);
    Py_DECREF(rootnode);
    Py_DECREF(model);

    return result;
}


PyDoc_STRVAR(TDI_RootNodeType_to_string__doc__,
"to_string(self, verbose=False)\n\
\n\
String representation of the tree\n\
\n\
:Parameters:\n\
  `verbose` : ``bool``\n\
    Show (shortened) text node content and separator nodes?\n\
\n\
:Return: The string representation\n\
:Rtype: ``str``");

static PyObject *
TDI_RootNodeType_to_string(tdi_node_t *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"verbose", NULL};
    PyObject *verbose = NULL;
    int is_verbose = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O", kwlist, &verbose))
        return NULL;

    if (!(self->flags & NODE_FINALIZED)) {
        PyErr_SetString(TDI_E_NodeTreeError,
                        "The tree was not finalized yet");
        return NULL;
    }

    if (verbose && ((is_verbose = PyObject_IsTrue(verbose)) == -1))
        return NULL;

    return tdi_repr_do(self, is_verbose);
}

PyDoc_STRVAR(TDI_RootNodeType_finalize__doc__,
"finalize(self, encoder)\n\
\n\
Finalize the tree\n\
\n\
This method assigns separator nodes to their accompanying content\n\
nodes, concatenates adjacent text nodes and tries to optimize\n\
the tree a bit.\n\
\n\
:Parameters:\n\
  `encoder` : `EncoderInterface`\n\
    Encoder instance\n\
\n\
:Exceptions:\n\
  - `NodeTreeError` : The tree was already finalized or endtag was not\n\
    set");

static PyObject *
TDI_RootNodeType_finalize(tdi_node_t *self, PyObject *args,
                          PyObject *kwds)
{
    static char *kwlist[] = {"encoder", "decoder", NULL};
    PyObject *encoder, *decoder;
    tdi_encoder_t *encoder_wrapper;
    tdi_decoder_t *decoder_wrapper;


    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO", kwlist,
                                     &encoder, &decoder))
        return NULL;

    if (!(encoder_wrapper = tdi_encoder_wrapper_new(encoder)))
        return NULL;

    if (!(decoder_wrapper = tdi_decoder_wrapper_new(decoder))) {
        Py_DECREF((PyObject *)encoder_wrapper);
        return NULL;
    }

    if (tdi_finalize_tree(self, encoder_wrapper, decoder_wrapper) == -1)
        return NULL;

    Py_RETURN_NONE;
}

PyDoc_STRVAR(TDI_RootNodeType_overlay__doc__,
"overlay(self, other)\n\
\n\
Overlay this tree with another one\n\
\n\
:Parameters:\n\
  `other` : `Root`\n\
    The tree to lay over\n\
\n\
:Exceptions:\n\
  - `NodeTreeError` : Finalization error");

static PyObject *
TDI_RootNodeType_overlay(tdi_node_t *self, PyObject *args,
                         PyObject *kwds)
{
    static char *kwlist[] = {"other", NULL};
    PyObject *other_obj;
    tdi_node_t *other, *newobject;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", kwlist, &other_obj))
        return NULL;

    if (!TDI_RootNodeType_CheckExact(other_obj)) {
        PyErr_SetString(PyExc_TypeError,
            "Overlay node must be a Root instance"
        );
        return NULL;
    }
    other = (tdi_node_t *)other_obj;

    if (!(self->flags & NODE_FINALIZED)) {
        PyErr_SetString(TDI_E_NodeTreeError, "Tree was not finalized yet.");
        return NULL;
    }
    if (!(other->flags & NODE_FINALIZED)) {
        PyErr_SetString(TDI_E_NodeTreeError,
                        "Overlay tree was not finalized yet.");
        return NULL;
    }

    Py_INCREF(other->overlays);
    newobject = tdi_overlay_do(self, PyTuple_GET_ITEM(other->overlays, 0));
    Py_DECREF(other->overlays);

    return (PyObject *)newobject;
}

static PyObject *
TDI_RootNodeType_getencoder(tdi_node_t *self, void *closure)
{
    Py_INCREF(self->encoder->encoder);
    return (PyObject *)self->encoder->encoder;
}

static PyObject *
TDI_RootNodeType_getdecoder(tdi_node_t *self, void *closure)
{
    Py_INCREF(self->decoder->decoder);
    return (PyObject *)self->decoder->decoder;
}

static PyObject *
TDI_RootNodeType_source_overlay_names(tdi_node_t *self, void *closure)
{
    if (!self->overlays) {
        return PyTuple_New(0);
    }
    return PyObject_CallMethod(PyTuple_GET_ITEM(self->overlays, 0),
                               "iterkeys", "");
}

static PyObject *
TDI_RootNodeType_target_overlay_names(tdi_node_t *self, void *closure)
{
    if (!self->overlays) {
        return PyTuple_New(0);
    }
    return PyObject_CallMethod(PyTuple_GET_ITEM(self->overlays, 1),
                               "iterkeys", "");
}

static PyGetSetDef TDI_RootNodeType_getset[] = {
    {"encoder",
     (getter)TDI_RootNodeType_getencoder,
     NULL,
     PyDoc_STR(
"Output encoder\n\
\n\
:Type: `EncoderInterface`"),
     NULL},

    {"decoder",
     (getter)TDI_RootNodeType_getdecoder,
     NULL,
     PyDoc_STR(
"Input decoder\n\
\n\
:Type: `DecoderInterface`"),
     NULL},

    {"source_overlay_names",
     (getter)TDI_RootNodeType_source_overlay_names,
     NULL,
     PyDoc_STR(
"Source overlay names\n\
\n\
:Type: iterable"),
     NULL},

    {"target_overlay_names",
     (getter)TDI_RootNodeType_target_overlay_names,
     NULL,
     PyDoc_STR(
"Target overlay names\n\
\n\
:Type: iterable"),
     NULL},

    {NULL}  /* Sentinel */
};

static struct PyMethodDef TDI_RootNodeType_methods[] = {
    {"render",
     (PyCFunction)TDI_RootNodeType_render,      METH_KEYWORDS,
     TDI_RootNodeType_render__doc__},

    {"to_string",
     (PyCFunction)TDI_RootNodeType_to_string,   METH_KEYWORDS,
     TDI_RootNodeType_to_string__doc__},

    {"finalize",
     (PyCFunction)TDI_RootNodeType_finalize,    METH_KEYWORDS,
     TDI_RootNodeType_finalize__doc__},

    {"overlay",
     (PyCFunction)TDI_RootNodeType_overlay,     METH_KEYWORDS,
     TDI_RootNodeType_overlay__doc__},

    {NULL, NULL}  /* Sentinel */
};

static PyObject *
TDI_RootNodeType_str(tdi_node_t *self)
{
    return tdi_repr_do(self, 1);
}

#ifndef TDI_AVOID_GC
static int
TDI_RootNodeType_traverse(tdi_node_t *self, visitproc visit, void *arg)
{
    Py_VISIT(self->nodes);
    Py_VISIT(self->namedict);
    Py_VISIT(self->overlays);
    TDI_CONTENT_VISIT(self->content);
    Py_VISIT((PyObject *)self->encoder);
    Py_VISIT((PyObject *)self->decoder);

    return 0;
}
#endif

static int
TDI_RootNodeType_clear(tdi_node_t *self)
{
    if (self->weakreflist)
        PyObject_ClearWeakRefs((PyObject *)self);
    Py_CLEAR(self->nodes);
    Py_CLEAR(self->namedict);
    Py_CLEAR(self->overlays);
    TDI_CONTENT_CLEAR(self->content);
    Py_CLEAR(self->encoder);
    Py_CLEAR(self->decoder);

    return 0;
}

static PyObject *
TDI_RootNodeType_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {NULL};
    tdi_node_t *self;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "", kwlist))
        return NULL;

    if (!(self = GENERIC_ALLOC(type)))
        return NULL;
    self->flags = NODE_ROOT;
    if (!(self->nodes = PyList_New(0)))
        goto error;

    return (PyObject *)self;

error:
    Py_DECREF(self);
    return NULL;
}

DEFINE_GENERIC_DEALLOC(TDI_RootNodeType)

PyDoc_STRVAR(TDI_RootNodeType__doc__,
"Root()\n\
\n\
Root Node class\n\
\n\
This class has to be used as the initial root of the tree.");

PyTypeObject TDI_RootNodeType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".Root",                            /* tp_name */
    sizeof(tdi_node_t),                                 /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_RootNodeType_dealloc,               /* tp_dealloc */
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
    (reprfunc)TDI_RootNodeType_str,                     /* tp_str */
    0,                                                  /* tp_getattro */
    0,                                                  /* tp_setattro */
    0,                                                  /* tp_as_buffer */
    Py_TPFLAGS_HAVE_WEAKREFS                            /* tp_flags */
    | Py_TPFLAGS_HAVE_CLASS
    | TDI_IF_GC(Py_TPFLAGS_HAVE_GC),
    TDI_RootNodeType__doc__,                            /* tp_doc */
    (traverseproc)TDI_IF_GC(TDI_RootNodeType_traverse), /* tp_traverse */
    (inquiry)TDI_IF_GC(TDI_RootNodeType_clear),         /* tp_clear */
    0,                                                  /* tp_richcompare */
    offsetof(tdi_node_t, weakreflist),                  /* tp_weaklistoffset */
    0,                                                  /* tp_iter */
    0,                                                  /* tp_iternext */
    TDI_RootNodeType_methods,                           /* tp_methods */
    0,                                                  /* tp_members */
    TDI_RootNodeType_getset,                            /* tp_getset */
    &TDI_TemplateNodeType,                              /* tp_base */
    0,                                                  /* tp_dict */
    0,                                                  /* tp_descr_get */
    0,                                                  /* tp_descr_set */
    0,                                                  /* tp_dictoffset */
    0,                                                  /* tp_init */
    0,                                                  /* tp_alloc */
    TDI_RootNodeType_new                                /* tp_new */
};

/* -------------------- END TDI_RootNodeType DEFINITION -------------------- */
