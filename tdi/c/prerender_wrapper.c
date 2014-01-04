/*
 * Copyright 2014
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

#include "tdi_exceptions.h"

#include "obj_prerender_wrapper.h"
#include "obj_render_adapter.h"

/*
 * Object structure for TDI_PreRenderWrapperType
 */
struct tdi_prerender_wrapper_t {
    PyObject_HEAD
    PyObject *weakreflist;  /* Weak reference list */

    PyObject *modelmethod;  /* PyCFunction to ask for the model method */
    PyObject *newmethod;    /* PyCFunction for adapter factory */
    PyObject *attr;         /* Attribute name mapping */
    PyObject *adapter;      /* Original adapter */

    int emit_escaped;       /* Emit escaped text? */
};


/*
 * Default modelmethod
 */
static PyObject *
modelmethod_default(tdi_prerender_wrapper_t *self, PyObject *prefix,
                    PyObject *name, PyObject *scope, int noauto)
{
    PyObject *method;

    method = tdi_adapter_method((tdi_adapter_t *)self->adapter, prefix, name,
                                scope, noauto);
    if (!method) {
        if (!PyErr_ExceptionMatches(TDI_E_ModelMissingError))
            return NULL;
        PyErr_Clear();
    }
    else if (method == Py_None) {
        Py_DECREF(method);
        method = NULL;
    }
    else {
        return method;
    }

#define SIZE (sizeof("separate") - 1)
    if ((PyString_GET_SIZE(prefix) == SIZE)
        && (!memcmp(PyString_AS_STRING(prefix), "separate", SIZE)))
        Py_RETURN_NONE;
#undef SIZE

    return NULL;
}


/*
 * Create new adapter from adapter with a new model
 */
PyObject *
tdi_prerender_wrapper_factory(tdi_prerender_wrapper_t *self, PyObject *model)
{
    PyObject *result;

    if (!self->newmethod) {
        PyObject *adapter;

        if (TDI_RenderAdapterType_CheckExact(self->adapter)) {
            adapter = tdi_adapter_factory((tdi_adapter_t *)self->adapter,
                                          model);
        }
        else {
            Py_INCREF(model);
            adapter = PyObject_CallMethod(self->adapter, "new", "O", model);
            Py_DECREF(model);
        }
        if (!adapter)
            return NULL;

        result = tdi_prerender_wrapper_new(self->ob_type, adapter, self->attr,
                                           self->emit_escaped);
        Py_DECREF(adapter);
        return result;
    }

    Py_INCREF(model);
    result = PyObject_CallFunction(self->newmethod, "O", model);
    Py_DECREF(model);
    return result;
}

/* -------------- BEGIN TDI_PreRenderWrapperType DEFINITION -------------- */

PyDoc_STRVAR(TDI_PreRenderWrapperType_modelmethod__doc__,
"modelmethod(prefix, name, scope, noauto)\n\
\n\
This asks the passed adapter and if the particular method is not\n\
found it generates its own, which restores the tdi attributes\n\
(but not tdi:overlay).\n\
\n\
:Parameters:\n\
  `prefix` : ``str``\n\
    The method prefix (``render``, or ``separate``)\n\
\n\
  `name` : ``str``\n\
    The node name\n\
\n\
  `scope` : ``str``\n\
    Scope\n\
\n\
  `noauto` : ``bool``\n\
    No automatic method calling?\n\
\n\
:Return: The method or ``None``\n\
:Rtype: ``callable``\n\
\n\
:Exceptions:\n\
  - `ModelMissingError` : The method was not found, but all\n\
    methods are required");

static PyObject *
TDI_PreRenderWrapperType_modelmethod(tdi_prerender_wrapper_t *self,
                                     PyObject *args)
{
    PyObject *prefix, *name, *scope, *noauto_o, *res;
    int noauto;

    if (!(PyArg_ParseTuple(args, "SOSO", &prefix, &name, &scope, &noauto_o)))
        return NULL;

    if ((noauto = PyObject_IsTrue(noauto_o)) == -1)
        return NULL;

    if (name == Py_None)
        name = NULL;
    else if (PyString_Check(name))
        Py_INCREF(name);
    else if (!(name = PyObject_Str(name)))
        return NULL;

    res = modelmethod_default(self, prefix, name, scope, noauto);
    Py_XDECREF(name);
    return res;
}

static struct PyMethodDef TDI_PreRenderWrapperType_modelmethod__def = {
    "modelmethod",
    (PyCFunction)TDI_PreRenderWrapperType_modelmethod,
    METH_VARARGS,
    TDI_PreRenderWrapperType_modelmethod__doc__
};

static PyObject *
TDI_PreRenderWrapperType_getmodelmethod(tdi_prerender_wrapper_t *self,
                                        void *closure)
{
    PyObject *tmp, *mod;

    if (self->modelmethod) {
        Py_INCREF(self->modelmethod);
        return self->modelmethod;
    }

    if (!(mod = PyString_FromString(EXT_MODULE_PATH)))
        return NULL;
    tmp = PyCFunction_NewEx(&TDI_PreRenderWrapperType_modelmethod__def,
                            (PyObject *)self, mod);
    Py_DECREF(mod);
    return tmp;
}

static int
TDI_PreRenderWrapperType_setmodelmethod(tdi_prerender_wrapper_t *self,
                                        PyObject *method, void *closure)
{
    PyObject *tmp;

    Py_INCREF(method);
    tmp = self->modelmethod;
    self->modelmethod = method;
    Py_DECREF(tmp);

    return 0;
}

PyDoc_STRVAR(TDI_PreRenderWrapperType_new_method__doc__,
"new(model)\n\
\n\
Create adapter for a new model");

static PyObject *
TDI_PreRenderWrapperType_new_method(tdi_prerender_wrapper_t *self,
                                    PyObject *args)
{
    PyObject *model;

    if (!(PyArg_ParseTuple(args, "O", &model)))
        return NULL;

    return tdi_prerender_wrapper_factory(self, model);
}

static struct PyMethodDef TDI_PreRenderWrapperType_new_method__def = {
    "new",
    (PyCFunction)TDI_PreRenderWrapperType_new_method,
    METH_VARARGS,
    TDI_PreRenderWrapperType_new_method__doc__
};

static PyObject *
TDI_PreRenderWrapperType_getnew(tdi_prerender_wrapper_t *self, void *closure)
{
    PyObject *tmp, *mod;

    if (self->newmethod) {
        Py_INCREF(self->newmethod);
        return self->newmethod;
    }

    if (!(mod = PyString_FromString(EXT_MODULE_PATH)))
        return NULL;
    tmp = PyCFunction_NewEx(&TDI_PreRenderWrapperType_new_method__def,
                            (PyObject *)self, mod);
    Py_DECREF(mod);
    return tmp;
}

static int
TDI_PreRenderWrapperType_setnew(tdi_prerender_wrapper_t *self,
                                PyObject *method, void *closure)
{
    PyObject *tmp;

    Py_INCREF(method);
    tmp = self->newmethod;
    self->newmethod = method;
    Py_DECREF(tmp);

    return 0;
}

static PyObject *
TDI_PreRenderWrapperType_getemit_escaped(tdi_prerender_wrapper_t *self,
                                         void *closure)
{
    if (self->emit_escaped)
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static int
TDI_PreRenderWrapperType_setemit_escaped(tdi_prerender_wrapper_t *self,
                                         PyObject *flag, void *closure)
{
    int res;

    if ((res = PyObject_IsTrue(flag)) == -1)
        return -1;
    self->emit_escaped = res;

    return 0;
}

static PyGetSetDef TDI_PreRenderWrapperType_getset[] = {
    {"modelmethod",
     (getter)TDI_PreRenderWrapperType_getmodelmethod,
     (setter)TDI_PreRenderWrapperType_setmodelmethod,
     NULL, NULL},

    {"new",
     (getter)TDI_PreRenderWrapperType_getnew,
     (setter)TDI_PreRenderWrapperType_setnew,
     NULL, NULL},

    {"emit_escaped",
     (getter)TDI_PreRenderWrapperType_getemit_escaped,
     (setter)TDI_PreRenderWrapperType_setemit_escaped,
     NULL, NULL},

    {NULL}  /* Sentinel */
};

static PyObject *
TDI_PreRenderWrapperType_new(PyTypeObject *type, PyObject *args,
                             PyObject *kwds)
{
    static char *kwlist[] = {"adapter", "attr", NULL};
    PyObject *adapter, *attr = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O", kwlist,
                                     &adapter, &attr))
        return NULL;

    return tdi_prerender_wrapper_new(type, adapter, attr, 1);
}

static int
TDI_PreRenderWrapperType_traverse(tdi_prerender_wrapper_t *self,
                                  visitproc visit, void *arg)
{
    Py_VISIT(self->adapter);
    Py_VISIT(self->attr);
    Py_VISIT(self->modelmethod);
    Py_VISIT(self->newmethod);

    return 0;
}

static int
TDI_PreRenderWrapperType_clear(tdi_prerender_wrapper_t *self)
{
    if (self->weakreflist)
        PyObject_ClearWeakRefs((PyObject *)self);

    Py_CLEAR(self->adapter);
    Py_CLEAR(self->attr);
    Py_CLEAR(self->modelmethod);
    Py_CLEAR(self->newmethod);

    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_PreRenderWrapperType)

PyDoc_STRVAR(TDI_PreRenderWrapperType__doc__,
"PreRenderWrapper(adapter, attr=None)\n\
\n\
Pre-Render wrapper adapter\n\
\n\
:See: `ModelAdapterInterface`\n\
\n\
:Parameters:\n\
  `adapter` : `ModelAdapterInterface`\n\
    model adapter for resolving methods\n\
\n\
  `attr` : ``dict``\n\
    Attribute name mapping. The keys 'scope' and 'tdi' are recognized.\n\
    If omitted or ``None``, the default attribute names are applied\n\
    ('tdi:scope' and 'tdi').");

PyTypeObject TDI_PreRenderWrapperType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".PreRenderWrapper",                /* tp_name */
    sizeof(tdi_prerender_wrapper_t),                    /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_PreRenderWrapperType_dealloc,       /* tp_dealloc */
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
    | Py_TPFLAGS_BASETYPE
    | Py_TPFLAGS_HAVE_GC,
    TDI_PreRenderWrapperType__doc__,                    /* tp_doc */
    (traverseproc)TDI_PreRenderWrapperType_traverse,    /* tp_traverse */
    (inquiry)TDI_PreRenderWrapperType_clear,            /* tp_clear */
    0,                                                  /* tp_richcompare */
    offsetof(tdi_prerender_wrapper_t, weakreflist),     /* tp_weaklistoffset */
    0,                                                  /* tp_iter */
    0,                                                  /* tp_iternext */
    0,                                                  /* tp_methods */
    0,                                                  /* tp_members */
    TDI_PreRenderWrapperType_getset,                    /* tp_getset */
    0,                                                  /* tp_base */
    0,                                                  /* tp_dict */
    0,                                                  /* tp_descr_get */
    0,                                                  /* tp_descr_set */
    0,                                                  /* tp_dictoffset */
    0,                                                  /* tp_init */
    0,                                                  /* tp_alloc */
    TDI_PreRenderWrapperType_new                        /* tp_new */
};

/* --------------- END TDI_PreRenderWrapperType DEFINITION --------------- */

/*
 * Create new prerender wrapper
 */
PyObject *
tdi_prerender_wrapper_new(PyTypeObject *type, PyObject *adapter,
                          PyObject *attr, int emit_escaped)
{
    tdi_prerender_wrapper_t *self;

    if (!(self = GENERIC_ALLOC(type)))
        return NULL;

    Py_INCREF(adapter);
    self->adapter = adapter;
    if (attr == Py_None)
        attr = NULL;
    Py_XINCREF(attr);
    self->attr = attr;
    self->emit_escaped = emit_escaped ? 1 : 0;

    return (PyObject *)self;
}
