/*
 * Copyright 2013
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

#include "obj_base_event_filter.h"

typedef struct base_event_filter {
    PyObject_HEAD
    PyObject *weakreflist;

    PyObject *builder;
} base_event_filter;

/* --------------- BEGIN TDI_BaseEventFilterType DEFINITION -------------- */

static PyObject *
TDI_BaseEventFilterType_getattro(base_event_filter *self, PyObject *name)
{
    PyObject *tmp, *attr;
    int res, cmp;

    if (!(tmp = PyObject_GenericGetAttr((PyObject *)self, name))) {
        if (!PyErr_ExceptionMatches(PyExc_AttributeError))
            return NULL;
        PyErr_Clear();
    }
    else
        return tmp;

    if (!(attr = PyString_InternFromString("builder")))
        return NULL;
    res = PyObject_Cmp(attr, name, &cmp);
    Py_DECREF(attr);
    if (res == -1)
        return NULL;
    if (!cmp) {
        if (!self->builder) {
            PyErr_SetObject(PyExc_AttributeError, name);
            return NULL;
        }
        return (Py_INCREF(self->builder), self->builder);
    }

    if (!(attr = PyString_InternFromString("__getattr__")))
        return NULL;
    tmp = PyObject_GenericGetAttr((PyObject *)self, attr);
    Py_DECREF(attr);
    if (tmp) {
        attr = PyObject_CallFunction(tmp, "O", name);
        Py_DECREF(tmp);
        return attr;
    }
    if (!PyErr_ExceptionMatches(PyExc_AttributeError))
        return NULL;
    PyErr_Clear();

    return PyObject_GetAttr(self->builder, name);
}

static int
TDI_BaseEventFilterType_traverse(base_event_filter *self, visitproc visit,
                                 void *arg)
{
    Py_VISIT(self->builder);
    return 0;
}

static int
TDI_BaseEventFilterType_clear(base_event_filter *self)
{
    if (self->weakreflist)
        PyObject_ClearWeakRefs((PyObject *)self);

    Py_CLEAR(self->builder);
    return 0;
}

static int
TDI_BaseEventFilterType_init(base_event_filter *self, PyObject *args,
                             PyObject *kwds)
{
    static char *kwlist[] = {"builder", NULL};
    PyObject *builder;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", kwlist, &builder))
        return -1;

    self->builder = (Py_INCREF(builder), builder);

    return 0;
}

static PyObject *
TDI_BaseEventFilterType_new(PyTypeObject *type, PyObject *args,
                            PyObject *kwds)
{
    return (PyObject *)GENERIC_ALLOC(type);
}

DEFINE_GENERIC_DEALLOC(TDI_BaseEventFilterType)

PyDoc_STRVAR(TDI_BaseEventFilterType__doc__,
"Base event filter class, which actually passes everything unfiltered\n\
\n\
Override the event handlers you need.\n\
\n\
:See: `BuildingListenerInterface`\n\
\n\
:IVariables:\n\
  `builder` : `BuildingListenerInterface`\n\
    The next level builder");

PyTypeObject TDI_BaseEventFilterType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".BaseEventFilter",                 /* tp_name */
    sizeof(base_event_filter),                          /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_BaseEventFilterType_dealloc,        /* tp_dealloc */
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
    (getattrofunc)TDI_BaseEventFilterType_getattro,     /* tp_getattro */
    0,                                                  /* tp_setattro */
    0,                                                  /* tp_as_buffer */
    Py_TPFLAGS_HAVE_WEAKREFS                            /* tp_flags */
    | Py_TPFLAGS_HAVE_CLASS
    | Py_TPFLAGS_BASETYPE
    | Py_TPFLAGS_HAVE_GC
    ,
    TDI_BaseEventFilterType__doc__,                     /* tp_doc */
    (traverseproc)TDI_BaseEventFilterType_traverse,     /* tp_traverse */
    (inquiry)TDI_BaseEventFilterType_clear,             /* tp_clear */
    0,                                                  /* tp_richcompare */
    offsetof(base_event_filter, weakreflist),           /* tp_weaklistoffset */
    0,                                                  /* tp_iter */
    0,                                                  /* tp_iternext */
    0,                                                  /* tp_methods */
    0,                                                  /* tp_members */
    0,                                                  /* tp_getset */
    0,                                                  /* tp_base */
    0,                                                  /* tp_dict */
    0,                                                  /* tp_descr_get */
    0,                                                  /* tp_descr_set */
    0,                                                  /* tp_dictoffset */
    (initproc)TDI_BaseEventFilterType_init,             /* tp_init */
    0,                                                  /* tp_alloc */
    TDI_BaseEventFilterType_new,                        /* tp_new */
};

/* ---------------- END TDI_BaseEventFilterType DEFINITION --------------- */
