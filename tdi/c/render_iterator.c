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

#include "tdi_content.h"
#include "tdi_copy.h"
#include "tdi_render.h"

#include "obj_model_adapters.h"
#include "obj_node.h"
#include "obj_render_iter.h"


/* ---------------- BEGIN TDI_RenderIteratorType DEFINITION ---------------- */

#define TDI_RenderIteratorType_iternext tdi_render_next
#define TDI_RenderIteratorType_iter PyObject_SelfIter

static int
TDI_RenderIteratorType_traverse(tdi_render_t *self, visitproc visit,
                                void *arg)
{
    Py_VISIT(self->model);
    Py_VISIT(self->endtag);
    Py_VISIT(self->content);
    TDI_RENDER_STACK_VISIT(self->stack);

    return 0;
}

static int
TDI_RenderIteratorType_clear(tdi_render_t *self)
{
    if (self->weakreflist)
        PyObject_ClearWeakRefs((PyObject *)self);
    Py_CLEAR(self->model);
    Py_CLEAR(self->endtag);
    Py_CLEAR(self->content);
    TDI_RENDER_STACK_CLEAR(self->stack);

    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_RenderIteratorType)

PyTypeObject TDI_RenderIteratorType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".RenderIterator",                  /* tp_name */
    sizeof(tdi_render_t),                               /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_RenderIteratorType_dealloc,         /* tp_dealloc */
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
    (traverseproc)TDI_RenderIteratorType_traverse,      /* tp_traverse */
    (inquiry)TDI_RenderIteratorType_clear,              /* tp_clear */
    0,                                                  /* tp_richcompare */
    offsetof(tdi_render_t, weakreflist),                /* tp_weaklistoffset */
    (getiterfunc)TDI_RenderIteratorType_iter,           /* tp_iter */
    (iternextfunc)TDI_RenderIteratorType_iternext,      /* tp_iternext */
};

/* ----------------- END TDI_RenderIteratorType DEFINITION ----------------- */

/*
 * Determine rootnodes to render
 */
static PyObject *
find_rootnodes(tdi_node_t *startnode, tdi_adapter_t *model)
{
    PyObject *list, *item = NULL, *iter = NULL;

    if (!(list = PyList_New(0)))
        return NULL;

#define APPEND(source) do {                                     \
    PyObject *tmp;                                              \
    int subresult;                                              \
    if (!(tmp = tdi_node_copy((source), model, NULL, 0, NULL))) \
        goto error;                                             \
    subresult = PyList_Append(list, tmp);                       \
    Py_DECREF(tmp);                                             \
    if (subresult == -1)                                        \
        goto error;                                             \
} while (0)

    if (!(startnode->flags & NODE_ROOT))
        APPEND(startnode);
    else {
        if (!(iter = PyObject_GetIter(startnode->nodes)))
            goto error;
        while ((item = PyIter_Next(iter))) {
            APPEND((tdi_node_t *)item);
            Py_DECREF(item);
        }
        if (PyErr_Occurred())
            goto error;
        Py_DECREF(iter);
    }

#undef APPEND

    iter = PyObject_GetIter(list);
    Py_DECREF(list);
    return iter;

error:
    Py_XDECREF(item);
    Py_XDECREF(iter);
    Py_DECREF(list);
    return NULL;
}


/*
 * Create new render iterator object
 */
PyObject *
tdi_render_iterator_new(tdi_node_t *startnode, tdi_adapter_t *model)
{
    PyObject *iter;
    tdi_render_t *self;

    if (!(self = GENERIC_ALLOC(&TDI_RenderIteratorType)))
        return NULL;

    if (startnode->flags & NODE_ROOT && startnode->content) {
        self->stage = TDI_RE_STAGE_ONLY_CONTENT;
        iter = tdi_adapter_emit_escaped(model) ?
            (startnode->content->with_escapes) : (startnode->content->clean);
        Py_INCREF(iter);
        self->model = iter;
    }
    else {
        self->stage = TDI_RE_STAGE_BEGIN;
        Py_INCREF((PyObject *)model);
        self->model = (PyObject *)model;
        self->emit_escaped = tdi_adapter_emit_escaped(model);
        if (!(iter = find_rootnodes(startnode, model)))
            goto error;
        if (tdi_render_stack_push(&self->stack, iter, NULL, 0) == -1)
            goto error;
    }

    return (PyObject *)self;

error:
    Py_DECREF(self);
    return NULL;
}
