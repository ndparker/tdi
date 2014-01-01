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
#include "tdi_repeat.h"

#include "obj_repeat_iter.h"

/* ----------------- BEGIN TDI_RepeatIteratorType DEFINITION --------------- */

#define TDI_RepeatIteratorType_iternext tdi_repeat_next
#define TDI_RepeatIteratorType_iter PyObject_SelfIter

static int
TDI_RepeatIteratorType_traverse(tdi_repeat_t *self, visitproc visit,
                                void *arg)
{
    Py_VISIT((PyObject *)self->node);
    Py_VISIT(self->callback);
    Py_VISIT(self->iteritems);
    Py_VISIT(self->fixed);
    Py_VISIT(self->sepmodel);
    Py_VISIT(self->item);
    Py_VISIT(self->last_item);

    return 0;
}

static int
TDI_RepeatIteratorType_clear(tdi_repeat_t *self)
{
    if (self->weakreflist)
        PyObject_ClearWeakRefs((PyObject *)self);
    Py_CLEAR(self->node);
    Py_CLEAR(self->callback);
    Py_CLEAR(self->iteritems);
    Py_CLEAR(self->fixed);
    Py_CLEAR(self->sepmodel);
    Py_CLEAR(self->item);
    Py_CLEAR(self->last_item);

    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_RepeatIteratorType)

PyTypeObject TDI_RepeatIteratorType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".RepeatIterator",                  /* tp_name */
    sizeof(tdi_repeat_t),                               /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_RepeatIteratorType_dealloc,         /* tp_dealloc */
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
    (traverseproc)TDI_RepeatIteratorType_traverse,      /* tp_traverse */
    (inquiry)TDI_RepeatIteratorType_clear,              /* tp_clear */
    0,                                                  /* tp_richcompare */
    offsetof(tdi_repeat_t, weakreflist),                /* tp_weaklistoffset */
    (getiterfunc)TDI_RepeatIteratorType_iter,           /* tp_iter */
    (iternextfunc)TDI_RepeatIteratorType_iternext,      /* tp_iternext */
};

/* ------------------ END TDI_RepeatIteratorType DEFINITION ---------------- */

/*
 * Create new repeat iterator object
 */
PyObject *
tdi_repeat_iterator_new(tdi_node_t *node, PyObject *callback,
                        PyObject *itemlist, PyObject *fixed,
                        PyObject *separate)
{
    tdi_repeat_t *self;

    if (!(self = GENERIC_ALLOC(&TDI_RepeatIteratorType))) {
        Py_DECREF(separate);
        Py_DECREF(fixed);
        Py_DECREF(itemlist);
        Py_DECREF(callback);
        Py_DECREF((PyObject *)node);
        return NULL;
    }

    self->node = node;
    self->callback = callback;
    self->iteritems = itemlist;
    self->fixed = fixed;
    if (separate == Py_None)
        Py_DECREF(separate);
    else
        self->sepmodel = separate;
    self->stage = TDI_RI_STAGE_BEGIN;

    return (PyObject *)self;
}
