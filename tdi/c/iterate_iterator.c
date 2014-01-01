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
#include "tdi_iterate.h"

#include "obj_iterate_iter.h"

/* ---------------- BEGIN TDI_IterateIteratorType DEFINITION --------------- */

#define TDI_IterateIteratorType_iternext tdi_iterate_next
#define TDI_IterateIteratorType_iter PyObject_SelfIter

static int
TDI_IterateIteratorType_traverse(tdi_iterate_t *self, visitproc visit,
                             void *arg)
{
    Py_VISIT((PyObject *)self->node);
    Py_VISIT(self->nodelist);
    Py_VISIT(self->iteritems);
    Py_VISIT(self->sepmodel);
    Py_VISIT(self->item);
    Py_VISIT(self->last_item);

    return 0;
}

static int
TDI_IterateIteratorType_clear(tdi_iterate_t *self)
{
    if (self->weakreflist)
        PyObject_ClearWeakRefs((PyObject *)self);
    Py_CLEAR(self->node);
    Py_CLEAR(self->nodelist);
    Py_CLEAR(self->iteritems);
    Py_CLEAR(self->sepmodel);
    Py_CLEAR(self->item);
    Py_CLEAR(self->last_item);

    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_IterateIteratorType)

PyTypeObject TDI_IterateIteratorType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".IterateIterator",                 /* tp_name */
    sizeof(tdi_iterate_t),                              /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_IterateIteratorType_dealloc,        /* tp_dealloc */
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
    Py_TPFLAGS_HAVE_WEAKREFS                            /* tp_flags */
    | Py_TPFLAGS_HAVE_CLASS
    | Py_TPFLAGS_HAVE_ITER
    | Py_TPFLAGS_HAVE_GC,
    0,                                                  /* tp_doc */
    (traverseproc)TDI_IterateIteratorType_traverse,     /* tp_traverse */
    (inquiry)TDI_IterateIteratorType_clear,             /* tp_clear */
    0,                                                  /* tp_richcompare */
    offsetof(tdi_iterate_t, weakreflist),               /* tp_weaklistoffset */
    (getiterfunc)TDI_IterateIteratorType_iter,          /* tp_iter */
    (iternextfunc)TDI_IterateIteratorType_iternext,     /* tp_iternext */
};

/* ----------------- END TDI_IterateIteratorType DEFINITION ---------------- */

/*
 * Create new iterate iterator object
 */
PyObject *
tdi_iterate_iterator_new(tdi_node_t *node, PyObject *nodelist,
                         PyObject *iteritems, PyObject *separate)
{
    tdi_iterate_t *self;

    if (!(self = GENERIC_ALLOC(&TDI_IterateIteratorType))) {
        Py_XDECREF(separate);
        Py_DECREF(iteritems);
        Py_DECREF(nodelist);
        Py_DECREF((PyObject *)node);
        return NULL;
    }

    self->node = node;
    self->nodelist = nodelist;
    self->iteritems = iteritems;
    self->sepmodel = separate;
    self->stage = TDI_RI_STAGE_BEGIN;

    return (PyObject *)self;
}
