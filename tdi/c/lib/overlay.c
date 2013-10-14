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
#include "tdi_finalize.h"
#include "tdi_overlay.h"
#include "tdi_scope.h"

#include "obj_node.h"
#include "obj_template_node.h"
#include "obj_root_node.h"

/*
 * Overlay stack
 */
typedef struct tdi_overlay_stack_t tdi_overlay_stack_t;
struct tdi_overlay_stack_t {
    tdi_overlay_stack_t *next;  /* Next item on stack */
    PyObject *nodes;            /* Target node list to append to */
    PyObject *iter;             /* Source node iterator */
    int in_overlay;             /* in_overlay state to recall */
};


/*
 * Copy overlay struct
 */
tdi_overlay_t *
tdi_overlay_copy(tdi_overlay_t *overlay)
{
    tdi_overlay_t *new_tdi_overlay;

    if (!overlay)
        return NULL;
    if (!(new_tdi_overlay = PyMem_Malloc(sizeof *new_tdi_overlay))) {
        PyErr_NoMemory();
        return NULL;
    }

    Py_INCREF(overlay->name);
    new_tdi_overlay->name = overlay->name;
    new_tdi_overlay->is_hidden = overlay->is_hidden;
    new_tdi_overlay->is_target = overlay->is_target;
    new_tdi_overlay->is_source = overlay->is_source;

    return new_tdi_overlay;
}

/*
 * Allocate new tdi_overlay_t struct
 */
tdi_overlay_t *
tdi_overlay_new(PyObject *name, int hidden, int source, int target)
{
    tdi_overlay_t *new_tdi_overlay;

    if (!(new_tdi_overlay = PyMem_Malloc(sizeof *new_tdi_overlay))) {
        Py_DECREF(name);
        PyErr_NoMemory();
        return NULL;
    }

    new_tdi_overlay->name = name;
    new_tdi_overlay->is_hidden = hidden;
    new_tdi_overlay->is_source = source;
    new_tdi_overlay->is_target = target;

    return new_tdi_overlay;
}

/*
 * Pop from overlay stack
 */
static void
tdi_overlay_stack_pop(tdi_overlay_stack_t **stack)
{
    if (*stack) {
        tdi_overlay_stack_t *tmp;

        tmp = *stack;
        *stack = tmp->next;
        Py_CLEAR(tmp->nodes);
        Py_CLEAR(tmp->iter);
        PyMem_Free(tmp);
    }
}

/*
 * Push to overlay stack
 */
static int
tdi_overlay_stack_push(tdi_overlay_stack_t **next, tdi_node_t *target,
                       tdi_node_t *source, int in_overlay)
{
    tdi_overlay_stack_t *stack;

    if (!(stack = PyMem_Malloc(sizeof *stack))) {
        PyErr_NoMemory();
        return -1;
    }

    stack->next = *next;
    if (!(stack->iter = PyObject_GetIter(source->nodes))) {
        PyMem_Free(stack);
        return -1;
    }
    Py_INCREF(target->nodes);
    stack->nodes = target->nodes;
    stack->in_overlay = in_overlay;
    *next = stack;

    return 0;
}

/*
 * Raise ambiguous overlay error
 */
static void
overlay_do__raise_ambiguous(PyObject *name)
{
    PyObject *tmp;
    const char *cname;

    if ((tmp = PyObject_Repr(name))) {
        cname = PyString_AsString(tmp);
        if (cname)
            PyErr_Format(TDI_E_NodeTreeError, "Ambiguous overlay %s", cname);
        Py_DECREF(tmp);
    }
}

/*
 * Clone node, but with empty child node list
 */
static tdi_node_t *
overlay_do__clone(tdi_node_t *source, PyTypeObject *pytype)
{
    tdi_node_t *target;

    if (!(target = GENERIC_ALLOC(pytype)))
        return NULL;

#define CLONE(op) do {       \
    Py_XINCREF((PyObject *)source->op);  \
    target->op = source->op; \
} while(0)

    CLONE(sep);
    CLONE(callback);
    CLONE(complete);
    CLONE(namedict);
    CLONE(tagname);
    CLONE(attr);
    CLONE(endtag);
    CLONE(name);
    CLONE(encoder);
    CLONE(decoder);

#undef CLONE

    if (!(target->nodes = PyList_New(0)))
        goto error;
    target->overlay = tdi_overlay_copy(source->overlay);
    if (PyErr_Occurred())
        goto error;
    target->scope = tdi_scope_copy(source->scope);
    if (PyErr_Occurred())
        goto error;
    target->content = tdi_content_copy(source->content);
    if (PyErr_Occurred())
        goto error;

    target->flags = source->flags & ~NODE_FINALIZED;
    target->kind = source->kind;

    return target;

error:
    Py_DECREF(target);
    return NULL;
}

/*
 * Transfer node to new tree or target
 */
static int
overlay_do__transfer(tdi_node_t *node, PyObject *oindex,
                     int *in_overlay, tdi_overlay_stack_t **stack,
                     tdi_node_t **target)
{
    PyObject *name, *tmp;
    tdi_node_t *newnode;
    tdi_scope_t *scope;
    int old_io, sepres;

    if (!node) {
        if (target)
            Py_CLEAR(*target);
        return 0;
    }
    Py_INCREF(node);
    old_io = *in_overlay;
    Py_XINCREF(node->name);
    name = node->name;
    scope = node->scope;
    if (!old_io && node->overlay && !node->overlay->is_source) {
        if (!(tmp = PyDict_GetItem(oindex, node->overlay->name))) {
            if (PyErr_Occurred())
                goto error_name;
        }
        else if (tmp == Py_None) {
            overlay_do__raise_ambiguous(node->overlay->name);
            goto error_name;
        }
        else {
            Py_INCREF(tmp);
            Py_DECREF(node);
            node = (tdi_node_t *)tmp;
            *in_overlay = 1;
        }
    }
    if (!(newnode = overlay_do__clone(node, &TDI_TemplateNodeType)))
        goto error_name;
    if (name) {
        Py_INCREF(name);
        Py_CLEAR(newnode->name);
        newnode->name = name;
    }
    if (scope) {
        scope = tdi_scope_copy(scope);
        if (PyErr_Occurred())
            goto error_newnode;
        TDI_SCOPE_CLEAR(newnode->scope);
        newnode->scope = scope;
    }

    if (target) {
        Py_INCREF(newnode);
        Py_CLEAR(*target);
        *target = newnode;
    }
    else {
        if (PyList_Append((*stack)->nodes, (PyObject *)newnode) == -1)
            goto error_newnode;
    }
    if (tdi_overlay_stack_push(stack, newnode, node, old_io) == -1)
        goto error_newnode;

    Py_XDECREF(name);
    Py_DECREF(node);
    sepres = overlay_do__transfer((tdi_node_t *)newnode->sep, oindex,
                                  in_overlay, stack,
                                  (tdi_node_t **)&newnode->sep);
    Py_DECREF(newnode);
    return sepres;

error_newnode:
    Py_DECREF(newnode);
error_name:
    Py_XDECREF(name);
    Py_DECREF(node);
    return -1;
}

/*
 * Do overlay
 */
tdi_node_t *
tdi_overlay_do(tdi_node_t *root, PyObject *oindex)
{
    tdi_node_t *result, *node;
    tdi_overlay_stack_t *stack = NULL;
    int in_overlay, subresult;

    if (!(result = overlay_do__clone(root, &TDI_RootNodeType)))
        return NULL;
    if (tdi_overlay_stack_push(&stack, result, root, 0) == -1)
        goto error;

    in_overlay = 0;
    while (stack) {
        if (!(node = (tdi_node_t *)PyIter_Next(stack->iter))) {
            if (PyErr_Occurred())
                goto error_stack;
            in_overlay = stack->in_overlay;
            tdi_overlay_stack_pop(&stack);
        }
        else if (node->kind == TEXT_NODE) {
            subresult = PyList_Append(stack->nodes, (PyObject *)node);
            Py_DECREF(node);
            if (subresult == -1)
                goto error_stack;
        }
        else {
            subresult = overlay_do__transfer(node, oindex, &in_overlay,
                                             &stack, NULL);
            Py_DECREF(node);
            if (subresult == -1)
                goto error_stack;
        }
    }

    Py_INCREF((PyObject *)result->encoder);
    Py_INCREF((PyObject *)result->decoder);
    if (tdi_finalize_tree(result, result->encoder, result->decoder) == -1)
        goto error;

    return result;

error_stack:
    while (stack)
        tdi_overlay_stack_pop(&stack);
error:
    Py_DECREF(result);
    return NULL;
}
