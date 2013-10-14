/*
 * Copyright 2006 - 2012
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
#include "tdi_globals.h"
#include "tdi_overlay.h"
#include "tdi_repr.h"

#include "obj_node.h"
#include "obj_repr_iter.h"

/*
 * Pop from repr stack
 */
static void
tdi_repr_stack_pop(tdi_repr_stack_t **stack)
{
    if (*stack) {
        tdi_repr_stack_t *tmp;

        tmp = *stack;
        *stack = tmp->next;
        Py_CLEAR(tmp->iter);
        PyMem_Free(tmp);
    }
}

/*
 * Push to repr stack
 */
int
tdi_repr_stack_push(tdi_repr_stack_t **next, tdi_node_t *node,
                    int verbose)
{
    PyObject *iter;
    tdi_repr_stack_t *stack;

    if (!(stack = PyMem_Malloc(sizeof *stack))) {
        PyErr_NoMemory();
        return -1;
    }

    stack->next = *next;
    if (node->content) {
        Py_INCREF(node->content->clean);
        stack->iter = node->content->clean;
        stack->flag = TDI_REPR_STACK_FLAG_IS_CONTENT;
    }
    else {
        if (!(iter = PyObject_GetIter(node->nodes)))
            goto error;

        if (verbose && node->sep) {
            if (!(stack->iter = PyTuple_New(2)))
                goto error_iter;
            Py_INCREF(node->sep);
            PyTuple_SET_ITEM(stack->iter, 0, node->sep);
            PyTuple_SET_ITEM(stack->iter, 1, iter);
            stack->flag = TDI_REPR_STACK_FLAG_SEPARATOR;
        }
        else {
            stack->iter = iter;
            stack->flag = 0;
        }
    }
    stack->length = (*next ? (*next)->length : 0) + 1;
    *next = stack;

    return 0;

error_iter:
    Py_DECREF(iter);
error:
    PyMem_Free(stack);
    return -1;
}

/*
 * Compute content result
 */
static PyObject *
repriter_next__content(tdi_repr_stack_t *stack, PyObject *content)
{
    PyObject *result, *tmp;
    char *source, *target;
    Py_ssize_t length, rsize, level;

    if (PY_SSIZE_T_MAX - stack->length < stack->length) {
        PyErr_SetString(PyExc_OverflowError, "Exceeded buffer size");
        return NULL;
    }
    if (!(result = PyObject_Repr(content)))
        return NULL;
    if ((length = PyString_Size(result)) == -1) {
        Py_DECREF(result);
        return NULL;
    }
    level = stack->length * 2;
    rsize = level + ((length >= 35) ? 35 : length);
    if (!(tmp = PyString_FromStringAndSize(NULL, rsize))) {
        Py_DECREF(result);
        return NULL;
    }
    target = PyString_AS_STRING(tmp);
    source = PyString_AS_STRING(result);
    (void)memset(target, ' ', (size_t)level);
    target += level;
    if (length < 35)
        (void)memcpy(target, source, (size_t)length);
    else {
        (void)memcpy(target, source, 16);
        target += 16;
        *target++ = '.';
        *target++ = '.';
        *target++ = '.';
        (void)memcpy(target, source + length - 16, 16);
    }
    Py_DECREF(result);

    return tmp;
}

/*
 * Compute node result
 */
static PyObject *
repriter_next__node(tdi_repr_stack_t *stack, tdi_node_t *node,
                    int verbose, int sep)
{
    PyObject *result;
    char *target;
    Py_ssize_t length, rsize, level;

    if (PY_SSIZE_T_MAX - stack->length < stack->length) {
        PyErr_SetString(PyExc_OverflowError, "Exceeded buffer size");
        return NULL;
    }
    level = stack->length * 2;
    rsize = level + (sep ? 1 : 0); /* ":" */
    if (node->name) {
        if ((length = PyString_Size(node->name)) == -1)
            return NULL;
        rsize += length;
    }
    if (!verbose && node->sep)
        rsize += 4; /* " (:)" */
    if (verbose && node->overlay) {
        if ((length = PyString_Size(node->overlay->name)) == -1)
            return NULL;
        rsize += length;
        if (node->overlay->is_hidden)
            ++rsize;
        if (node->overlay->is_target)
            ++rsize;
        if (node->overlay->is_source)
            ++rsize;
        rsize += 7; /* " (<<< )" */
    }

    if (!(result = PyString_FromStringAndSize(NULL, rsize)))
        return NULL;
    target = PyString_AS_STRING(result);
    (void)memset(target, ' ', (size_t)level);
    target += level;
    if (sep)
        *target++ = ':';
    if (node->name) {
        length = PyString_GET_SIZE(node->name);
        (void)memcpy(target, PyString_AS_STRING(node->name), (size_t)length);
        target += length;
    }
    if (!verbose && node->sep) {
        *target++ = ' ';
        *target++ = '(';
        *target++ = ':';
        *target++ = ')';
    }
    if (verbose && node->overlay) {
        *target++ = ' ';
        *target++ = '(';
        *target++ = '<';
        *target++ = '<';
        *target++ = '<';
        *target++ = ' ';
        if (node->overlay->is_hidden)
            *target++ = '-';
        if (node->overlay->is_target)
            *target++ = '>';
        if (node->overlay->is_source)
            *target++ = '<';
        length = PyString_GET_SIZE(node->overlay->name);
        (void)memcpy(target, PyString_AS_STRING(node->overlay->name),
                     (size_t)length);
        target += length;
        *target++ = ')';
    }

    return result;
}

/*
 * Get next representation line
 */
PyObject *
tdi_repr_next(tdi_repr_t *self)
{
    PyObject *tmp;
    tdi_node_t *node;

    switch (self->stage) {
    case TDI_RP_STAGE_BEGIN:
        self->stage = TDI_RP_STAGE_NEXTNODE;
        return PyString_FromString("/");

    case TDI_RP_STAGE_NEXTNODE:
    tdi_rp_stage_nextnode:
        if (!self->stack) {
            self->stage = TDI_RP_STAGE_END;
            goto tdi_rp_stage_end;
        }
        switch (self->stack->flag) {
        case TDI_REPR_STACK_FLAG_IS_CONTENT:
            if (!self->verbose)
                tmp = NULL;
            else if (!(tmp = repriter_next__content(self->stack,
                                                    self->stack->iter)))
                goto exit;
            tdi_repr_stack_pop(&self->stack);
            if (!tmp)
                goto tdi_rp_stage_nextnode;
            return tmp;

        case TDI_REPR_STACK_FLAG_SEPARATOR:
            node = (tdi_node_t *)PyTuple_GET_ITEM(self->stack->iter, 0);
            Py_INCREF(node);
            tmp = PyTuple_GET_ITEM(self->stack->iter, 1);
            Py_INCREF(tmp);
            Py_CLEAR(self->stack->iter);
            self->stack->iter = tmp;
            self->stack->flag = 0;
            tmp = repriter_next__node(self->stack, (tdi_node_t *)node,
                                      self->verbose, 1);
            Py_DECREF(node);
            return tmp;

        default:
            if (!(node = (tdi_node_t *)PyIter_Next(self->stack->iter))) {
                if (PyErr_Occurred())
                    goto exit;
                tdi_repr_stack_pop(&self->stack);
                goto tdi_rp_stage_nextnode;
            }
            if (node->kind == TEXT_NODE) {
                if (self->verbose) {
                    tmp = repriter_next__content(self->stack,
                                                 node->content->clean);
                    Py_DECREF(node);
                    if (!tmp)
                        goto exit;
                    return tmp;
                }
                goto tdi_rp_stage_nextnode;
            }
            tmp = repriter_next__node(self->stack, node, self->verbose, 0);
            if (tdi_repr_stack_push(&self->stack, node, self->verbose) == -1) {
                Py_DECREF(node);
                goto exit;
            }
            Py_DECREF(node);
            return tmp;
        }

    case TDI_RP_STAGE_END:
    tdi_rp_stage_end:
        self->stage = TDI_RP_STAGE_DONE;
        return PyString_FromString("\\");

    case TDI_RP_STAGE_DONE:
        goto exit;
    }

exit:
    return NULL;
}


/*
 * Compute representation
 */
PyObject *
tdi_repr_do(tdi_node_t *root, int verbose)
{
    PyObject *result, *reslist, *item, *iter;
    int subresult;

    if (!(reslist = PyList_New(0)))
        return NULL;

    Py_INCREF(root);
    iter = tdi_repr_iterator_new(root, verbose);
    Py_DECREF(root);
    if (!iter)
        goto error;

    while ((item = PyIter_Next(iter))) {
        subresult = PyList_Append(reslist, item);
        Py_DECREF(item);
        if (subresult == -1)
            break;
    }
    Py_DECREF(iter);
    if (PyErr_Occurred())
        goto error;
    if (PyList_Append(reslist, tdi_g_empty) == -1)
        goto error;

    result = PyObject_CallMethod(tdi_g_newline, "join", "O", reslist);
    Py_DECREF(reslist);
    return result;

error:
    Py_DECREF(reslist);

    return NULL;
}
