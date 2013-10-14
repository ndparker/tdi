/*
 * Copyright 2010
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

#ifndef TDI_RENDER_H
#define TDI_RENDER_H

#include "cext.h"
#include "tdi.h"

/*
 * Render stack structure
 */
typedef struct tdi_render_stack_t tdi_render_stack_t;
struct tdi_render_stack_t {
    tdi_render_stack_t *next;  /* Next item on stack */
    PyObject *iter;            /* Node iterator */
    PyObject *endtag;          /* Endtag (or NULL) */
    int done;                  /* done state to recall */
};

#define TDI_RENDER_STACK_VISIT(stack) do { \
    tdi_render_stack_t *tmp__ = (stack);   \
    while (tmp__) {                        \
        Py_VISIT(tmp__->iter);             \
        Py_VISIT(tmp__->endtag);           \
        tmp__ = tmp__->next;               \
    }                                      \
} while (0)

#define TDI_RENDER_STACK_CLEAR(stack) do { \
    tdi_render_stack_t *tmp__;             \
    while (stack) {                        \
        tmp__ = (stack);                   \
        (stack) = tmp__->next;             \
        Py_DECREF(tmp__->iter);            \
        Py_XDECREF(tmp__->endtag);         \
        PyMem_Free(tmp__);                 \
    }                                      \
} while (0)


/*
 * tdi_render_t state (a.k.a. jump target)
 */
typedef enum {
    TDI_RE_STAGE_ONLY_CONTENT,
    TDI_RE_STAGE_BEGIN,
    TDI_RE_STAGE_NEXTNODE,
    TDI_RE_STAGE_ENDTAG,
    TDI_RE_STAGE_CONTENT,

    TDI_RE_STAGE_DONE
} tdi_render_stage_t;


/*
 * Object structure for RenderIteratorType
 */
struct tdi_render_t {
    PyObject_HEAD
    PyObject *weakreflist;

    PyObject *model;
    PyObject *endtag;
    PyObject *content;
    tdi_render_stack_t *stack;
    int done;
    int emit_escaped;
    tdi_render_stage_t stage;
};


/*
 * Push to render stack
 */
int
tdi_render_stack_push(tdi_render_stack_t **next, PyObject *iter,
                      PyObject *endtag, int done);

/*
 * Node iterator
 *
 * iteritems and separate references are stolen.
 */
PyObject *
tdi_render_iterate(tdi_node_t *self, PyObject *iteritems, PyObject *separate);

/*
 * Get next rendered chunk
 */
PyObject *
tdi_render_next(tdi_render_t *self);

#endif
