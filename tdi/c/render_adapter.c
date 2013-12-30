/*
 * Copyright 2006 - 2013
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
#include "tdi_globals.h"

#include "obj_render_adapter.h"


/*
 * Find the model
 */
static PyObject *
find_model(tdi_adapter_t *adapter, PyObject *scope)
{
    PyObject *model, *part, *scope_part, *tmp;
    const char *cscope, *c1, *c2, *sentinel;
    char *cp;
    Py_ssize_t size;

    model = PyDict_GetItem(adapter->models, scope);
    if (model) {
        Py_INCREF(model);
        return model;
    }

    if (!(model = PyDict_GetItem(adapter->models, tdi_g_empty))) {
        PyErr_SetObject(PyExc_KeyError, tdi_g_empty);
        return NULL;
    }
    Py_INCREF(model);

    cscope = c1 = PyString_AS_STRING(scope);
    size = PyString_GET_SIZE(scope);
    sentinel = cscope + size;
    while (c1 < sentinel) {
        c2 = memchr(c1, '.', size);
        if (!c2)
            c2 = sentinel;
        size -= (c2 - c1);
        scope_part = PyString_FromStringAndSize(cscope, c2 - cscope);
        if (!scope_part) {
            Py_DECREF(model);
            return NULL;
        }
        if ((tmp = PyDict_GetItem(adapter->models, scope_part))) {
            Py_DECREF(model);
            Py_INCREF(tmp);
            model = tmp;
        }
        else {
            if (!(part = PyString_FromStringAndSize(NULL, c2 - c1 + 6)))
                goto error_scope_part;

            cp = PyString_AS_STRING(part);
            *cp++ = 's';
            *cp++ = 'c';
            *cp++ = 'o';
            *cp++ = 'p';
            *cp++ = 'e';
            *cp++ = '_';
            (void)memcpy(cp, c1, c2 - c1);
            tmp = PyObject_GetAttr(model, part);
            Py_DECREF(part);
            if (!tmp) {
                if (!PyErr_ExceptionMatches(PyExc_AttributeError))
                    goto error_scope_part;
                PyErr_Clear();
                if (adapter->requirescopes) {
                    PyErr_SetObject(TDI_E_ModelMissingError, scope_part);
                    goto error_scope_part;
                }
                Py_INCREF(Py_None);
                tmp = Py_None;
            }
            Py_DECREF(model);
            model = tmp;
            if (PyDict_SetItem(adapter->models, scope_part, model) == -1)
                goto error_scope_part;
        }
        Py_DECREF(scope_part);
        c1 = c2 + (c2 != sentinel);
    }

    return model;

error_scope_part:
    Py_DECREF(scope_part);
    Py_DECREF(model);

    return NULL;
}


/*
 * Find a model method
 */
static PyObject *
modelmethod_default(tdi_adapter_t *adapter, PyObject *prefix, PyObject *name,
                    PyObject *scope, int noauto)
{
    PyObject *method, *methodname, *model;
    char *cmethodname;
    Py_ssize_t size;

    if (noauto || !name)
        Py_RETURN_NONE;

    if ((!PyString_CheckExact(prefix) && !PyString_Check(prefix)) ||
        (!PyString_CheckExact(name) && !PyString_Check(name)) ||
        (!PyString_CheckExact(scope) && !PyString_Check(scope))) {
        PyErr_SetString(TDI_E_ModelError,
                        "Wrong arguments to modelmethod call");
        return NULL;
    }

    if (!(model = find_model(adapter, scope)))
        return NULL;
    if (model == Py_None)
        return model;

    /*
     * Method lookup
     */

    /* build methodname */
    size = PyString_GET_SIZE(prefix) + PyString_GET_SIZE(name) + 1;
    if (!(methodname = PyString_FromStringAndSize(NULL, size))) {
        Py_DECREF(model);
        return NULL;
    }

    cmethodname = PyString_AS_STRING(methodname);
    size = PyString_GET_SIZE(prefix);
    (void)memcpy(cmethodname, PyString_AS_STRING(prefix), (size_t)size);
    cmethodname += size;
    *cmethodname++ = '_';
    (void)memcpy(cmethodname, PyString_AS_STRING(name),
                 (size_t)PyString_GET_SIZE(name));

    method = PyObject_GetAttr(model, methodname);
    Py_DECREF(model);
    if (!method) {
        if (!PyErr_ExceptionMatches(PyExc_AttributeError))
            goto error_methodname;
        PyErr_Clear();
        if (adapter->requiremethods) {
            PyErr_SetObject(TDI_E_ModelMissingError, methodname);
            goto error_methodname;
        }
        Py_INCREF(Py_None);
        method = Py_None;
    }
    Py_DECREF(methodname);

    return method;

error_methodname:
    Py_DECREF(methodname);
    return NULL;
}


/*
 * Find a model method
 */
PyObject *
tdi_render_adapter_method(tdi_adapter_t *adapter, PyObject *prefix,
                          PyObject *name, PyObject *scope, int noauto)
{
    PyObject *name_passed, *res;

    if (!adapter->modelmethod)
        return modelmethod_default(adapter, prefix, name, scope, noauto);

    if (!name) {
        Py_INCREF(Py_None);
        name_passed = Py_None;
    }
    else
        name_passed = name;

    res = PyObject_CallFunction(adapter->modelmethod, "OOOi",
                                prefix, name_passed, scope, noauto);
    if (!name) {
        Py_DECREF(Py_None);
    }
    return res;
}


/*
 * Create new adapter from adapter with a new model
 */
PyObject *
tdi_render_adapter_factory(tdi_adapter_t *self, PyObject *model)
{
    if (!self->newmethod)
        return tdi_adapter_new(self->ob_type, model, self->requiremethods,
                               self->requirescopes, self->emit_escaped);

    return PyObject_CallFunction(self->newmethod, "O", model);
}


/* ----------------- BEGIN TDI_RenderAdapterType DEFINITION ---------------- */

PyDoc_STRVAR(TDI_RenderAdapterType_for_prerender__doc__,
"for_prerender(cls, model)\n\
\n\
Create prerender adapter from model\n\
\n\
:Parameters:\n\
  `model` : any\n\
    User model\n\
\n\
:Return: Prerender adapter\n\
:Rtype: `ModelAdapterInterface`");

static PyObject *
TDI_RenderAdapterType_for_prerender(PyObject *cls, PyObject *args,
                                    PyObject *kwds)
{
    static char *kwlist[] = {"model", "attr", NULL};
    PyObject *wrapper, *model, *adapter, *cargs, *ckwds, *attr = NULL;
    int res;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O", kwlist,
                                     &model, &attr))
        return NULL;

    if (!(adapter = PyObject_CallFunction(cls, "O", model)))
        return NULL;

    if (!(model = PyImport_ImportModule("tdi.model_adapters"))) {
        Py_DECREF(adapter);
        return NULL;
    }

    wrapper = PyObject_GetAttrString(model, "PreRenderWrapper");
    Py_DECREF(model);
    if (!wrapper) {
        Py_DECREF(adapter);
        return NULL;
    }

    if (!attr)
        attr = Py_None;
    Py_INCREF(attr);

    if (!(cargs = PyTuple_New(1))) {
        Py_DECREF(attr);
        Py_DECREF(wrapper);
        Py_DECREF(adapter);
        return NULL;
    }
    PyTuple_SET_ITEM(cargs, 0, adapter);

    if (!(ckwds = PyDict_New())) {
        Py_DECREF(cargs);
        Py_DECREF(attr);
        Py_DECREF(wrapper);
        return NULL;
    }
    res = PyDict_SetItemString(ckwds, "attr", attr);
    Py_DECREF(attr);
    if (res == -1) {
        Py_DECREF(ckwds);
        Py_DECREF(cargs);
        Py_DECREF(wrapper);
        return NULL;
    }

    model = PyObject_Call(wrapper, cargs, ckwds);
    Py_DECREF(wrapper);
    Py_DECREF(ckwds);
    Py_DECREF(cargs);

    return model;
}

static struct PyMethodDef TDI_RenderAdapterType_methods[] = {
    {"for_prerender",
     (PyCFunction)TDI_RenderAdapterType_for_prerender,
                                        METH_KEYWORDS | METH_CLASS,
     TDI_RenderAdapterType_for_prerender__doc__},

    {NULL, NULL}  /* Sentinel */
};

PyDoc_STRVAR(TDI_RenderAdapterType_modelmethod__doc__,
"modelmethod(prefix, name, scope, noauto)\n\
\n\
Build the method name from prefix and node name and resolve\n\
\n\
This implements the default look up.\n\
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
TDI_RenderAdapterType_modelmethod(tdi_adapter_t *self, PyObject *args)
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

static struct PyMethodDef TDI_RenderAdapterType_modelmethod__def = {
    "modelmethod",
    (PyCFunction)TDI_RenderAdapterType_modelmethod,
    METH_VARARGS,
    TDI_RenderAdapterType_modelmethod__doc__
};

static PyObject *
TDI_RenderAdapterType_getmodelmethod(tdi_adapter_t *self, void *closure)
{
    PyObject *tmp, *mod;

    if (self->modelmethod) {
        Py_INCREF(self->modelmethod);
        return self->modelmethod;
    }

    if (!(mod = PyString_FromString(EXT_MODULE_PATH)))
        return NULL;
    tmp = PyCFunction_NewEx(&TDI_RenderAdapterType_modelmethod__def,
                            (PyObject *)self, mod);
    Py_DECREF(mod);
    return tmp;
}

static int
TDI_RenderAdapterType_setmodelmethod(tdi_adapter_t *self, PyObject *method,
                                     void *closure)
{
    PyObject *tmp;

    Py_INCREF(method);
    tmp = self->modelmethod;
    self->modelmethod = method;
    Py_DECREF(tmp);

    return 0;
}

PyDoc_STRVAR(TDI_RenderAdapterType_new_method__doc__,
"new(model)\n\
\n\
Create adapter for a new model");

static PyObject *
TDI_RenderAdapterType_new_method(tdi_adapter_t *self, PyObject *args)
{
    PyObject *model;

    if (!(PyArg_ParseTuple(args, "O", &model)))
        return NULL;

    return tdi_render_adapter_factory(self, model);
}

static struct PyMethodDef TDI_RenderAdapterType_new_method__def = {
    "new",
    (PyCFunction)TDI_RenderAdapterType_new_method,
    METH_VARARGS,
    TDI_RenderAdapterType_new_method__doc__
};

static PyObject *
TDI_RenderAdapterType_getnew(tdi_adapter_t *self, void *closure)
{
    PyObject *tmp, *mod;

    if (self->newmethod) {
        Py_INCREF(self->newmethod);
        return self->newmethod;
    }

    if (!(mod = PyString_FromString(EXT_MODULE_PATH)))
        return NULL;
    tmp = PyCFunction_NewEx(&TDI_RenderAdapterType_new_method__def,
                            (PyObject *)self, mod);
    Py_DECREF(mod);
    return tmp;
}

static int
TDI_RenderAdapterType_setnew(tdi_adapter_t *self, PyObject *method,
                             void *closure)
{
    PyObject *tmp;

    Py_INCREF(method);
    tmp = self->newmethod;
    self->newmethod = method;
    Py_DECREF(tmp);

    return 0;
}

static PyObject *
TDI_RenderAdapterType_getemit_escaped(tdi_adapter_t *self, void *closure)
{
    if (self->emit_escaped)
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static int
TDI_RenderAdapterType_setemit_escaped(tdi_adapter_t *self, PyObject *flag,
                                      void *closure)
{
    int res;

    if ((res = PyObject_IsTrue(flag)) == -1)
        return -1;
    self->emit_escaped = res;

    return 0;
}

static PyGetSetDef TDI_RenderAdapterType_getset[] = {
    {"modelmethod",
     (getter)TDI_RenderAdapterType_getmodelmethod,
     (setter)TDI_RenderAdapterType_setmodelmethod,
     NULL, NULL},

    {"new",
     (getter)TDI_RenderAdapterType_getnew,
     (setter)TDI_RenderAdapterType_setnew,
     NULL, NULL},

    {"emit_escaped",
     (getter)TDI_RenderAdapterType_getemit_escaped,
     (setter)TDI_RenderAdapterType_setemit_escaped,
     NULL, NULL},

    {NULL}  /* Sentinel */
};

static PyObject *
TDI_RenderAdapterType_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"model", "requiremethods", "requirescopes",
                             NULL};
    PyObject *model, *requiremethods_o = NULL, *requirescopes_o = NULL;
    int requiremethods, requirescopes;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OO", kwlist,
                                     &model, &requiremethods_o,
                                     &requirescopes_o))
        return NULL;

    if (!requiremethods_o)
        requiremethods = 0;
    else if ((requiremethods = PyObject_IsTrue(requiremethods_o)) == -1)
        return NULL;

    if (!requirescopes_o)
        requirescopes = 0;
    else if ((requirescopes = PyObject_IsTrue(requirescopes_o)) == -1)
        return NULL;

    return tdi_adapter_new(type, model, requiremethods, requirescopes, 0);
}

static int
TDI_RenderAdapterType_traverse(tdi_adapter_t *self, visitproc visit, void *arg)
{
    Py_VISIT(self->models);
    Py_VISIT(self->modelmethod);
    Py_VISIT(self->newmethod);

    return 0;
}

static int
TDI_RenderAdapterType_clear(tdi_adapter_t *self)
{
    if (self->weakreflist)
        PyObject_ClearWeakRefs((PyObject *)self);
    Py_CLEAR(self->models);
    Py_CLEAR(self->modelmethod);
    Py_CLEAR(self->newmethod);

    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_RenderAdapterType)

PyDoc_STRVAR(TDI_RenderAdapterType__doc__,
"RenderAdapter(model, requiremethods=False, requirescopes=False)\n\
\n\
Regular Render-Adapter implementation\n\
\n\
:See: `ModelAdapterInterface`");

PyTypeObject TDI_RenderAdapterType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".RenderAdapter",                   /* tp_name */
    sizeof(tdi_adapter_t),                              /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_RenderAdapterType_dealloc,          /* tp_dealloc */
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
    TDI_RenderAdapterType__doc__,                       /* tp_doc */
    (traverseproc)TDI_RenderAdapterType_traverse,       /* tp_traverse */
    (inquiry)TDI_RenderAdapterType_clear,               /* tp_clear */
    0,                                                  /* tp_richcompare */
    offsetof(tdi_adapter_t, weakreflist),               /* tp_weaklistoffset */
    0,                                                  /* tp_iter */
    0,                                                  /* tp_iternext */
    TDI_RenderAdapterType_methods,                      /* tp_methods */
    0,                                                  /* tp_members */
    TDI_RenderAdapterType_getset,                       /* tp_getset */
    0,                                                  /* tp_base */
    0,                                                  /* tp_dict */
    0,                                                  /* tp_descr_get */
    0,                                                  /* tp_descr_set */
    0,                                                  /* tp_dictoffset */
    0,                                                  /* tp_init */
    0,                                                  /* tp_alloc */
    TDI_RenderAdapterType_new                           /* tp_new */
};

/* ------------------ END TDI_RenderAdapterType DEFINITION ----------------- */

/*
 * Create new model adapter
 */
PyObject *
tdi_adapter_new(PyTypeObject *type, PyObject *model, int requiremethods,
                int requirescopes, int emit_escaped)
{
    tdi_adapter_t *self;

    if (!(self = GENERIC_ALLOC(type)))
        return NULL;

    self->requiremethods = requiremethods ? 1 : 0;
    self->requirescopes = requirescopes ? 1 : 0;
    self->emit_escaped = emit_escaped ? 1 : 0;

    if (!(self->models = PyDict_New()))
        goto error;
    if (PyDict_SetItem(self->models, tdi_g_empty, model) == -1)
        goto error;

    return (PyObject *)self;

error:
    Py_DECREF(self);
    return NULL;
}


/*
 * Create model object from alien model
 */
PyObject *
tdi_adapter_new_alien(PyObject *model)
{
    tdi_adapter_t *self;
    PyObject *tmp;
    int res;

    if (!(self = GENERIC_ALLOC(&TDI_RenderAdapterType)))
        return NULL;

    Py_INCREF(model);
    if (!(self->modelmethod = PyObject_GetAttrString(model, "modelmethod")))
        goto error;
    if (!(self->newmethod = PyObject_GetAttrString(model, "new")))
        goto error;
    if (!(tmp = PyObject_GetAttrString(model, "emit_escaped"))
        || (res = PyObject_IsTrue(tmp)) == -1)
        goto error_tmp;
    Py_DECREF(model);
    Py_DECREF(tmp);
    self->emit_escaped = res;

    return (PyObject *)self;

error_tmp:
    Py_XDECREF(tmp);
error:
    Py_DECREF(model);
    Py_DECREF(self);
    return NULL;
}
