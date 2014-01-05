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
#include "tdi_copy.h"
#include "tdi_globals.h"
#include "tdi_render.h"

#include "obj_encoder.h"
#include "obj_iterate_iter.h"
#include "obj_model_adapters.h"
#include "obj_node.h"
#include "obj_repeat_iter.h"


/*
 * Node iterator
 *
 * iteritems and separate references are stolen.
 */
PyObject *
tdi_render_iterate(tdi_node_t *self, PyObject *iteritems, PyObject *separate)
{
    PyObject *tmp, *nodelist;

    if (!(nodelist = PyList_New(0))) {
        Py_DECREF(iteritems);
        Py_XDECREF(separate);
        return NULL;
    }
    Py_INCREF(self);
    /* Note: tmp is passed later to tdi_iterate_iterator_new */
    if (!(tmp = tdi_node_deepcopy(self, self->model, self->ctx, NULL))) {
        Py_DECREF(self);
        Py_DECREF(nodelist);
        Py_DECREF(iteritems);
        Py_XDECREF(separate);
        return NULL;
    }

    /*
     * This effectively indents the iterated nodeset by one level.
     * The original node (which was copied from before) only acts as a
     * container now.
     */
    TDI_CONTENT_CLEAR(self->content);
    Py_CLEAR(self->nodes);
    Py_INCREF(nodelist);
    self->nodes = nodelist;
    Py_INCREF(tdi_g_empty_dict);
    Py_CLEAR(self->namedict);
    self->namedict = tdi_g_empty_dict;
    self->flags |= NODE_MASKED;
    Py_DECREF(self);

    return tdi_iterate_iterator_new((tdi_node_t *)tmp, nodelist,
                                    iteritems, separate);
}


/*
 * Pop from render stack
 */
static void
tdi_render_stack_pop(tdi_render_stack_t **stack)
{
    if (*stack) {
        tdi_render_stack_t *tmp;

        tmp = *stack;
        *stack = tmp->next;
        Py_CLEAR(tmp->iter);
        Py_CLEAR(tmp->endtag);
        PyMem_Free(tmp);
    }
}


/*
 * Push to render stack
 */
int
tdi_render_stack_push(tdi_render_stack_t **next, PyObject *iter,
                      PyObject *endtag, int done)
{
    tdi_render_stack_t *stack;

    if (!(stack = PyMem_Malloc(sizeof *stack))) {
        Py_DECREF(iter);
        Py_XDECREF(endtag);
        PyErr_NoMemory();
        return -1;
    }

    stack->next = *next;
    stack->iter = iter;
    stack->endtag = endtag;
    stack->done = done;
    *next = stack;

    return 0;
}


/*
 * Make repeated node iterator
 */
static PyObject *
repeat(tdi_node_t *node)
{
    PyObject *callback, *itemlist, *fixed, *separate;

    Py_INCREF(node);
    callback = PyTuple_GET_ITEM(node->overlays, 0);
    Py_INCREF(callback);
    itemlist = PyTuple_GET_ITEM(node->overlays, 1);
    Py_INCREF(itemlist);
    fixed = PyTuple_GET_ITEM(node->overlays, 2);
    Py_INCREF(fixed);
    separate = PyTuple_GET_ITEM(node->overlays, 3);
    Py_INCREF(separate);

    /* Clear the flag now, so the copies are not repeated again... */
    node->flags &= ~NODE_REPEATED;

    Py_CLEAR(node->overlays);

    return tdi_repeat_iterator_new(node, callback, itemlist, fixed, separate);
}


/*
 * Run a callback
 */
static PyObject *
ask_model__callback(PyObject *func, tdi_node_t *node)
{
    PyObject *final_arg, *tmp, *args;
    Py_ssize_t j, length;

    args = node->overlays;
    length = PyTuple_GET_SIZE(args) + 1;
    if (!(final_arg = PyTuple_New(length)))
        return NULL;

    Py_INCREF(node);
    PyTuple_SET_ITEM(final_arg, 0, (PyObject *)node);

    for (j = 1; j < length; ++j) {
        tmp = PyTuple_GET_ITEM(args, j - 1);
        Py_INCREF(tmp);
        PyTuple_SET_ITEM(final_arg, j, tmp);
    }

    Py_CLEAR(node->overlays);

    tmp = PyObject_CallObject(func, final_arg);
    Py_DECREF(final_arg);
    return tmp;
}


/*
 * Ask the model
 */
static int
ask_model(tdi_render_t *self, tdi_node_t *node, int *done)
{
    PyObject *tmp, *result;
    int user_control;

    if (node->kind == DONE_NODE) {
        *done = 1;
        return 0;
    }

#define AS_BOOL(op) ((op) ? PyObject_IsTrue(op) : -1)

nested_callback:
    user_control = 0;
    if (node->kind == CB_NODE) {
        tmp = node->callback;
        Py_INCREF(tmp);
        Py_CLEAR(node->callback);
        node->kind = DONE_NODE;
        if (tmp == Py_None) {
            Py_DECREF(tmp);
            Py_CLEAR(node->overlays);
            *done = 0;
            return 0;
        }
        result = ask_model__callback(tmp, node);
        Py_DECREF(tmp);
        *done = AS_BOOL(result);
        Py_XDECREF(result);
        if (*done == -1)
            return -1;
        user_control = 1;
    }
    else if (self->done) {
        *done = 1;
    }
    else {
        tmp = tdi_adapter_method(
            (tdi_adapter_t *)self->model, tdi_g_rendermethod, node->name,
            node->modelscope,
            !!(node->flags & NODE_NOAUTO)
        );
        if (!tmp)
            return -1;
        if (tmp == Py_None) {
            Py_DECREF(tmp);
            *done = 0;
        }
        else {
            result = PyObject_CallFunctionObjArgs(tmp, (PyObject *)node, NULL);
            Py_DECREF(tmp);
            *done = AS_BOOL(result);
            Py_XDECREF(result);
            if (*done == -1)
                return -1;
            user_control = 1;
        }
    }

#undef AS_BOOL

    if (node->flags & NODE_REMOVED) {
        return 1;
    }
    else if (node->flags & NODE_REPEATED) {
        if (!(tmp = repeat(node)))
            return -1;
        if (tdi_render_stack_push(&self->stack, tmp, NULL, self->done) == -1)
            return -1;
        self->done = 0;
        return 1;
    }
    else if (user_control && node->kind == CB_NODE) {
        goto nested_callback;
    }

    return 0;
}


/*
 * Determine subnodes to render
 */
static PyObject *
subnodes(tdi_node_t *node, tdi_adapter_t *model)
{
    PyObject *list, *item = NULL, *iter = NULL;

    if (!(list = PyList_New(0)))
        return NULL;

#define APPEND(source) do {                                          \
    PyObject *tmp;                                                   \
    int subresult;                                                   \
    if (!(tmp = tdi_node_copy((source), model, node->ctx, 1, NULL))) \
        goto error;                                                  \
    subresult = PyList_Append(list, tmp);                            \
    Py_DECREF(tmp);                                                  \
    if (subresult == -1)                                             \
        goto error;                                                  \
} while (0)

    if (!(iter = PyObject_GetIter(node->nodes)))
        goto error;
    while ((item = PyIter_Next(iter))) {
        APPEND((tdi_node_t *)item);
        Py_DECREF(item);
    }
    if (PyErr_Occurred())
        goto error;
    Py_DECREF(iter);

#undef APPEND

    iter = PyObject_GetIter(list);
    Py_DECREF(list);
    return iter;

error:
    Py_XDECREF(item);
    Py_XDECREF(iter);
    Py_DECREF(list);
    return NULL;
}


/*
 * Get next rendered chunk
 */
PyObject *
tdi_render_next(tdi_render_t *self)
{
    PyObject *tmp, *endtag, *nodes, *esc;
    tdi_node_t *node;
    int done, asked;

    switch (self->stage) {

    case TDI_RE_STAGE_ONLY_CONTENT:
        self->stage = TDI_RE_STAGE_DONE;
        Py_INCREF(self->model);
        return self->model;


    case TDI_RE_STAGE_BEGIN:
        self->stage = TDI_RE_STAGE_NEXTNODE;


    case TDI_RE_STAGE_NEXTNODE:
    tdi_re_stage_nextnode:
        if (!self->stack) {
            self->stage = TDI_RE_STAGE_DONE;
            goto exit;
        }
        if (!(tmp = PyIter_Next(self->stack->iter))) {
            if (PyErr_Occurred())
                goto exit;
            self->done = self->stack->done;
            self->endtag = self->stack->endtag;
            Py_XINCREF(self->endtag);
            tdi_render_stack_pop(&self->stack);
            goto tdi_re_stage_endtag;
        }
        node = (tdi_node_t *)tmp;

        if (node->kind == TEXT_NODE) {
            tmp = self->emit_escaped ?
                node->content->with_escapes : node->content->clean;
            Py_INCREF(tmp);
            Py_DECREF(node);
            return tmp;
        }

        if (node->flags & NODE_REMOVED) {
            Py_DECREF(node);
            goto tdi_re_stage_nextnode;
        }

        if ((asked = ask_model(self, node, &done)) == -1) {
            Py_DECREF(node);
            goto exit;
        }
        if (asked == 1) {
            Py_DECREF(node);
            goto tdi_re_stage_nextnode;
        }

        if (!(node->flags & (NODE_NOELEMENT | NODE_MASKED))) {
            if (!(tmp = ENCODE_STARTTAG(node))) {
                Py_DECREF(node);
                goto exit;
            }
            asked = 1;
            Py_INCREF(node->endtag);
            endtag = node->endtag;
        }
        else
            endtag = NULL;

        if (node->content) {
            if (self->emit_escaped) {
                if (node->content->with_escapes) {
                    Py_INCREF(node->content->with_escapes);
                    self->content = node->content->with_escapes;
                }
                else {
                    if (!(esc = ENCODE_ESCAPE(node, node->content->clean))) {
                        Py_DECREF(node);
                        goto exit;
                    }
                    self->content = esc;
                }
            }
            else {
                Py_INCREF(node->content->clean);
                self->content = node->content->clean;
            }
            Py_DECREF(node);
            self->endtag = endtag;
            self->stage = TDI_RE_STAGE_CONTENT;
            if (asked != 1)
                goto tdi_re_stage_content;
        }
        else {
            nodes = subnodes(node, (tdi_adapter_t *)self->model);
            Py_DECREF(node);
            if (!nodes)
                goto exit;
            if (tdi_render_stack_push(&self->stack, nodes, endtag,
                                      self->done) == -1)
                goto exit;
            if (done)
                self->done = 1;
            if (asked != 1)
                goto tdi_re_stage_nextnode;
        }
        return tmp;


    case TDI_RE_STAGE_CONTENT:
    tdi_re_stage_content:
        self->stage = self->endtag
            ? TDI_RE_STAGE_ENDTAG
            : TDI_RE_STAGE_NEXTNODE;
        tmp = self->content;
        self->content = NULL;
        return tmp;


    case TDI_RE_STAGE_ENDTAG:
    tdi_re_stage_endtag:
        self->stage = TDI_RE_STAGE_NEXTNODE;
        if (!self->endtag)
            goto tdi_re_stage_nextnode;
        tmp = self->endtag;
        self->endtag = NULL;
        return tmp;


    case TDI_RE_STAGE_DONE:
        goto exit;
    }

exit:
    return NULL;
}
