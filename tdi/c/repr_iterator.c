/*
 * Copyright 2006 - 2010
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
#include "tdi_repr.h"

#include "obj_repr_iter.h"

/* ----------------- BEGIN TDI_ReprIteratorType DEFINITION ----------------- */

#define TDI_ReprIteratorType_iternext tdi_repr_next
#define TDI_ReprIteratorType_iter PyObject_SelfIter

static int
TDI_ReprIteratorType_traverse(tdi_repr_t *self, visitproc visit, void *arg)
{
    TDI_REPR_STACK_VISIT(self->stack);

    return 0;
}

static int
TDI_ReprIteratorType_clear(tdi_repr_t *self)
{
    TDI_REPR_STACK_CLEAR(self->stack);

    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_ReprIteratorType)

PyTypeObject TDI_ReprIteratorType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".ReprIterator",                    /* tp_name */
    sizeof(tdi_repr_t),                                 /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_ReprIteratorType_dealloc,           /* tp_dealloc */
    0,                                                  /* tp_print */
    0,                                                  /* tp_getattr */
    0,                                                  /* tp_setattr */
    0,                                                  /* tp_compare */
    0,                                                  /* tp_repr */
    0,                                                  /* tp_as_number */
    0,                                                  /* tp_as_sequence */
    0,                                                  /* tp_as_mapping */
    0,                                                  /* tp_hash */
    0,                                                  /* tp_call */
    0,                                                  /* tp_str */
    0,                                                  /* tp_getattro */
    0,                                                  /* tp_setattro */
    0,                                                  /* tp_as_buffer */
    Py_TPFLAGS_HAVE_CLASS                               /* tp_flags */
    | Py_TPFLAGS_HAVE_ITER
    | Py_TPFLAGS_HAVE_GC,
    0,                                                  /* tp_doc */
    (traverseproc)TDI_ReprIteratorType_traverse,        /* tp_traverse */
    (inquiry)TDI_ReprIteratorType_clear,                /* tp_clear */
    0,                                                  /* tp_richcompare */
    0,                                                  /* tp_weaklistoffset */
    (getiterfunc)TDI_ReprIteratorType_iter,             /* tp_iter */
    (iternextfunc)TDI_ReprIteratorType_iternext,        /* tp_iternext */
};

/* ------------------ END TDI_ReprIteratorType DEFINITION ------------------ */

/*
 * Create new representation iterator object
 */
PyObject *
tdi_repr_iterator_new(tdi_node_t *startnode, int verbose)
{
    tdi_repr_t *self;

    if (!(self = GENERIC_ALLOC(&TDI_ReprIteratorType)))
        return NULL;

    self->stage = TDI_RP_STAGE_BEGIN;
    self->verbose = verbose;
    if (tdi_repr_stack_push(&self->stack, startnode, verbose) == -1) {
        Py_DECREF(self);
        return NULL;
    }

    return (PyObject *)self;
}
