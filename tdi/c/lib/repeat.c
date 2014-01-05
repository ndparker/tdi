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
#include "tdi_repeat.h"

#include "obj_model_adapters.h"
#include "obj_node.h"


/*
 * make repeated ctx
 */
static PyObject *
make_repeated_ctx(tdi_repeat_t *self, PyObject *item, int diff)
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

    tmp = self->fixed;
    Py_INCREF(tmp);
    PyTuple_SET_ITEM(ctx, 2, tmp);

    return ctx;
}

/*
 * make repeated callback args
 *
 * item may be NULL (for separators)
 */
static PyObject *
make_repeated_callback_args(tdi_repeat_t *self, PyObject *item)
{
    PyObject *args, *tmp;
    Py_ssize_t length, j;
    int diff = 0 + !!item;

    length = diff + PyTuple_GET_SIZE(self->fixed);
    if (!(args = PyTuple_New(length)))
        return NULL;

    if (item) {
        Py_INCREF(item);
        PyTuple_SET_ITEM(args, 0, item);
    }
    for (j = diff; j < length; ++j) {
        tmp = PyTuple_GET_ITEM(self->fixed, j - diff);
        Py_INCREF(tmp);
        PyTuple_SET_ITEM(args, j, tmp);
    }

    return args;
}


/*
 * make repeated separator
 */
static PyObject *
make_repeated_separator(tdi_repeat_t *self)
{
    PyObject *ctx, *item;
    tdi_node_t *newnode, *sep = (tdi_node_t *)self->node->sep;

    /* easy case and probably the general one: render as text */
    if (!self->sepmodel && sep->complete)
        return Py_INCREF(sep->complete), sep->complete;

    /* callback case */
    if (!(item = PyTuple_New(2)))
        return NULL;
    Py_INCREF(self->last_item);
    PyTuple_SET_ITEM(item, 0, self->last_item);
    Py_INCREF(self->item);
    PyTuple_SET_ITEM(item, 1, self->item);

    ctx = make_repeated_ctx(self, item, 1);
    Py_DECREF(item);
    if (!ctx)
        return NULL;

    /* create repeated node */
    newnode = (tdi_node_t *)tdi_node_deepcopy(sep, self->node->model, ctx,
                                              NULL);
    Py_DECREF(ctx);
    if (!newnode)
        return NULL;

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
    newnode->overlays = make_repeated_callback_args(self, NULL);
    if (!newnode->overlays) {
        Py_DECREF(newnode);
        return NULL;
    }

    return (PyObject *)newnode;
}


/*
 * make repeated node
 */
static PyObject *
make_repeated_node(tdi_repeat_t *self)
{
    PyObject *ctx;
    tdi_node_t *newnode;

    if (!(ctx = make_repeated_ctx(self, self->item, 0)))
        return NULL;

    /* create repeated node */
    newnode = (tdi_node_t *)tdi_node_deepcopy(self->node, self->node->model,
                                              ctx, NULL);
    Py_DECREF(ctx);
    if (!newnode)
        return NULL;

    newnode->kind = CB_NODE;
    Py_INCREF(self->callback);
    newnode->callback = self->callback;

    Py_CLEAR(newnode->overlays);
    newnode->overlays = make_repeated_callback_args(self, self->item);
    if (!newnode->overlays) {
        Py_DECREF(newnode);
        return NULL;
    }

    return (PyObject *)newnode;
}


/*
 * Get next repetition node
 */
PyObject *
tdi_repeat_next(tdi_repeat_t *self)
{
    PyObject *nextnode;

    switch (self->stage) {

    case TDI_RI_STAGE_BEGIN:
        self->idx = -1;
        Py_CLEAR(self->node->callback);
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
            if (PyErr_Occurred())
                goto exit;
            goto done;
        }
        ++self->idx;
        if (self->idx > 0 && self->node->sep) {
            self->stage = TDI_RI_STAGE_SEP;
            goto stage_sep;
        }
        self->stage = TDI_RI_STAGE_NODE;

    case TDI_RI_STAGE_NODE:
        nextnode = make_repeated_node(self);
        if (!nextnode)
            goto exit;
        Py_CLEAR(self->last_item);
        self->last_item = self->item;
        self->item = NULL;
        self->stage = TDI_RI_STAGE_NEXT;
        return nextnode;

    case TDI_RI_STAGE_SEP:
    stage_sep:
        nextnode = make_repeated_separator(self);
        if (!nextnode)
            goto exit;
        self->stage = TDI_RI_STAGE_NODE;
        return nextnode;

    case TDI_RI_STAGE_DONE:
        goto done;
    }

exit:
    return NULL;

done:
    self->stage = TDI_RI_STAGE_DONE;
    Py_CLEAR(self->node);
    Py_CLEAR(self->callback);
    Py_CLEAR(self->iteritems);
    Py_CLEAR(self->fixed);
    Py_CLEAR(self->sepmodel);
    Py_CLEAR(self->item);
    Py_CLEAR(self->last_item);
    return NULL;
}
