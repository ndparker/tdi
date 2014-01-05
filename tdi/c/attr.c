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

#include "obj_avoid_gc.h"
#include "obj_attr.h"


/* --------------------- BEGIN TDI_AttrType DEFINITION --------------------- */

#ifndef TDI_AVOID_GC
static int
TDI_AttrType_traverse(tdi_attr_t *self, visitproc visit, void *arg)
{
    Py_VISIT(self->key);
    Py_VISIT(self->value);
    return 0;
}
#endif

static int
TDI_AttrType_clear(tdi_attr_t *self)
{
    Py_CLEAR(self->key);
    Py_CLEAR(self->value);
    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_AttrType)

PyTypeObject TDI_AttrType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".Attr",                            /* tp_name */
    sizeof(tdi_attr_t),                                 /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_AttrType_dealloc,                   /* tp_dealloc */
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
    | TDI_IF_GC(Py_TPFLAGS_HAVE_GC),
    0,                                                  /* tp_doc */
    (traverseproc)TDI_IF_GC(TDI_AttrType_traverse),     /* tp_traverse */
    (inquiry)TDI_IF_GC(TDI_AttrType_clear)              /* tp_clear */
};

/* ---------------------- END TDI_AttrType DEFINITION ---------------------- */

/*
 * Allocate new TDI_AttrType and initialize.
 */
PyObject *
tdi_attr_new(PyObject *key, PyObject *value)
{
    tdi_attr_t *self;

    if (!(self = GENERIC_ALLOC(&TDI_AttrType)))
        return NULL;

    Py_INCREF(key);
    self->key = key;
    Py_INCREF(value);
    self->value = value;

    return (PyObject *)self;
}
