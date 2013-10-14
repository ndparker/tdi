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

#ifndef TDI_REPR_H
#define TDI_REPR_H

#include "cext.h"
#include "tdi.h"

typedef enum {
    TDI_REPR_STACK_FLAG_IS_CONTENT = 1,
    TDI_REPR_STACK_FLAG_SEPARATOR
} tdi_repr_stack_flag_t;


/*
 * Repr stack structure
 */
typedef struct tdi_repr_stack_t tdi_repr_stack_t;
struct tdi_repr_stack_t {
    tdi_repr_stack_t *next;      /* Next item on stack */
    PyObject *iter;              /* Node iterator */
    Py_ssize_t length;           /* Stack length */
    tdi_repr_stack_flag_t flag;  /* Flag */
};

#define TDI_REPR_STACK_VISIT(stack) do { \
    tdi_repr_stack_t *tmp__ = (stack);   \
    while (tmp__) {                      \
        Py_VISIT(tmp__->iter);           \
        tmp__ = tmp__->next;             \
    }                                    \
} while (0)

#define TDI_REPR_STACK_CLEAR(stack) do { \
    tdi_repr_stack_t *tmp__;             \
    while (stack) {                      \
        tmp__ = (stack);                 \
        (stack) = tmp__->next;           \
        Py_DECREF(tmp__->iter);          \
        PyMem_Free(tmp__);               \
    }                                    \
} while (0)



/*
 * tdi_repr_t state (a.k.a. jump target)
 */
typedef enum {
    TDI_RP_STAGE_BEGIN,
    TDI_RP_STAGE_NEXTNODE,
    TDI_RP_STAGE_END,

    TDI_RP_STAGE_DONE
} tdi_repr_stage_t;


/*
 * Object structure for ReprIteratorType
 */
struct tdi_repr_t {
    PyObject_HEAD

    tdi_repr_stack_t *stack;
    tdi_repr_stage_t stage;
    int verbose;
};

/*
 * Push to repr stack
 */
int
tdi_repr_stack_push(tdi_repr_stack_t **next, tdi_node_t *node,
                    int verbose);


/*
 * Get next representation line
 */
PyObject *
tdi_repr_next(tdi_repr_t *self);

/*
 * Compute representation
 */
PyObject *
tdi_repr_do(tdi_node_t *root, int verbose);

#endif
