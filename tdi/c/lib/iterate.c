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

#include "tdi_copy.h"
#include "tdi_globals.h"
#include "tdi_iterate.h"

#include "obj_model_adapters.h"
#include "obj_node.h"


/*
 * make iterated ctx
 */
static PyObject *
make_iterated_ctx(tdi_iterate_t *self, PyObject *item, int diff)
{
    PyObject *ctx, *tmp;

    if (!(ctx = PyTuple_New(3))) {
        return NULL;
    }

    Py_INCREF(item);
    PyTuple_SET_ITEM(ctx, 1, item);

    if (!(tmp = PyInt_FromSsize_t(self->idx - diff))) {
        Py_DECREF(ctx);
        return NULL;
    }
    PyTuple_SET_ITEM(ctx, 0, tmp);

    Py_INCREF(tdi_g_empty_tuple);
    PyTuple_SET_ITEM(ctx, 2, tdi_g_empty_tuple);

    return ctx;
}


/*
 * make iterated callback args
 */
static PyObject *
make_iterated_callback_args(void)
{
    PyObject *args;

    if (!(args = PyTuple_New(0)))
        return NULL;

    return args;
}


/*
 * make iterated separator
 */
static int
make_iterated_separator(tdi_iterate_t *self)
{
    PyObject *ctx, *item;
    tdi_node_t *newnode, *sep = (tdi_node_t *)self->node->sep;
    int result;

    /* easy case and probably the general one: render as text */
    if (!self->sepmodel && sep->complete)
        return PyList_Append(self->nodelist, sep->complete);

    /* callback case */
    if (!(item = PyTuple_New(2)))
        return -1;
    Py_INCREF(self->last_item);
    PyTuple_SET_ITEM(item, 0, self->last_item);
    Py_INCREF(self->item);
    PyTuple_SET_ITEM(item, 1, self->item);

    ctx = make_iterated_ctx(self, item, 1);
    Py_DECREF(item);
    if (!ctx)
        return -1;

    /* create repeated node */
    newnode = (tdi_node_t *)tdi_node_deepcopy(sep, self->node->model, ctx,
                                              NULL);
    Py_DECREF(ctx);
    if (!newnode)
        return -1;

    newnode->kind = CB_NODE;
    Py_CLEAR(newnode->callback);
    if (self->sepmodel) {
        Py_INCREF(self->sepmodel);
        newnode->callback = self->sepmodel;
    }
    else {
        Py_INCREF(Py_None);
        newnode->callback = Py_None;
    }

    Py_CLEAR(newnode->overlays);
    newnode->overlays = make_iterated_callback_args();
    if (!newnode->overlays) {
        Py_DECREF(newnode);
        return -1;
    }

    result = PyList_Append(self->nodelist, (PyObject *)newnode);
    Py_DECREF(newnode);
    return result;
}


/*
 * make iterated (node, item) tuple
 */
static PyObject *
make_iterated_node(tdi_iterate_t *self)
{
    PyObject *result;
    tdi_node_t *newnode;

    /* create repeated node */
    newnode = (tdi_node_t *)tdi_node_deepcopy(self->node, self->node->model,
                                              NULL, NULL);
    if (!newnode)
        return NULL;
    newnode->kind = DONE_NODE;
    if (!(result = PyTuple_New(2))) {
        Py_DECREF(newnode);
        return NULL;
    }
    PyTuple_SET_ITEM(result, 0, (PyObject *)newnode);
    Py_INCREF(self->item);
    PyTuple_SET_ITEM(result, 1, self->item);

    if (PyList_Append(self->nodelist, (PyObject *)newnode) == -1) {
        Py_DECREF(result);
        return NULL;
    }

    return result;
}


/*
 * Get next iteration node
 */
PyObject *
tdi_iterate_next(tdi_iterate_t *self)
{
    PyObject *nextnode;

    switch (self->stage) {
    case TDI_RI_STAGE_BEGIN:
        self->idx = -1;
        if (self->node->sep && !self->sepmodel && self->node->name) {
            /* nextnode misuse as callback tmp */
            nextnode = tdi_adapter_method(
                self->node->model, tdi_g_separatemethod, self->node->name,
                ((tdi_node_t *)(self->node->sep))->modelscope,
                !!(((tdi_node_t *)(self->node->sep))->flags & NODE_NOAUTO)
            );
            if (!nextnode)
                goto exit;
            if (nextnode == Py_None) {
                Py_DECREF(Py_None);
                nextnode = NULL;
            }
            self->sepmodel = nextnode;
        }
        self->stage = TDI_RI_STAGE_NEXT;

    case TDI_RI_STAGE_NEXT:
        if (!self->item && !(self->item = PyIter_Next(self->iteritems))) {
            if (!PyErr_Occurred()) {
                Py_CLEAR(self->last_item);
                self->stage = TDI_RI_STAGE_DONE;
            }
            goto exit;
        }
        ++self->idx;
        if (self->idx > 0 && self->node->sep) {
            if (make_iterated_separator(self) == -1)
                goto exit;
        }
        self->stage = TDI_RI_STAGE_NODE;

    case TDI_RI_STAGE_NODE:
        nextnode = make_iterated_node(self);
        if (!nextnode)
            goto exit;
        Py_CLEAR(self->last_item);
        self->last_item = self->item;
        self->item = NULL;
        self->stage = TDI_RI_STAGE_NEXT;
        return nextnode;

    case TDI_RI_STAGE_SEP:
        PyErr_SetString(PyExc_SystemError, "Invalid iterator state");

    case TDI_RI_STAGE_DONE:
        goto exit;
    }

exit:
    return NULL;
}
