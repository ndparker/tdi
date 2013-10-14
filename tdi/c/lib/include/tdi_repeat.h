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

#ifndef TDI_REPEAT_H
#define TDI_REPEAT_H

#include "cext.h"
#include "tdi.h"


/*
 * tdi_repeat_t state (a.k.a. jump target)
 */
typedef enum {
    TDI_RI_STAGE_BEGIN,
    TDI_RI_STAGE_NEXT,
    TDI_RI_STAGE_NODE,
    TDI_RI_STAGE_SEP,
    TDI_RI_STAGE_DONE
} tdi_repeat_stage_t;

/*
 * Object structure for RepeatIteratorType
 */
typedef struct {
    PyObject_HEAD
    PyObject *weakreflist;

    tdi_node_t *node;
    PyObject *callback;
    PyObject *iteritems;
    PyObject *fixed;
    PyObject *sepmodel;
    PyObject *item;
    PyObject *last_item;
    tdi_repeat_stage_t stage;
    Py_ssize_t idx;
} tdi_repeat_t;


/*
 * Get next repetition node
 */
PyObject *
tdi_repeat_next(tdi_repeat_t *self);

#endif
