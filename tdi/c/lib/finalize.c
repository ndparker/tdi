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
#include "tdi_exceptions.h"
#include "tdi_finalize.h"
#include "tdi_globals.h"
#include "tdi_overlay.h"
#include "tdi_scope.h"

#include "obj_attr.h"
#include "obj_encoder.h"
#include "obj_decoder.h"
#include "obj_node.h"
#include "obj_template_node.h"


/*
 * Finalize stack
 */
typedef struct tdi_finalize_stack_t tdi_finalize_stack_t;
struct tdi_finalize_stack_t {
    tdi_finalize_stack_t *next;  /* Next item on stack */
    tdi_node_t *node;            /* Current node */
    PyObject *iter;              /* Child node iterator */
    PyObject *nodes;             /* Node collector (list) */
    PyObject *seps;              /* Separator collector (dict) */
    PyObject *sepname;           /* Separator node, we're inside (or NULL) */
    PyObject *modelscope;        /* Scope */
};


/*
 * Pop from finalize stack
 */
static void
tdi_finalize_stack_pop(tdi_finalize_stack_t **stack)
{
    if (*stack) {
        tdi_finalize_stack_t *tmp;

        tmp = *stack;
        *stack = tmp->next;
        Py_CLEAR(tmp->node);
        Py_CLEAR(tmp->iter);
        Py_CLEAR(tmp->nodes);
        Py_CLEAR(tmp->seps);
        Py_CLEAR(tmp->sepname);
        Py_CLEAR(tmp->modelscope);
        PyMem_Free(tmp);
    }
}

/*
 * Push to finalize stack
 *
 * node will be stolen.
 */
static int
tdi_finalize_stack_push(tdi_finalize_stack_t **next, tdi_node_t *node,
                        PyObject *sepname, PyObject *modelscope)
{
    tdi_finalize_stack_t *stack;

    if (!(stack = PyMem_Malloc(sizeof *stack)))
        goto error;
    if (!(stack->nodes = PyList_New(0)))
        goto error_stack;
    if (!(stack->seps = PyDict_New()))
        goto error_nodes;
    if (!(stack->iter = PyObject_GetIter(node->nodes)))
        goto error_seps;

    stack->node = node;
    Py_XINCREF(sepname);
    stack->sepname = sepname;
    Py_XINCREF(modelscope);
    stack->modelscope = modelscope;
    stack->next = *next;
    *next = stack;

    return 0;

error_seps:
    Py_DECREF(stack->seps);
error_nodes:
    Py_DECREF(stack->nodes);
error_stack:
    PyMem_Free(stack);
error:
    Py_DECREF(node);
    return -1;
}

/*
 * Merge scopes
 */
static int
merge_scope(PyObject *current, tdi_scope_t *newscope, PyObject **final)
{
    Py_ssize_t size;
    char *cfinal;

    if (!newscope) {
        Py_XINCREF(current);
        *final = current;
        return 0;
    }
    else if ((newscope->is_absolute) || !current
            || PyString_GET_SIZE(current) == 0) {
        Py_INCREF(newscope->name);
        *final = newscope->name;
        return 0;
    }

    size = PyString_GET_SIZE(current);
    if (size <= (PY_SSIZE_T_MAX - 1))
        size += 1;
    else {
        PyErr_SetNone(PyExc_OverflowError);
        return -1;
    }
    if (size <= (PY_SSIZE_T_MAX - PyString_GET_SIZE(newscope->name)))
        size += PyString_GET_SIZE(newscope->name);
    else {
        PyErr_SetNone(PyExc_OverflowError);
        return -1;
    }

    if (!(*final = PyString_FromStringAndSize(NULL, size)))
        return -1;

    cfinal = PyString_AS_STRING(*final);
    (void)memcpy(cfinal, PyString_AS_STRING(current),
                 (size_t)PyString_GET_SIZE(current));
    cfinal += PyString_GET_SIZE(current);
    *cfinal++ = '.';
    (void)memcpy(cfinal, PyString_AS_STRING(newscope->name),
                 (size_t)PyString_GET_SIZE(newscope->name));

    return 0;
}


/*
 * Check for superfluous separator nodes
 *
 * seps is stolen.
 */
static int
finalize_do__finish_level__checkseps(PyObject *seps)
{
    PyObject *keys, *tmp, *iter;
    char *cp;
    Py_ssize_t idx, length;
    int res;

    if ((length = PyDict_Size(seps)) == -1)
        goto error;
    if (length == 0) {
        Py_DECREF(seps);
        return 0;
    }

    if (!(keys = PyDict_Keys(seps)))
        goto error;
    if (!(tmp = PyObject_CallMethod(keys, "sort", "()"))) {
        Py_DECREF(keys);
        goto error;
    }
    Py_DECREF(tmp);
    Py_DECREF(seps);
    if (!(seps = PyList_New(0))) {
        Py_DECREF(keys);
        return -1;
    }
    if (!(iter = PyObject_GetIter(keys))) {
        Py_DECREF(keys);
        goto error;
    }
    Py_DECREF(keys);
    length = 0;
    while ((keys = PyIter_Next(iter))) {
        tmp = PyObject_Repr(keys);
        Py_DECREF(keys);
        if (!tmp)
            break;
        if (PyList_GET_SIZE(seps) > 0)
            length += 2; /* ", " */
        length += PyString_GET_SIZE(tmp);
        res = PyList_Append(seps, tmp);
        Py_DECREF(tmp);
        if (res == -1)
            break;
    }
    Py_DECREF(iter);
    if (PyErr_Occurred())
        goto error;

#define PART1 "Ignoring separator node(s) without accompanying content " \
              "node: "

    length += (Py_ssize_t)sizeof(PART1) - 1;
    if (!(keys = PyString_FromStringAndSize(NULL, length)))
        goto error;
    cp = PyString_AS_STRING(keys);

    (void)memcpy(cp, PART1, sizeof(PART1) - 1);
    cp += sizeof(PART1) - 1;
    for (idx = 0; idx < PyList_GET_SIZE(seps); ++idx) {
        if (idx > 0) {
            *cp++ = ',';
            *cp++ = ' ';
        }
        tmp = PyList_GET_ITEM(seps, idx);
        (void)memcpy(cp, PyString_AS_STRING(tmp),
                     (size_t)PyString_GET_SIZE(tmp));
        cp += PyString_GET_SIZE(tmp);
    }
    Py_DECREF(seps);

#undef PART1

    tmp = PyObject_CallMethod(TDI_E_NodeWarning, "emit", "O", keys);
    Py_DECREF(keys);
    if (!tmp)
        return -1;

    return 0;

error:
    Py_DECREF(seps);
    return -1;
}

/*
 * Normalize attributes
 */
static int
norm_attributes(tdi_node_t *node)
{
    PyObject *result;

    if (node->attr) {
        PyObject *normkey, *attr;
        Py_ssize_t j, length = PyList_GET_SIZE(node->attr);
        int res;

        if (!(result = PyDict_New())) {
            return -1;
        }
        for (j = 0; j < length; ++j) {
            attr = PyList_GET_ITEM(node->attr, j);
            Py_INCREF(attr);
            if (!(normkey = DECODER_NORMALIZE(node,
                                              ((tdi_attr_t *)attr)->key))) {
                Py_DECREF(attr);
                goto error;
            }
            res = PyDict_SetItem(result, normkey, attr);
            Py_DECREF(normkey);
            Py_DECREF(attr);
            if (res == -1) goto error;
        }
        Py_CLEAR(node->attr);
        node->attr = result;
    }
    node->flags &= ~NODE_NEWATTR;

    return 0;

error:
    Py_DECREF(result);
    return -1;
}

/*
 * Finish a stack level
 */
static int
finalize_do__finish_level(tdi_finalize_stack_t **stack,
                          tdi_encoder_t *encoder, tdi_decoder_t *decoder,
                          PyObject *separated)
{
    PyObject *nodes, *seps, *modelscope, *tmp, *tmp2, *names, *name;
    PyObject *nameless = NULL;
    tdi_node_t *node, *tmp_node;
    Py_ssize_t idx, length;
    int res;

    node = (*stack)->node;
    Py_INCREF(node);
    nodes = (*stack)->nodes;
    Py_INCREF(nodes);
    seps = (*stack)->seps;
    Py_INCREF(seps);
    if (!(modelscope = (*stack)->modelscope))
        modelscope = tdi_g_empty;
    Py_INCREF(modelscope);
    tdi_finalize_stack_pop(stack);

    if (!(names = PyDict_New()))
        goto error_modelscope;
    Py_CLEAR(node->namedict);
    node->namedict = names;
    Py_INCREF(encoder);
    Py_CLEAR(node->encoder);
    node->encoder = encoder;
    Py_INCREF(decoder);
    Py_CLEAR(node->decoder);
    node->decoder = decoder;
    Py_CLEAR(node->modelscope);
    node->modelscope = modelscope;
    Py_CLEAR(node->nodes);
    if (node->flags & NODE_NEWATTR) {
        norm_attributes(node);
    }

    /* Fast exit: Optimize for text-only content */
    if (PyList_GET_SIZE(nodes) == 0) {
        if (!node->content) {
            if (!(node->content = tdi_content_new()))
                goto error;
            Py_INCREF(tdi_g_empty);
            node->content->clean = tdi_g_empty;
            Py_INCREF(tdi_g_empty);
            node->content->with_escapes = tdi_g_empty;
        }
        node->nodes = nodes;
        Py_DECREF(node);
        return finalize_do__finish_level__checkseps(seps);
    }
    else if (PyList_GET_SIZE(nodes) == 1) {
        tmp_node = (tdi_node_t *)PyList_GET_ITEM(nodes, 0);
        if (tmp_node->kind == TEXT_NODE) {
            TDI_CONTENT_CLEAR(node->content);
            node->content = tdi_content_copy(tmp_node->content);
            if (PyErr_Occurred())
                goto error;
            if (!(node->nodes = PyList_New(0)))
                goto error;
            Py_DECREF(nodes);
            Py_DECREF(node);
            return finalize_do__finish_level__checkseps(seps);
        }
    }

    TDI_CONTENT_CLEAR(node->content);
    node->nodes = nodes;
    Py_DECREF(node);

    /*
     * Now assign separator nodes (and push onto stack, so they can be
     * finalized) and collect nameless "ghost" nodes for later addition
     * to the namedict
     */
    if (!(nameless = PyList_New(0)))
        goto error_loop;
    length = PyList_GET_SIZE(nodes);
    for (idx = 0; idx < length; ++idx) {
        /* Skip text nodes (SEP_NODE is not possible at this stage) */
        node = (tdi_node_t *)PyList_GET_ITEM(nodes, idx);
        if (node->kind != PROC_NODE)
            continue;

        /* Record nameless node's namedict */
        if (!node->name) {
            if (PyObject_Cmp(modelscope, node->modelscope, &res) == -1)
                goto error_loop;
            if (res == 0) {
                if (!(tmp = PyTuple_New(2)))
                    goto error_loop;
                if (!(tmp2 = PyInt_FromSsize_t(-1 - idx))) {
                    Py_DECREF(tmp);
                    goto error_loop;
                }
                Py_INCREF(node->namedict);
                PyTuple_SET_ITEM(tmp, 0, tmp2);
                PyTuple_SET_ITEM(tmp, 1, node->namedict);
                res = PyList_Append(nameless, tmp);
                Py_DECREF(tmp);
                if (res == -1)
                    goto error_loop;
            }
            continue;
        }

        /* Assign separator if found on this level and append to stack */
        if ((tmp = PyDict_GetItem(seps, node->name))) {
            Py_INCREF(tmp);
            if (PyDict_DelItem(seps, node->name) == -1) {
                Py_DECREF(tmp);
                goto error_loop;
            }
            ((tdi_node_t *)tmp)->kind = PROC_NODE;
            Py_CLEAR(node->sep);
            node->sep = tmp;
        }
        else if (PyErr_Occurred())
            goto error_loop;
        if (node->sep) {
            Py_INCREF(node->sep);
            if (merge_scope(node->modelscope,
                            ((tdi_node_t *)(node->sep))->scope, &tmp)
                    == -1)
                goto error_loop;
            if (tdi_finalize_stack_push(stack, (tdi_node_t *)node->sep,
                                        node->name, tmp) == -1) {
                Py_DECREF(tmp);
                goto error_loop;
            }
            Py_DECREF(tmp);
            if (PyList_Append(separated, node->sep) == -1)
                goto error_loop;
        }

        /* finally maintain namedict */
        if (PyObject_Cmp(modelscope, node->modelscope, &res) == -1)
            goto error_loop;
        if (res == 0) {
            if (!(tmp = PyInt_FromSsize_t(idx)))
                goto error_loop;
            res = PyDict_SetItem(names, node->name, tmp);
            Py_DECREF(tmp);
            if (res == -1)
                goto error_loop;
        }
    }

    if (finalize_do__finish_level__checkseps(seps) == -1)
        goto error_nameless;

    /*
     * Now add nameless node's children to our namedict (if the names do not
     * exist yet)
     */
    length = PyList_GET_SIZE(nameless);
    while (length-- > 0) {
        tmp = PyList_GET_ITEM(nameless, length);
        if (!(tmp2 = PyDict_Keys(PyTuple_GET_ITEM(tmp, 1))))
            goto error_nameless;
        nodes = PyObject_GetIter(tmp2);
        Py_DECREF(tmp2);
        if (!nodes)
            goto error_nameless;
        while ((name = PyIter_Next(nodes))) {
            if (!(tmp2 = PyDict_GetItem(names, name))) {
                if (PyErr_Occurred()) {
                    Py_DECREF(name);
                    break;
                }
                if (PyDict_SetItem(names, name,
                                   PyTuple_GET_ITEM(tmp, 0)) == -1) {
                    Py_DECREF(name);
                    break;
                }
            }
        }
        Py_DECREF(nodes);
        if (PyErr_Occurred())
            goto error_nameless;
    };

    Py_DECREF(nameless);
    return 0;

error_modelscope:
    Py_DECREF(modelscope);
error:
    Py_DECREF(node);
    Py_DECREF(nodes);
error_loop:
    Py_DECREF(seps);
error_nameless:
    Py_XDECREF(nameless);
    return -1;
}

/*
 * Finalize text node
 *
 * node is stolen.
 */
static int
finalize_do__text(tdi_finalize_stack_t **stack, tdi_node_t *node)
{
    PyObject *nodes;
    tdi_node_t *lastnode;
    Py_ssize_t length;

    nodes = (*stack)->nodes;
    length = PyList_GET_SIZE(nodes);
    if (length > 0) {
        lastnode = (tdi_node_t *)PyList_GET_ITEM(nodes, length - 1);
        /* Concatenate with lastnode */
        if (lastnode->kind == TEXT_NODE) {
            PyObject *content;
            char *cp;
            Py_ssize_t clength;

            clength = PyString_GET_SIZE(lastnode->content->clean)
                    + PyString_GET_SIZE(node->content->clean);
            if (!(content = PyString_FromStringAndSize(NULL, clength)))
                goto error;
            cp = PyString_AS_STRING(content);
            (void)memcpy(cp, PyString_AS_STRING(lastnode->content->clean),
                         (size_t)PyString_GET_SIZE(lastnode->content->clean));
            cp += PyString_GET_SIZE(lastnode->content->clean);
            (void)memcpy(cp, PyString_AS_STRING(node->content->clean),
                         (size_t)PyString_GET_SIZE(node->content->clean));
            Py_CLEAR(lastnode->content->clean);
            lastnode->content->clean = content;

            clength = PyString_GET_SIZE(lastnode->content->with_escapes)
                    + PyString_GET_SIZE(node->content->with_escapes);
            if (!(content = PyString_FromStringAndSize(NULL, clength)))
                goto error;
            cp = PyString_AS_STRING(content);
            (void)memcpy(cp,
                         PyString_AS_STRING(lastnode->content->with_escapes),
                         (size_t)PyString_GET_SIZE(
                                            lastnode->content->with_escapes));
            cp += PyString_GET_SIZE(lastnode->content->with_escapes);
            (void)memcpy(cp, PyString_AS_STRING(node->content->with_escapes),
                         (size_t)PyString_GET_SIZE(
                                                node->content->with_escapes));

            if (   PyString_GET_SIZE(lastnode->content->clean) == clength
                && !memcmp(PyString_AS_STRING(lastnode->content->clean),
                           PyString_AS_STRING(content), clength)) {
                Py_DECREF(content);
                content = lastnode->content->clean;
                Py_INCREF(content);
            }

            Py_CLEAR(lastnode->content->with_escapes);
            lastnode->content->with_escapes = content;

            Py_DECREF(node);
            return 0;
        }
    }
    if (PyList_Append(nodes, (PyObject *)node) == -1)
        goto error;

    Py_DECREF(node);
    return 0;

error:
    Py_DECREF(node);
    return -1;
}

/*
 * Raise missing-endtag error
 */
static int
finalize_do__node__check_endtag(tdi_node_t *node)
{
    PyObject *name = NULL;
    const char *cname;

    if (node->flags & NODE_ROOT || node->endtag)
        return 0;

    if (node->flags & NODE_CLOSED) {
        Py_INCREF(tdi_g_empty);
        node->endtag = tdi_g_empty;
        return 0;
    }

    if (node->name) {
        if (!(name = PyObject_Repr(node->name)))
            return -1;
        if (!(cname = PyString_AsString(name)))
            return -1;
    }
    else
        cname = "None";

    PyErr_Format(TDI_E_NodeTreeError,
                 "endtag was not assigned for node %s", cname);

    Py_XDECREF(name);
    return -1;
}

/*
 * Warn about separator source overlay
 */
static int
finalize_do__node__warn_sepoverlay(PyObject *sepname, PyObject *oname)
{
    PyObject *text, *tmp;
    char *cp;

    if (!(sepname = PyObject_Repr(sepname)))
        return -1;
    if (!(oname = PyObject_Repr(oname))) {
        Py_DECREF(sepname);
        return -1;
    }

#define PART1 "Ignoring source overlay "
#define PART2 " in separator node "

    if (!(text = PyString_FromStringAndSize(NULL,
                                           PyString_GET_SIZE(sepname)
                                         + PyString_GET_SIZE(oname)
                                         + (Py_ssize_t)sizeof(PART1) - 1
                                         + (Py_ssize_t)sizeof(PART2) - 1))) {
        Py_DECREF(oname);
        Py_DECREF(sepname);
        return -1;
    }

    cp = PyString_AS_STRING(text);
    (void)memcpy(cp, PART1, sizeof(PART1) - 1);
    cp += sizeof(PART1) - 1;
    (void)memcpy(cp, PyString_AS_STRING(oname),
                 (size_t)PyString_GET_SIZE(oname));
    cp += PyString_GET_SIZE(oname);
    (void)memcpy(cp, PART2, sizeof(PART2) - 1);
    cp += sizeof(PART2) - 1;
    (void)memcpy(cp, PyString_AS_STRING(sepname),
                 (size_t)PyString_GET_SIZE(sepname));

#undef PART2
#undef PART1

    Py_DECREF(sepname);
    Py_DECREF(oname);
    tmp = PyObject_CallMethod(TDI_E_NodeWarning, "emit", "O", text);
    Py_DECREF(text);
    if (!tmp)
        return -1;

    return 0;
}

/*
 * Finalize proc node
 *
 * node is stolen.
 */
static int
finalize_do__node(tdi_finalize_stack_t **stack, tdi_node_t *node,
                  PyObject *overlays)
{
    PyObject *tmp;
    int res;

    if (finalize_do__node__check_endtag(node) == -1)
        goto error;

    if (node->overlay) {
        if (!node->overlay->is_target) {
            if ((*stack)->sepname) {
                res = finalize_do__node__warn_sepoverlay((*stack)->sepname,
                                                         node->overlay->name);
                if (res == -1)
                    goto error;
            }
            else if ((tmp = PyDict_GetItem(PyTuple_GET_ITEM(overlays, 0),
                                           node->overlay->name))) {
                /* later this will result in "ambiguous overlay" */
                if (PyDict_SetItem(PyTuple_GET_ITEM(overlays, 0),
                                   node->overlay->name, Py_None) == -1)
                    goto error;
            }
            else if (   PyErr_Occurred()
                     || PyDict_SetItem(PyTuple_GET_ITEM(overlays, 0),
                                       node->overlay->name,
                                       (PyObject *)node) == -1) {
                goto error;
            }
        }
        if (!node->overlay->is_source) {
            if ((tmp = PyDict_GetItem(PyTuple_GET_ITEM(overlays, 1),
                                      node->overlay->name))) {
                Py_INCREF(tmp);
            }
            else {
                if (PyErr_Occurred() || !(tmp = PyList_New(0)))
                    goto error;
                if (PyDict_SetItem(PyTuple_GET_ITEM(overlays, 1),
                                   node->overlay->name, tmp) == -1) {
                    Py_DECREF(tmp);
                    goto error;
                }
            }
            res = PyList_Append(tmp, (PyObject *)node);
            Py_DECREF(tmp);
            if (res == -1)
                goto error;
        }
    }

    if (node->kind == SEP_NODE) {
        if (PyDict_SetItem((*stack)->seps, node->name,
                           (PyObject *)node) == -1)
            goto error;
        Py_DECREF(node);
        return 0;
    }

    if (PyList_Append((*stack)->nodes, (PyObject *)node) == -1)
        goto error;
    if (merge_scope((*stack)->modelscope, node->scope, &tmp) == -1)
        goto error;
    res = tdi_finalize_stack_push(stack, node, (*stack)->sepname, tmp);
    Py_XDECREF(tmp);
    return res;

error:
    Py_DECREF(node);
    return -1;
}


/*
 * Optimize separator nodes
 *
 * separated is stolen.
 */
static int
finalize_do__separators(PyObject *separated)
{
    PyObject *iter;
    tdi_node_t *sepnode;

    iter = PyObject_GetIter(separated);
    Py_DECREF(separated);
    if (!iter)
        return -1;

    while ((sepnode = (tdi_node_t *)PyIter_Next(iter))) {
        if (sepnode->content) {
            Py_CLEAR(sepnode->complete);
            if (sepnode->flags & NODE_NOELEMENT) {
                sepnode->complete = tdi_template_node_escaped_text_new(
                                            sepnode->content->clean,
                                            sepnode->content->with_escapes);
                if (!sepnode->complete)
                    goto error;
            }
            else {
                PyObject *clean, *with_escapes;

                if (!(clean = ENCODE_STARTTAG(sepnode)))
                    goto error;
                PyString_Concat(&clean, sepnode->content->clean);
                if (!clean)
                    goto error;
                PyString_Concat(&clean, sepnode->endtag);
                if (!clean)
                    goto error;

                if (!(with_escapes = ENCODE_STARTTAG(sepnode))) {
                    Py_DECREF(clean);
                    goto error;
                }
                PyString_Concat(&with_escapes,
                                sepnode->content->with_escapes);
                if (!with_escapes) {
                    Py_DECREF(clean);
                    goto error;
                }
                PyString_Concat(&with_escapes, sepnode->endtag);
                if (!with_escapes) {
                    Py_DECREF(clean);
                    goto error;
                }
                if (   (PyString_GET_SIZE(clean) ==
                        PyString_GET_SIZE(with_escapes))
                    && !memcmp(PyString_AS_STRING(clean),
                               PyString_AS_STRING(with_escapes),
                               PyString_GET_SIZE(clean))) {
                    Py_DECREF(with_escapes);
                    Py_INCREF(clean);
                    with_escapes = clean;
                }
                sepnode->complete = tdi_template_node_escaped_text_new(
                                                        clean, with_escapes);
                Py_DECREF(clean);
                Py_DECREF(with_escapes);
                Py_DECREF(sepnode);
                if (!sepnode->complete)
                    break;
            }
            continue;

        error:
            Py_DECREF(sepnode);
            break;
        }
    }
    Py_DECREF(iter);
    if (PyErr_Occurred())
        return -1;

    return 0;
}

/*
 * Do finalize - main controller
 *
 * Encoder is being stolen.
 * Decoder is being stolen.
 */
static PyObject *
finalize_do(tdi_node_t *root, tdi_encoder_t *encoder, tdi_decoder_t *decoder)
{
    PyObject *overlays, *separated, *tmp;
    tdi_node_t *node;
    tdi_finalize_stack_t *stack = NULL;

    if (!(overlays = PyTuple_New(2)))
        goto error_encoder;
    if (!(tmp = PyDict_New()))
        goto error_overlays;
    PyTuple_SET_ITEM(overlays, 0, tmp);
    if (!(tmp = PyDict_New()))
        goto error_overlays;
    PyTuple_SET_ITEM(overlays, 1, tmp);
    if (!(separated = PyList_New(0)))
        goto error_overlays;
    Py_INCREF(root);
    if (tdi_finalize_stack_push(&stack, root, NULL, NULL) == -1)
        goto error_separated;

    while (stack) {
        if (!(node = (tdi_node_t *)PyIter_Next(stack->iter))) {
            if (PyErr_Occurred())
                goto error_stack;
            if (finalize_do__finish_level(&stack, encoder, decoder,
                                          separated) == -1)
                goto error_stack;
        }
        else if (node->kind == TEXT_NODE) {
            if (finalize_do__text(&stack, node) == -1)
                goto error_stack;
        }
        else if (finalize_do__node(&stack, node, overlays) == -1)
            goto error_stack;
    }
    if (finalize_do__separators(separated) == -1)
        goto error_overlays;
    Py_DECREF(encoder);
    Py_DECREF(decoder);

    return overlays;

error_stack:
    while (stack)
        tdi_finalize_stack_pop(&stack);
error_separated:
    Py_DECREF(separated);
error_overlays:
    Py_DECREF(overlays);
error_encoder:
    Py_DECREF(encoder);
    Py_DECREF(decoder);
    return NULL;
}

/*
 * finalize tree
 *
 * Encoder is being stolen.
 * Decoder is being stolen.
 */
int
tdi_finalize_tree(tdi_node_t *root, tdi_encoder_t *encoder,
                  tdi_decoder_t *decoder)
{
    if (root->flags & NODE_FINALIZED) {
        Py_DECREF(encoder);
        Py_DECREF(decoder);
        PyErr_SetString(TDI_E_NodeTreeError, "Tree was already finalized");
        return -1;
    }

    Py_CLEAR(root->overlays);
    if (!(root->overlays = finalize_do(root, encoder, decoder)))
        return -1;
    root->flags |= NODE_FINALIZED;

    return 0;
}
