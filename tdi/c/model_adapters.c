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

#include "tdi_exceptions.h"
#include "tdi_globals.h"

#include "obj_avoid_gc.h"
#include "obj_model_adapters.h"


typedef enum {
    ADAPTED_RENDER = 1,
    ADAPTED_PRERENDER,
    ADAPTED_FOREIGN
} adapted_e;

/*
 * Object structure for TDI_RenderAdapterType and TDI_PreRenderWrapperType
 */
struct tdi_adapter_t {
    PyObject_HEAD
    PyObject *weakreflist;  /* Weak reference list */

    PyObject *modelmethod;  /* PyCFunction to ask for the model method */
    PyObject *newmethod;    /* PyCFunction for adapter factory */
    int emit_escaped;       /* Emit escaped text? */
    adapted_e adapted;      /* What was adapted? */

    union {
        struct {
            PyObject *models;       /* user models */
            int requiremethods;     /* Require methods? */
            int requirescopes;      /* Require scopes? */
        } render;
        struct {
            tdi_adapter_t *adapter; /* Original adapter */
            PyObject *attr;         /* Attribute name mapping */
            PyObject *tdi_attr;     /* tdi attribute name */
            PyObject *scope_attr;   /* scope attribute name */
        } prerender;
    } u;
};

static PyObject *prerender_tup;

/*
 * Object structure for TDI_PreRenderMethodType
 */
typedef struct {
    PyObject_HEAD

    PyObject *name;
    PyObject *scope;
    PyObject *tdi_attr;
    PyObject *scope_attr;
    int noauto;
} tdi_premethod_t;


/*
 * Find the model
 */
static PyObject *
render_find_model(tdi_adapter_t *adapter, PyObject *scope)
{
    PyObject *model, *part, *scope_part, *tmp;
    const char *cscope, *c1, *c2, *sentinel;
    char *cp;
    Py_ssize_t size;

    model = PyDict_GetItem(adapter->u.render.models, scope);
    if (model) {
        Py_INCREF(model);
        return model;
    }

    if (!(model = PyDict_GetItem(adapter->u.render.models, tdi_g_empty))) {
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
        if ((tmp = PyDict_GetItem(adapter->u.render.models, scope_part))) {
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
                if (adapter->u.render.requirescopes) {
                    PyErr_SetObject(TDI_E_ModelMissingError, scope_part);
                    goto error_scope_part;
                }
                Py_INCREF(Py_None);
                tmp = Py_None;
            }
            Py_DECREF(model);
            model = tmp;
            if (-1 == PyDict_SetItem(adapter->u.render.models, scope_part,
                                     model))
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
render_modelmethod(tdi_adapter_t *adapter, PyObject *prefix, PyObject *name,
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

    if (!(model = render_find_model(adapter, scope)))
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
        if (adapter->u.render.requiremethods) {
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
 * Create new model adapter
 */
static PyObject *
render_new(PyTypeObject *type, PyObject *model, int requiremethods,
           int requirescopes, int emit_escaped)
{
    tdi_adapter_t *self;

    if (!(self = GENERIC_ALLOC(type)))
        return NULL;

    self->adapted = ADAPTED_RENDER;
    self->u.render.requiremethods = requiremethods ? 1 : 0;
    self->u.render.requirescopes = requirescopes ? 1 : 0;
    self->emit_escaped = emit_escaped ? 1 : 0;

    if (!(self->u.render.models = PyDict_New()))
        goto error;
    if (PyDict_SetItem(self->u.render.models, tdi_g_empty, model) == -1)
        goto error;

    return (PyObject *)self;

error:
    Py_DECREF(self);
    return NULL;
}


/*
 * Create new prerender wrapper
 */
static PyObject *
prerender_new(PyTypeObject *type, PyObject *adapter, PyObject *attr,
              int emit_escaped)
{
    PyObject *tmp;
    tdi_adapter_t *self;

    if (!(self = GENERIC_ALLOC(type)))
        return NULL;

    self->adapted = ADAPTED_PRERENDER;

    Py_INCREF(adapter);
    if (!(self->u.prerender.adapter = tdi_adapter_adapt(adapter)))
        goto error;

    if (attr == Py_None)
        attr = NULL;
    Py_XINCREF(attr);
    self->u.prerender.attr = attr;

    if (!(tmp = PyString_FromString("tdi:scope")))
        goto error;
    if (attr) {
        self->u.prerender.scope_attr = PyObject_CallMethod(attr, "get", "sO",
                                                           "scope", tmp);
        Py_DECREF(tmp);
        if (!self->u.prerender.scope_attr)
            goto error;
    }
    else {
        self->u.prerender.scope_attr = tmp;
    }

    if (!(tmp = PyString_FromString("tdi")))
        goto error;
    if (attr) {
        self->u.prerender.tdi_attr = PyObject_CallMethod(attr, "get", "sO",
                                                         "tdi", tmp);
        Py_DECREF(tmp);
        if (!self->u.prerender.tdi_attr)
            goto error;
    }
    else {
        self->u.prerender.tdi_attr = tmp;
    }

    self->emit_escaped = emit_escaped ? 1 : 0;

    return (PyObject *)self;

error:
    Py_DECREF(self);
    return NULL;
}


/*
 * Create new prerender wrapper
 */
static PyObject *
premethod_new(PyObject *name, PyObject *scope, PyObject *tdi_attr,
              PyObject *scope_attr, int noauto)
{
    tdi_premethod_t *self;

    if (!(self = GENERIC_ALLOC(&TDI_PreRenderMethodType)))
        return NULL;

    if (name == Py_None)
        name = NULL;
    Py_XINCREF(name);
    self->name = name;

    Py_INCREF(scope);
    self->scope = scope;

    Py_INCREF(tdi_attr);
    self->tdi_attr = tdi_attr;

    Py_INCREF(scope_attr);
    self->scope_attr = scope_attr;

    self->noauto = noauto;

    return (PyObject *)self;
}

/*
 * Prerender modelmethod
 */
static PyObject *
prerender_modelmethod(tdi_adapter_t *self, PyObject *prefix, PyObject *name,
                      PyObject *scope, int noauto)
{
    PyObject *method;

    method = tdi_adapter_method(self->u.prerender.adapter, prefix, name,
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

    return premethod_new(name, scope, self->u.prerender.tdi_attr,
                         self->u.prerender.scope_attr, noauto);
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
    PyObject *wrapper, *model, *adapter, *attr = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O", kwlist,
                                     &model, &attr))
        return NULL;

    Py_INCREF(model);
    Py_XINCREF(attr);
    adapter = PyObject_CallFunction(cls, "O", model);
    Py_DECREF(model);
    if (!adapter) {
        Py_XDECREF(attr);
        return NULL;
    }

    wrapper = prerender_new(&TDI_PreRenderWrapperType, adapter, attr, 1);
    Py_DECREF(adapter);
    Py_XDECREF(attr);

    return wrapper;
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

    res = render_modelmethod(self, prefix, name, scope, noauto);
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

    return tdi_adapter_factory(self, model);
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

    return render_new(type, model, requiremethods, requirescopes, 0);
}

static int
TDI_RenderAdapterType_traverse(tdi_adapter_t *self, visitproc visit, void *arg)
{
    if (self->adapted == ADAPTED_RENDER)
        Py_VISIT(self->u.render.models);
    Py_VISIT(self->modelmethod);
    Py_VISIT(self->newmethod);

    return 0;
}

static int
TDI_RenderAdapterType_clear(tdi_adapter_t *self)
{
    if (self->weakreflist)
        PyObject_ClearWeakRefs((PyObject *)self);

    if (self->adapted == ADAPTED_RENDER)
        Py_CLEAR(self->u.render.models);
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
:See: `ModelAdapterInterface`\n\
\n\
:Parameters:\n\
  `model` : any\n\
    User model\n\
\n\
  `requiremethods` : ``bool``\n\
    Require methods to exist?\n\
\n\
  `requirescopes` : ``bool``\n\
    Require scopes to exist?");

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
TDI_PreRenderWrapperType_modelmethod(tdi_adapter_t *self, PyObject *args)
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

    res = prerender_modelmethod(self, prefix, name, scope, noauto);
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
TDI_PreRenderWrapperType_getmodelmethod(tdi_adapter_t *self, void *closure)
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

PyDoc_STRVAR(TDI_PreRenderWrapperType_new_method__doc__,
"new(model)\n\
\n\
Create adapter for a new model");

static PyObject *
TDI_PreRenderWrapperType_new_method(tdi_adapter_t *self, PyObject *args)
{
    PyObject *model;

    if (!(PyArg_ParseTuple(args, "O", &model)))
        return NULL;

    return tdi_adapter_factory(self, model);
}

static struct PyMethodDef TDI_PreRenderWrapperType_new_method__def = {
    "new",
    (PyCFunction)TDI_PreRenderWrapperType_new_method,
    METH_VARARGS,
    TDI_PreRenderWrapperType_new_method__doc__
};

static PyObject *
TDI_PreRenderWrapperType_getnew(tdi_adapter_t *self, void *closure)
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

/* method setters are the same as above */
#define TDI_PreRenderWrapperType_setmodelmethod \
    TDI_RenderAdapterType_setmodelmethod
#define TDI_PreRenderWrapperType_setnew \
        TDI_RenderAdapterType_setnew

/* emit_escaped getter/setter are the same as above. */
#define TDI_PreRenderWrapperType_getemit_escaped \
    TDI_RenderAdapterType_getemit_escaped
#define TDI_PreRenderWrapperType_setemit_escaped \
    TDI_RenderAdapterType_setemit_escaped

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

    return prerender_new(type, adapter, attr, 1);
}

static int
TDI_PreRenderWrapperType_traverse(tdi_adapter_t *self, visitproc visit,
                                  void *arg)
{
    if (self->adapted == ADAPTED_PRERENDER) {
        Py_VISIT(((PyObject *)self->u.prerender.adapter));
        Py_VISIT(self->u.prerender.attr);
        Py_VISIT(self->u.prerender.tdi_attr);
        Py_VISIT(self->u.prerender.scope_attr);
    }
    Py_VISIT(self->modelmethod);
    Py_VISIT(self->newmethod);

    return 0;
}

static int
TDI_PreRenderWrapperType_clear(tdi_adapter_t *self)
{
    if (self->weakreflist)
        PyObject_ClearWeakRefs((PyObject *)self);

    if (self->adapted == ADAPTED_PRERENDER) {
        Py_CLEAR(self->u.prerender.adapter);
        Py_CLEAR(self->u.prerender.attr);
        Py_CLEAR(self->u.prerender.tdi_attr);
        Py_CLEAR(self->u.prerender.scope_attr);
    }
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
    sizeof(tdi_adapter_t),                              /* tp_basicsize */
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
    offsetof(tdi_adapter_t, weakreflist),               /* tp_weaklistoffset */
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

/* --------------- BEGIN TDI_PreRenderMethodType DEFINITION -------------- */

static int
prerender_setscope(tdi_premethod_t *self, PyObject *node)
{
    PyObject *scope, *tmp;
    char *cscope;
    int res;

    scope = PyString_FromStringAndSize(NULL,               /* 2 := =[+-] */
                                       PyString_GET_SIZE(self->scope) + 2);
    if (!scope)
        return -1;

    cscope = PyString_AS_STRING(scope);
    *cscope++ = '=';

    if (!(tmp = PyObject_GetAttrString(node, "hiddenelement")))
        goto error;
    res = PyObject_IsTrue(tmp);
    Py_DECREF(tmp);
    if (res == -1)
        goto error;
    *cscope++ = res ? '-' : '+';

    (void)memcpy(cscope, PyString_AS_STRING(self->scope),
                 (size_t)PyString_GET_SIZE(self->scope));

    if (PyObject_SetItem(node, self->scope_attr, scope) == -1)
        goto error;
    Py_DECREF(scope);

    return 0;

error:
    Py_DECREF(scope);
    return -1;
}


static int
prerender_toremove(PyObject *node)
{
    PyObject *key, *val;
    int res, res2;

    if (!(key = PyString_FromString("tdi:prerender")))
        return -1;
    val = PyObject_GetItem(node, key);
    if (!val) {
        Py_DECREF(key);
        if (!PyErr_ExceptionMatches(PyExc_KeyError))
            return -1;
        PyErr_Clear();
        return 0;
    }

    res = PyObject_DelItem(node, key);
    Py_DECREF(key);
    if (res == -1)
        goto error_val;

    if (!(key = PyString_FromString("remove-node")))
        goto error_val;

    res2 = PyObject_Cmp(val, key, &res);
    Py_DECREF(key);
    Py_DECREF(val);

    return (res2 == -1) ? -1 : !res;

error_val:
    Py_DECREF(val);
    return -1;
}


static int
prerender_settdi(tdi_premethod_t *self, PyObject *node, int sep)
{
    PyObject *tdi, *tmp;
    char *ctdi;
    int res;

    tdi = PyString_FromStringAndSize(NULL,
                                     !!self->noauto + !!sep +    /* [-+] */
                                        PyString_GET_SIZE(self->name) + 1);
    if (!tdi)
        return -1;
    ctdi = PyString_AS_STRING(tdi);

    if (!(tmp = PyObject_GetAttrString(node, "hiddenelement")))
        goto error;
    res = PyObject_IsTrue(tmp);
    Py_DECREF(tmp);
    if (res == -1)
        goto error;

    *ctdi++ = res ? '-' : '+';
    if (self->noauto)
        *ctdi++ = '*';
    if (sep)
        *ctdi++ = ':';

    (void)memcpy(ctdi, PyString_AS_STRING(self->name),
                 (size_t)PyString_GET_SIZE(self->name));

    if (PyObject_SetItem(node, self->tdi_attr, tdi) == -1)
        goto error;
    Py_DECREF(tdi);

    if (res && PyObject_SetAttrString(node, "hiddenelement", Py_False) == -1)
        return -1;

    return 0;

error:
    Py_DECREF(tdi);
    return -1;
}


static PyObject *
prerender_repeat_func(tdi_premethod_t *self, PyObject *args, PyObject *kws)
{
    PyObject *ret;
    int res;

    if ((res = PyObject_IsTrue(PyTuple_GET_ITEM(args, 1))) == -1)
        return NULL;
    if (res) {
        ret = PyObject_CallMethod(PyTuple_GET_ITEM(args, 0), "remove", "");
        if (!ret)
            return NULL;
        Py_DECREF(ret);
    }
    if (-1 == PyObject_SetAttrString(PyTuple_GET_ITEM(args, 0), "ctx",
                                     PyTuple_GET_ITEM(args, 2)))
        return NULL;

    Py_RETURN_NONE;
}


static int
prerender_render(tdi_premethod_t *, PyObject *, int);


static PyObject *
prerender_separate_func(tdi_premethod_t *self, PyObject *args, PyObject *kws)
{
    if (-1 == PyObject_SetAttrString(PyTuple_GET_ITEM(args, 0), "ctx",
                                     PyTuple_GET_ITEM(args, 1)))
        return NULL;

    if (-1 == prerender_render(self, PyTuple_GET_ITEM(args, 0), 1))
        return NULL;

    Py_RETURN_NONE;
}


static struct PyMethodDef prerender_repeat_method = {
    "_repeat", (PyCFunction)prerender_repeat_func, METH_VARARGS
};

static struct PyMethodDef prerender_separate_method = {
    "_separate", (PyCFunction)prerender_separate_func, METH_VARARGS
};


static int
prerender_repeat(tdi_premethod_t *self, PyObject *node)
{
    PyObject *repeat, *separate, *ctx, *tup, *method, *args, *kws, *ret;

    if (!(method = PyObject_GetAttrString(node, "repeat")))
        return -1;

    if (!(ctx = PyObject_GetAttrString(node, "ctx")))
        goto error_method;

    repeat = PyCFunction_NewEx(&prerender_repeat_method, (PyObject *)self,
                               NULL);
    if (!repeat)
        goto error_ctx;

    separate = PyCFunction_NewEx(&prerender_separate_method, (PyObject *)self,
                                 NULL);
    if (!separate)
        goto error_repeat;

    if (!(tup = prerender_tup)) {
        if (!(tup = PyTuple_New(2)))
            goto error_separate;
        if (!(kws = PyInt_FromLong(0)))
            goto error_tup;
        PyTuple_SET_ITEM(tup, 0, kws);
        if (!(kws = PyInt_FromLong(1)))
            goto error_tup;
        PyTuple_SET_ITEM(tup, 1, kws);
        prerender_tup = tup;
    }
    Py_INCREF(tup);

    if (!(kws = PyDict_New()))
        goto error_tup;

    if (!(args = PyTuple_New(3)))
        goto error_kws;

    if (PyDict_SetItemString(kws, "separate", separate) == -1)
        goto error_args;
    Py_DECREF(separate);

    PyTuple_SET_ITEM(args, 0, repeat);
    PyTuple_SET_ITEM(args, 1, tup);
    PyTuple_SET_ITEM(args, 2, ctx);

    ret = PyObject_Call(method, args, kws);
    Py_DECREF(args);
    Py_DECREF(kws);
    Py_DECREF(method);
    if (!ret)
        return -1;
    Py_DECREF(ret);

    return 0;

error_args:
    Py_DECREF(args);
error_kws:
    Py_DECREF(kws);
error_tup:
    Py_DECREF(tup);
error_separate:
    Py_DECREF(separate);
error_repeat:
    Py_DECREF(repeat);
error_ctx:
    Py_DECREF(ctx);
error_method:
    Py_DECREF(method);

    return -1;
}


static int
prerender_render(tdi_premethod_t *self, PyObject *node, int sep)
{
    int res;

    if ((res = prerender_toremove(node)) == -1)
        return -1;

    if (prerender_setscope(self, node) == -1)
        return -1;

    if (!res && self->name && prerender_settdi(self, node, sep) == -1)
        return -1;

    return prerender_repeat(self, node);
}


static PyObject *
TDI_PreRenderMethodType_call(tdi_premethod_t *self, PyObject *args,
                             PyObject *kwds)
{
    PyObject *node;

    if (!PyArg_ParseTuple(args, "O", &node))
        return NULL;

    if (!self->name) {
        if (prerender_setscope(self, node) == -1)
            return NULL;
    }
    else if (prerender_render(self, node, 0) == -1) {
        return NULL;
    }

    Py_RETURN_NONE;
}

#ifndef TDI_AVOID_GC
static int
TDI_PreRenderMethodType_traverse(tdi_premethod_t *self, visitproc visit,
                                 void *arg)
{
    Py_VISIT(self->name);
    Py_VISIT(self->scope);
    Py_VISIT(self->tdi_attr);
    Py_VISIT(self->scope_attr);

    return 0;
}
#endif

static int
TDI_PreRenderMethodType_clear(tdi_premethod_t *self)
{
    Py_CLEAR(self->name);
    Py_CLEAR(self->scope);
    Py_CLEAR(self->tdi_attr);
    Py_CLEAR(self->scope_attr);

    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_PreRenderMethodType)

PyTypeObject TDI_PreRenderMethodType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH "._PreRenderMethod",                /* tp_name */
    sizeof(tdi_premethod_t),                            /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_PreRenderMethodType_dealloc,        /* tp_dealloc */
    0,                                                  /* tp_print */
    0,                                                  /* tp_getattr */
    0,                                                  /* tp_setattr */
    0,                                                  /* tp_compare */
    0,                                                  /* tp_repr */
    0,                                                  /* tp_as_number */
    0,                                                  /* tp_as_sequence */
    0,                                                  /* tp_as_mapping */
    0,                                                  /* tp_hash */
    (ternaryfunc)TDI_PreRenderMethodType_call,          /* tp_call */
    0,                                                  /* tp_str */
    0,                                                  /* tp_getattro */
    0,                                                  /* tp_setattro */
    0,                                                  /* tp_as_buffer */
    Py_TPFLAGS_HAVE_CLASS                               /* tp_flags */
    | TDI_IF_GC(Py_TPFLAGS_HAVE_GC),
    0,                                                  /* tp_doc */
    (traverseproc)TDI_IF_GC(TDI_PreRenderMethodType_traverse),
                                                        /* tp_traverse */
    (inquiry)TDI_IF_GC(TDI_PreRenderMethodType_clear)   /* tp_clear */
};

/* ---------------- END TDI_PreRenderMethodType DEFINITION --------------- */

/*
 * Create adapter from anything.
 *
 * Adapter is stolen.
 *
 * Return: new adapter.
 */
tdi_adapter_t *
tdi_adapter_adapt(PyObject *adapter)
{
    tdi_adapter_t *self;
    PyObject *tmp;
    int res;

    if (TDI_RenderAdapterType_Check(adapter)
        || TDI_PreRenderWrapperType_Check(adapter))
        return (tdi_adapter_t *)adapter;

    if (!(self = GENERIC_ALLOC(&TDI_RenderAdapterType)))
        goto error_adapter;

    self->adapted = ADAPTED_FOREIGN;
    if (!(self->modelmethod = PyObject_GetAttrString(adapter, "modelmethod")))
        goto error_self;
    if (!(self->newmethod = PyObject_GetAttrString(adapter, "new")))
        goto error_self;
    if (!(tmp = PyObject_GetAttrString(adapter, "emit_escaped"))
        || (res = PyObject_IsTrue(tmp)) == -1)
        goto error_tmp;
    Py_DECREF(((PyObject *)adapter));
    Py_DECREF(tmp);
    self->emit_escaped = res;

    return self;

error_tmp:
    Py_XDECREF(tmp);
error_self:
    Py_DECREF(self);
error_adapter:
    Py_DECREF(((PyObject *)adapter));
    return NULL;
}


/*
 * Return emit_escaped flag
 *
 * (adapter.emit_escaped)
 */
int
tdi_adapter_emit_escaped(tdi_adapter_t *self)
{
    return self->emit_escaped;
}


/*
 * Raise invalid-setup assertion
 */
static PyObject *
raise_assert(void)
{
    PyErr_SetString(PyExc_AssertionError,
                    "Invalid render adapter setup. This is a bug in TDI.");
    return NULL;
}


/*
 * Find a model method
 *
 * (adapter.modelmethod())
 */
PyObject *
tdi_adapter_method(tdi_adapter_t *self, PyObject *prefix, PyObject *name,
                   PyObject *scope, int noauto)
{
    PyObject *name_passed, *res;

    if (!self->modelmethod) {
        if (self->adapted == ADAPTED_RENDER) {
            return render_modelmethod(self, prefix, name, scope, noauto);
        }
        else if (self->adapted == ADAPTED_PRERENDER) {
            return prerender_modelmethod(self, prefix, name, scope, noauto);
        }
        else {
            return raise_assert();
        }
    }

    if (!name) {
        Py_INCREF(Py_None);
        name_passed = Py_None;
    }
    else
        name_passed = name;

    res = PyObject_CallFunction(self->modelmethod, "OOOi",
                                prefix, name_passed, scope, noauto);
    if (!name) {
        Py_DECREF(Py_None);
    }
    return res;
}


/*
 * Create new adapter from adapter with a new model
 *
 * (adapter.new())
 */
PyObject *
tdi_adapter_factory(tdi_adapter_t *self, PyObject *model)
{
    PyObject *result;

    if (!self->newmethod) {
        if (self->adapted == ADAPTED_RENDER) {
            return render_new(self->ob_type, model,
                              self->u.render.requiremethods,
                              self->u.render.requirescopes,
                              self->emit_escaped);
        }
        else if (self->adapted == ADAPTED_PRERENDER) {
            PyObject *adapter;

            adapter = tdi_adapter_factory(self->u.prerender.adapter, model);
            if (!adapter)
                return NULL;

            result = prerender_new(self->ob_type, adapter,
                                   self->u.prerender.attr,
                                   self->emit_escaped);
            Py_DECREF(adapter);
            return result;
        }
        else {
            return raise_assert();
        }
    }

    Py_INCREF(model);
    result = PyObject_CallFunction(self->newmethod, "O", model);
    Py_DECREF(model);
    return result;
}
