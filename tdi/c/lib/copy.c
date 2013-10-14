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
#include "tdi.h"
#include "tdi_content.h"
#include "tdi_copy.h"
#include "tdi_node_clear.h"
#include "tdi_overlay.h"
#include "tdi_scope.h"

#include "obj_node.h"

/*
 * Allocate new TDI_NodeType and initialize from another Node or TemplateNode
 */
PyObject *
tdi_node_copy(tdi_node_t *node, tdi_adapter_t *model, PyObject *ctx,
              int light, tdi_node_t *target)
{
    PyObject *item;
    tdi_node_t *self;
    Py_ssize_t j, length;

    if (node->kind == TEXT_NODE)
        return Py_INCREF(node), (PyObject *)node;

    if (light && !target && (node->flags & NODE_USER)) {
        Py_INCREF(node);
        if (!node->callback || node->callback == Py_None) {
            Py_XINCREF(ctx);
            Py_CLEAR(node->ctx);
            node->ctx = ctx;
        }
        return (PyObject *)node;
    }

    if (target) {
        self = target;
        if (!(self->flags & NODE_USER)) {
            PyErr_SetString(PyExc_ValueError,
                "Internal TDI error, wrong node type passed.");
            return NULL;
        }
        Py_INCREF(self);
        if (self != node)
            node_clear(self);
    }
    else if (!(self = GENERIC_ALLOC(&TDI_NodeType)))
         return NULL;

    if (node->flags & NODE_USER
        && node->callback && node->callback != Py_None) {
        Py_XINCREF(node->ctx);
        self->ctx = node->ctx;
    }
    else {
        Py_XINCREF(ctx);
        if (node->flags & NODE_USER && self == node)
            Py_CLEAR(self->ctx);
        self->ctx = ctx;
    }

    Py_INCREF((PyObject *)model);
    if (target && self == node) {
        if (node->flags & NODE_USER)
            Py_CLEAR(self->model);
        self->model = model;
        goto done;
    }

    self->flags = node->flags | NODE_USER;

    self->model = model;
    self->kind = node->kind;

    Py_XINCREF(node->sep);
    self->sep = node->sep;

    Py_XINCREF(node->callback);
    self->callback = node->callback;

    Py_XINCREF(node->overlays);
    self->overlays = node->overlays;

    Py_XINCREF(node->tagname);
    self->tagname = node->tagname;

    Py_INCREF(node->endtag);
    self->endtag = node->endtag;

    Py_XINCREF(node->name);
    self->name = node->name;

    Py_INCREF((PyObject *)node->encoder);
    self->encoder = node->encoder;

    Py_INCREF((PyObject *)node->decoder);
    self->decoder = node->decoder;

    Py_INCREF(node->namedict);
    self->namedict = node->namedict;

    Py_INCREF(node->modelscope);
    self->modelscope = node->modelscope;

    self->content = tdi_content_copy(node->content);
    if (PyErr_Occurred())
        goto error_content;

    self->scope = tdi_scope_copy(node->scope);
    if (PyErr_Occurred())
        goto error_scope;

    self->overlay = tdi_overlay_copy(node->overlay);
    if (PyErr_Occurred())
        goto error_overlay;

    if (!(self->attr = PyDict_Copy(node->attr)))
        goto error_attr;

    length = PyList_GET_SIZE(node->nodes);
    if (!(self->nodes = PyList_New(length)))
        goto error_nodes;
    for (j = 0; j < length; ++j) {
        if (!(item = PyList_GetItem(node->nodes, j)))
            goto error_nodes;
        Py_INCREF(item);
        PyList_SET_ITEM(self->nodes, j, item);
    }

done:
    return (PyObject *)self;

error_content:
error_scope:
error_overlay:
    self->attr = NULL;
error_attr:
    self->nodes = NULL;
error_nodes:
    Py_DECREF(self);

    return NULL;
}


/*
 * Deep-copy TDI_NodeType (but shallow-copy TemplateNodeType subnodes)
 */
PyObject *
tdi_node_deepcopy(tdi_node_t *self, tdi_adapter_t *model, PyObject *ctx,
                  tdi_node_t *node)
{
    PyObject *item;
    tdi_node_t *subnode;
    Py_ssize_t j, length;

    if (!(node = (tdi_node_t *)tdi_node_copy(self, model, ctx, 0, node)))
        return NULL;

    if (!node->content) {
        length = PyList_GET_SIZE(node->nodes);
        for (j = 0; j < length; ++j) {
            subnode = (tdi_node_t *)PyList_GET_ITEM(node->nodes, j);
            if (subnode->kind != TEXT_NODE && (subnode->flags & NODE_USER)) {
                if (!(item = tdi_node_deepcopy(subnode, model, ctx, NULL))) {
                    Py_DECREF(node);
                    return NULL;
                }
                if (PyList_SetItem(node->nodes, j, item) == -1) {
                    Py_DECREF(node);
                    return NULL;
                }
            }
        }
    }

    return (PyObject *)node;
}


