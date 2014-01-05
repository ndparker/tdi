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
#include "tdi_exceptions.h"
#include "tdi_globals.h"
#include "tdi_node_clear.h"
#include "tdi_overlay.h"
#include "tdi_remove.h"
#include "tdi_render.h"
#include "tdi_replace.h"
#include "tdi_scope.h"
#include "tdi_util.h"

#include "obj_attr.h"
#include "obj_decoder.h"
#include "obj_encoder.h"
#include "obj_model_adapters.h"
#include "obj_node.h"
#include "obj_raw_node.h"
#include "obj_render_iter.h"
#include "obj_template_node.h"


#define TDI_NodeType_Check(op) PyObject_TypeCheck(op, &TDI_NodeType)

/*
 * clear node
 */
void
node_clear(tdi_node_t *self) {
    Py_CLEAR(self->sep);
    Py_CLEAR(self->callback);
    Py_CLEAR(self->overlays);
    Py_CLEAR(self->nodes);
    Py_CLEAR(self->namedict);
    Py_CLEAR(self->modelscope);
    TDI_SCOPE_CLEAR(self->scope);
    TDI_OVERLAY_CLEAR(self->overlay);
    TDI_CONTENT_CLEAR(self->content);
    Py_CLEAR(self->complete);
    Py_CLEAR(self->tagname);
    Py_CLEAR(self->attr);
    Py_CLEAR(self->endtag);
    Py_CLEAR(self->name);
    Py_CLEAR(self->encoder);
    Py_CLEAR(self->decoder);
    Py_CLEAR(self->ctx);
    Py_CLEAR(self->model);
}


/* --------------------- BEGIN TDI_NodeType DEFINITION --------------------- */

PyDoc_STRVAR(TDI_NodeType_repeat__doc__,
"repeat(self, callback, itemlist, *fixed, **kwargs)\n\
\n\
Repeat the snippet ``len(list(itemlist))`` times\n\
\n\
The actually supported signature is::\n\
\n\
    repeat(self, callback, itemlist, *fixed, separate=None)\n\
\n\
Examples:\n\
\n\
>>> def render_foo(self, node):\n\
>>>     def callback(node, item):\n\
>>>         ...\n\
>>>     node.repeat(callback, [1, 2, 3, 4])\n\
\n\
>>> def render_foo(self, node):\n\
>>>     def callback(node, item):\n\
>>>         ...\n\
>>>     def sep(node):\n\
>>>         ...\n\
>>>     node.repeat(callback, [1, 2, 3, 4], separate=sep)\n\
\n\
>>> def render_foo(self, node):\n\
>>>     def callback(node, item, foo, bar):\n\
>>>         ...\n\
>>>     node.repeat(callback, [1, 2, 3, 4], \"foo\", \"bar\")\n\
\n\
>>> def render_foo(self, node):\n\
>>>     def callback(node, item, foo, bar):\n\
>>>         ...\n\
>>>     def sep(node):\n\
>>>         ...\n\
>>>     node.repeat(callback, [1, 2, 3, 4], \"foo\", \"bar\",\n\
>>>                 separate=sep)\n\
\n\
:Parameters:\n\
  `callback` : ``callable``\n\
    The callback function\n\
\n\
  `itemlist` : iterable\n\
    The items to iterate over\n\
\n\
  `fixed` : ``tuple``\n\
    Fixed parameters to be passed to the repeat methods\n\
\n\
:Keywords:\n\
  `separate` : ``callable``\n\
    Alternative callback function for separator nodes. If omitted or\n\
    ``None``, ``self.separate_name`` is looked up and called if it\n\
    exists.");

static PyObject *
TDI_NodeType_repeat(tdi_node_t *self, PyObject *args, PyObject *kwds)
{
    PyObject *callback, *itemlist, *fixed, *cbargs, *separate;
    Py_ssize_t length;
    int expected_kwds = 0;

    length = PyTuple_GET_SIZE(args);
    if (length >= 2) {
        itemlist = PyTuple_GET_ITEM(args, 1);
        Py_INCREF(itemlist);
        callback = PyTuple_GET_ITEM(args, 0);
        Py_INCREF(callback);
    }
    else {
        itemlist = kwds ? PyDict_GetItemString(kwds, "itemlist") : NULL;
        if (!itemlist) {
            if (!PyErr_Occurred())
                PyErr_SetString(PyExc_TypeError,
                                "Node.repeat takes at least 2 arguments");
            return NULL;
        }
        Py_INCREF(itemlist);
        ++expected_kwds;

        if (length == 1) {
            callback = PyTuple_GET_ITEM(args, 0);
        }
        else  {
            callback = kwds ? PyDict_GetItemString(kwds, "callback") : NULL;
            if (!callback) {
                if (!PyErr_Occurred())
                    PyErr_SetString(PyExc_TypeError,
                                    "Node.repeat takes at least 2 arguments");
                Py_DECREF(itemlist);
                return NULL;
            }
        }
        Py_INCREF(callback);
        ++expected_kwds;
    }
    fixed = PyObject_GetIter(itemlist);
    Py_DECREF(itemlist);
    if (!fixed) {
        Py_DECREF(callback);
        return NULL;
    }
    itemlist = fixed;

    if (!(separate = kwds ? PyDict_GetItemString(kwds, "separate") : NULL)) {
        if (PyErr_Occurred()) {
            Py_DECREF(itemlist);
            Py_DECREF(callback);
            return NULL;
        }
        separate = Py_None;
    }
    else
        ++expected_kwds;
    Py_INCREF(separate);

    if (kwds && PyDict_Size(kwds) > expected_kwds) {
        PyErr_SetString(PyExc_TypeError, "Unrecognized keyword parameters");
        Py_DECREF(separate);
        Py_DECREF(itemlist);
        Py_DECREF(callback);
        return NULL;
    }

    if (length <= 2) {
        fixed = tdi_g_empty_tuple;
        Py_INCREF(fixed);
    }
    else if (!(fixed = PyTuple_GetSlice(args, 2, length))) {
        Py_DECREF(separate);
        Py_DECREF(itemlist);
        Py_DECREF(callback);
        return NULL;
    }

    if (!(cbargs = PyTuple_New(4))) {
        Py_DECREF(separate);
        Py_DECREF(itemlist);
        Py_DECREF(callback);
        Py_DECREF(fixed);
        return NULL;
    }

    PyTuple_SET_ITEM(cbargs, 0, callback);
    PyTuple_SET_ITEM(cbargs, 1, itemlist);
    PyTuple_SET_ITEM(cbargs, 2, fixed);
    PyTuple_SET_ITEM(cbargs, 3, separate);

    Py_CLEAR(self->overlays);
    self->overlays = cbargs;
    self->flags |= NODE_REPEATED;
    self->kind = PROC_NODE;

    Py_RETURN_NONE;
}

PyDoc_STRVAR(TDI_NodeType_remove__doc__,
"remove(self)\n\
\n\
Remove the node from the tree\n\
\n\
Tells the system, that the node (and all of its subnodes) should\n\
not be rendered.");

static PyObject *
TDI_NodeType_remove(tdi_node_t *self, PyObject *dummy)
{
    tdi_remove_node(self);
    Py_RETURN_NONE;
}

PyDoc_STRVAR(TDI_NodeType_iterate__doc__,
"iterate(self, itemlist, separate=None)\n\
\n\
Iterate over repeated nodes\n\
\n\
Iteration works by repeating the original node\n\
``len(list(iteritems))`` times, turning the original node into a\n\
container node and appending the generated nodeset to that container.\n\
That way, the iterated nodes are virtually indented by one level, but\n\
the container node is completely hidden, so it won't be visible.\n\
\n\
All repeated nodes are marked as ``DONE``, so they (and their\n\
subnodes) are not processed any further (except explicit callbacks).\n\
If there is a separator node assigned, it's put between the\n\
repetitions and *not* marked as ``DONE``. The callbacks to them\n\
(if any) are executed when the template system gets back to control.\n\
\n\
:Parameters:\n\
  `itemlist` : iterable\n\
    The items to iterate over\n\
\n\
  `separate` : ``callable``\n\
    Alternative callback function for separator nodes. If omitted or\n\
    ``None``, ``self.separate_name`` is looked up and called if it\n\
    exists.\n\
\n\
:Return: The repeated nodes and items (``[(node, item), ...]``)\n\
:Rtype: iterable");

static PyObject *
TDI_NodeType_iterate(tdi_node_t *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"itemlist", "separate", NULL};
    PyObject *itemlist, *separate = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O", kwlist,
                                     &itemlist, &separate))
        return NULL;

    if (!(itemlist = PyObject_GetIter(itemlist)))
        return NULL;
    if (separate == Py_None)
        separate = NULL;
    else if (separate)
        Py_INCREF(separate);

    return tdi_render_iterate(self, itemlist, separate);
}

PyDoc_STRVAR(TDI_NodeType_replace__doc__,
"replace(self, callback, other, *fixed)\n\
\n\
Replace the node (and all subnodes) with the copy of another one\n\
\n\
The replacement node is deep-copied, so use it with care\n\
(performance-wise).\n\
\n\
:Parameters:\n\
  `callback` : ``callable``\n\
    callback function\n\
\n\
  `other` : `Node`\n\
    The replacement node\n\
\n\
  `fixed` : ``tuple``\n\
    Fixed parameters for the callback\n\
\n\
:Return: The replaced node (actually the node itself, but with\n\
         updated parameters)\n\
:Rtype: `Node`");

static PyObject *
TDI_NodeType_replace(tdi_node_t *self, PyObject *args)
{
    PyObject *callback, *other, *fixed;
    Py_ssize_t length;
    int result;

    length = PyTuple_GET_SIZE(args);
    if (length < 2) {
        PyErr_SetString(PyExc_TypeError,
                        "Node.replace takes at least 2 arguments");
        return NULL;
    }
    else if (length == 2)
        fixed = NULL;
    else if (!(fixed = PyTuple_GetSlice(args, 2, length)))
        return NULL;
    callback = PyTuple_GET_ITEM(args, 0);
    other = PyTuple_GET_ITEM(args, 1);
    if (!TDI_NodeType_Check(other) && !TDI_TemplateNodeType_Check(other)) {
        PyErr_SetString(PyExc_ValueError,
            "Node.replace: second argument must be a node"
        );
        Py_XDECREF(fixed);
        return NULL;
    }
    result = tdi_replace_node(self, (tdi_node_t *)other, callback, fixed);
    Py_XDECREF(fixed);

    if (result == -1)
        return NULL;
    return Py_INCREF(self), (PyObject *)self;
}

PyDoc_STRVAR(TDI_NodeType_copy__doc__,
"copy(self)\n\
\n\
Deep copy this node\n\
\n\
:Return: The node copy\n\
:Rtype: `Node`");

static PyObject *
TDI_NodeType_copy(tdi_node_t *self, PyObject *dummy)
{
    return tdi_node_deepcopy(self, self->model, self->ctx, NULL);
}

PyDoc_STRVAR(TDI_NodeType_render__doc__,
"render(self, callback, params, **kwargs)\n\
\n\
Render this node only and return the result as string\n\
\n\
Note that callback and params are optional positional parameters::\n\
\n\
    render(self, decode=True, decode_errors='strict')\n\
    # or\n\
    render(self, callback, decode=True, decode_errors='strict')\n\
    # or\n\
    render(self, callback, param1, paramx, ... decode=True, ...)\n\
\n\
is also possible.\n\
\n\
:Parameters:\n\
  `callback` : callable or ``None``\n\
    Optional callback function and additional parameters\n\
\n\
  `params` : ``tuple``\n\
    Optional extra parameters for `callback`\n\
\n\
:Keywords:\n\
  `decode` : ``bool``\n\
    Decode the result back to unicode? This uses the encoding of the\n\
    template.\n\
\n\
  `decode_errors` : ``str``\n\
    Error handler if decode errors happen.\n\
\n\
  `model` : any\n\
    New render model, if omitted or ``None``, the current model is\n\
    applied.\n\
\n\
  `adapter` : ``callable``\n\
    Model adapter factory, takes the model and returns a\n\
    `ModelAdapterInterface`. If omitted or ``None``, the current\n\
    adapter is used. This parameter is ignored, if no ``model``\n\
    parameter is passed.\n\
\n\
:Return: The rendered node, type depends on ``decode`` keyword\n\
:Rtype: ``basestring``");

static PyObject *
TDI_NodeType_render(tdi_node_t *self, PyObject *args, PyObject *kwds)
{
    PyObject *tmp, *tmp2, *callback, *fixed, *collect, *iter;
    PyObject *decode_o, *decode_errors_o, *model_o, *adapter_o;
    tdi_adapter_t *model;
    char *decode_errors, *encoding;
    tdi_node_t *mynode;
    Py_ssize_t length;
    int decode, res, expected_kwds;

    /* Evaluate Keywords */
    if (!kwds) {
        decode_o = NULL;
        decode_errors_o = NULL;
        model_o = NULL;
        adapter_o = NULL;
    }
    else {
        expected_kwds = 0;

#define KW(name) do {                                      \
    if (!(name##_o = PyDict_GetItemString(kwds, #name))) { \
        if (PyErr_Occurred())                              \
            return NULL;                                   \
    }                                                      \
    else {                                                 \
        ++expected_kwds;                                   \
    }                                                      \
} while(0)

        /* all references are borrowed */
        KW(decode);
        KW(decode_errors);
        KW(model);
        KW(adapter);

        if (PyDict_Size(kwds) > expected_kwds) {
            PyErr_SetString(PyExc_TypeError,
                            "Unrecognized keyword parameters");
            return NULL;
        }

#undef KW
    }

    if (!decode_o)
        decode = 1; /* default: True */
    else if ((decode = PyObject_IsTrue(decode_o)) == -1)
        return NULL;

    if (!decode_errors_o)
        decode_errors = "strict";
    else if (!(decode_errors = PyString_AsString(decode_errors_o)))
        return NULL;

    /* Evaluate positional arguments */
    length = PyTuple_GET_SIZE(args);
    if (length == 0) {
        callback = Py_None;
        fixed = NULL;
    }
    else {
        callback = PyTuple_GET_ITEM(args, 0);
        if (length == 1)
            fixed = NULL;
        else if (!(fixed = PyTuple_GetSlice(args, 1, length)))
            return NULL;
    }
    Py_INCREF(callback);

    /* setup model */
    if (!model_o || model_o == Py_None) {
        model = (Py_INCREF(self->model), self->model);
    }
    else if (!adapter_o || adapter_o == Py_None) {
        model = (tdi_adapter_t *)tdi_adapter_factory(self->model, model_o);
        if (!model)
            goto error_args;
    }
    else if (!(tmp = PyObject_CallFunction(adapter_o, "O", model_o))
            || !(model = tdi_adapter_adapt(tmp)))
        goto error_args;

    /* setup node */
    mynode = (tdi_node_t *)tdi_node_deepcopy(self, model, self->ctx, NULL);
    if (!mynode)
        goto error_model;

    if (tdi_replace_node(mynode, mynode, callback, fixed) == -1)
        goto error_mynode;

    /* render */
    if (!(collect = PyList_New(0)))
        goto error_mynode;
    if (!(iter = tdi_render_iterator_new(mynode, model)))
        goto error_collect;

    while ((tmp = PyIter_Next(iter))) {
        res = PyList_Append(collect, tmp);
        Py_DECREF(tmp);
        if (res == -1)
            goto error_iter;
    }
    if (PyErr_Occurred())
        goto error_iter;
    Py_DECREF(iter);

    /* join everything together */
    tmp = tdi_g_empty;
    Py_INCREF(tmp);
    tmp2 = PyObject_CallMethod(tmp, "join", "(O)", collect);
    Py_DECREF(tmp);
    Py_DECREF(collect);
    Py_DECREF(mynode);
    Py_DECREF(model);
    Py_XDECREF(fixed);
    Py_DECREF(callback);
    if (!tmp2)
        return NULL;
    if (!decode)
        return tmp2;

    /* decode */
    if (!(encoding = PyString_AsString(self->encoder->encoding))) {
        Py_DECREF(tmp2);
        return NULL;
    }
    tmp = PyString_AsDecodedObject(tmp2, encoding, decode_errors);
    Py_DECREF(tmp2);
    return tmp;

error_iter:
    Py_DECREF(iter);
error_collect:
    Py_DECREF(collect);
error_mynode:
    Py_DECREF(mynode);
error_model:
    Py_DECREF(model);
error_args:
    Py_XDECREF(fixed);
    Py_DECREF(callback);

    return NULL;
}

#ifdef METH_COEXIST  /* Python 2.4 optimization */
PyDoc_STRVAR(TDI_NodeType_call__doc__,
"__call__(self, name)\n\
\n\
Determine direct subnodes by name\n\
\n\
In contrast to ``__getattr__`` this works for all names. Also the\n\
exception in case of a failed lookup is different.\n\
\n\
:Parameters:\n\
  `name` : ``str``\n\
    The name looked for\n\
\n\
:return: The found node\n\
:rtype: `Node`\n\
\n\
:Exceptions:\n\
  - `NodeNotFoundError` : The subnode was not found");

PyDoc_STRVAR(TDI_NodeType_getattro__doc__,
"__getattribute__(self, name)\n\
\n\
Determine attributes/methods or direct subnodes by name.\n\
\n\
If the attribute (or method) was not found, it's tried to resolve as a\n\
subnode.\n\
\n\
:Return: The found attribute or subnode\n\
:Rtype: any\n\
\n\
:Exceptions:\n\
  - `AttributeError` : The attribute/subnode was not found");

PyDoc_STRVAR(TDI_NodeType_getitem__doc__,
"__getitem__(self, name)\n\
\n\
Determine the value of attribute `name`.\n\
\n\
:Return: The attribute (``None`` for shorttags)\n\
:Rtype: ``str``\n\
\n\
:Exceptions:\n\
  - `KeyError` : The attribute does not exist");

/* Forward declaration */
static PyObject *TDI_NodeType_call(tdi_node_t *, PyObject *, PyObject *);
static PyObject *TDI_NodeType_getattro(tdi_node_t *, PyObject *);
static PyObject *TDI_NodeType_getitem(tdi_node_t *, PyObject *);
#endif /* METH_COEXIST */

static struct PyMethodDef TDI_NodeType_methods[] = {
#ifdef METH_COEXIST
    {"__call__",
     (PyCFunction)TDI_NodeType_call,        METH_KEYWORDS | METH_COEXIST,
     TDI_NodeType_call__doc__},

    {"__getattribute__",
     (PyCFunction)TDI_NodeType_getattro,    METH_O | METH_COEXIST,
     TDI_NodeType_getattro__doc__},

    {"__getitem__",
     (PyCFunction)TDI_NodeType_getitem,     METH_O | METH_COEXIST,
     TDI_NodeType_getitem__doc__},
#endif
    {"repeat",
     (PyCFunction)TDI_NodeType_repeat,      METH_KEYWORDS,
     TDI_NodeType_repeat__doc__},

    {"remove",
     (PyCFunction)TDI_NodeType_remove,      METH_NOARGS,
     TDI_NodeType_remove__doc__},

    {"iterate",
     (PyCFunction)TDI_NodeType_iterate,     METH_KEYWORDS,
     TDI_NodeType_iterate__doc__},

    {"replace",
     (PyCFunction)TDI_NodeType_replace,     METH_VARARGS,
     TDI_NodeType_replace__doc__},

    {"copy",
     (PyCFunction)TDI_NodeType_copy,        METH_NOARGS,
     TDI_NodeType_copy__doc__},

    {"render",
     (PyCFunction)TDI_NodeType_render,      METH_KEYWORDS,
     TDI_NodeType_render__doc__},

    {NULL, NULL}  /* Sentinel */
};


static PyObject *
TDI_NodeType_call(tdi_node_t *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"name", NULL};
    PyObject *tmp, *name;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", kwlist, &tmp))
        return NULL;

    if (!(name = PyObject_Str(tmp))) {
        if (PyErr_ExceptionMatches(PyExc_UnicodeError))
            PyErr_SetObject(TDI_E_NodeNotFoundError, tmp);
        return NULL;
    }

    tmp = tdi_util_subnode(self, name);
    Py_DECREF(name);
    return tmp;
}

static PyObject *
TDI_NodeType_getattro(tdi_node_t *self, PyObject *name)
{
    PyObject *tmp;

    if (!(tmp = PyObject_GenericGetAttr((PyObject *)self, name))) {
        if (!PyErr_ExceptionMatches(PyExc_AttributeError))
            return NULL;
        PyErr_Clear();
    }
    else
        return tmp;

    if (!PyString_CheckExact(name) && !PyString_Check(name)) {
        PyErr_SetString(PyExc_TypeError, "Subnodes are named by strings");
        return NULL;
    }

    if (!(tmp = tdi_util_subnode(self, name))) {
        if (PyErr_ExceptionMatches(TDI_E_NodeNotFoundError))
            PyErr_SetObject(PyExc_AttributeError, name);
    }

    return tmp;
}

static PyObject *
TDI_NodeType_getitem(tdi_node_t *self, PyObject *key)
{
    PyObject *tmp, *normkey, *value;
    tdi_attr_t *item;
    const char *cvalue;

    if (!(key = ENCODE_NAME(self, key)))
        return NULL;

    if (!PyString_CheckExact(key) && !PyString_Check(key)) {
        PyErr_SetString(TDI_E_ModelError, "attribute key must be a string");
        Py_DECREF(key);
        return NULL;
    }
    normkey = DECODER_NORMALIZE(self, key);
    Py_DECREF(key);
    if (!normkey)
        return NULL;

    item = (tdi_attr_t *)PyDict_GetItem(self->attr, normkey);
    Py_DECREF(normkey);
    if (!item) {
        PyErr_SetString(PyExc_KeyError, "Attribute not found.");
        return NULL;
    }
    value = item->value;
    Py_INCREF(value);

    if (value == Py_None)
        return value;

    cvalue = PyString_AS_STRING(value);
    if (*cvalue == '"' || *cvalue == '\'') {
        Py_ssize_t length = PyString_GET_SIZE(value);

        tmp = PySequence_GetSlice(value, 1, length - 1);
        Py_DECREF(value);
        if (!tmp)
            return NULL;
        value = tmp;
    }

    return value;
}

static int
TDI_NodeType_setitem(tdi_node_t *self, PyObject *key, PyObject *value)
{
    PyObject *tmp, *normkey;
    tdi_attr_t *item;
    int subresult;

    if (!(key = ENCODE_NAME(self, key)))
        return -1;

    if (!PyString_CheckExact(key) && !PyString_Check(key)) {
        PyErr_SetString(TDI_E_ModelError, "attribute key must be a string");
        Py_DECREF(key);
        return -1;
    }
    if (!(normkey = DECODER_NORMALIZE(self, key))) {
        Py_DECREF(key);
        return -1;
    }

    if (!value) {
        subresult = PyDict_DelItem(self->attr, normkey);
        if (subresult == -1) {
            if (PyErr_ExceptionMatches(PyExc_KeyError)) {
                PyErr_Clear();
                subresult = 0;
            }
        }
        Py_DECREF(normkey);
        Py_DECREF(key);
        return subresult;
    }

    if (value == Py_None)
        Py_INCREF(value);
    else {
        if (BaseString_Check(value))
            Py_INCREF(value);
        else if (!(value = PyObject_Str(value))) {
            Py_DECREF(normkey);
            Py_DECREF(key);
            return -1;
        }

        tmp = ENCODE_ATTRIBUTE(self, value);
        Py_DECREF(value);
        if (!tmp) {
            Py_DECREF(key);
            Py_DECREF(normkey);
            return -1;
        }
        value = tmp;
        if (!PyString_CheckExact(value) && !PyString_Check(value)) {
            Py_DECREF(value);
            Py_DECREF(key);
            Py_DECREF(normkey);
            PyErr_SetString(TDI_E_ModelError,
                            "Encoded value must be a string");
            return -1;
        }
    }

    item = (tdi_attr_t *)PyDict_GetItem(self->attr, normkey);
    tmp = tdi_attr_new(item ? item->key : key, value);
    Py_DECREF(value);
    if (!tmp) {
        Py_DECREF(key);
        Py_DECREF(normkey);
        return -1;
    }
    subresult = PyDict_SetItem(self->attr, normkey, tmp);
    Py_DECREF(tmp);
    Py_DECREF(key);
    Py_DECREF(normkey);

    return subresult;
}

static PyMappingMethods TDI_NodeType_as_mapping = {
    0,                                /* mp_length */
    (binaryfunc)TDI_NodeType_getitem,     /* mp_subscript */
    (objobjargproc)TDI_NodeType_setitem,  /* mp_ass_subscript */
};

#define OFF(x) offsetof(tdi_node_t, x)
static PyMemberDef TDI_NodeType_members[] = {
    {"ctx", T_OBJECT, OFF(ctx), 0},

    {NULL}  /* Sentinel */
};
#undef OFF

static PyObject *
TDI_NodeType_gethidden(tdi_node_t *self, void *closure)
{
    if (self->flags & NODE_NOELEMENT)
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static int
TDI_NodeType_sethidden(tdi_node_t *self, PyObject *value, void *closure)
{
    int bool_noelement;

    if (!value) {
        PyErr_SetString(PyExc_TypeError,
                        "Cannot delete the hiddenelement attribute");
        return -1;
    }

    if ((bool_noelement = PyObject_IsTrue(value)) == -1)
        return -1;

    if (bool_noelement)
        self->flags |= NODE_NOELEMENT;
    else
        self->flags &= ~NODE_NOELEMENT;

    return 0;
}

static PyObject *
TDI_NodeType_getclosed(tdi_node_t *self, void *closure)
{
    if (self->flags & NODE_CLOSED)
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static PyObject *
TDI_NodeType_getcontent(tdi_node_t *self, void *closure)
{
    if (self->content) {
        Py_INCREF(self->content->clean);
        return self->content->clean;
    }

    Py_RETURN_NONE;
}

static int
TDI_NodeType_setcontent(tdi_node_t *self, PyObject *value, void *closure)
{
    PyObject *tmp;
    tdi_content_t *tmp_content;

    if (!value) {
        PyErr_SetString(PyExc_TypeError,
                        "Cannot delete the content attribute");
        return -1;
    }

    if (BaseString_Check(value))
        Py_INCREF(value);
    else if (!(value = PyObject_Str(value)))
        return -1;

    tmp = ENCODE_CONTENT(self, value);
    Py_DECREF(value);
    if (!tmp)
        return -1;
    value = tmp;

    if (!PyString_CheckExact(value) && !PyString_Check(value)) {
        PyErr_SetString(TDI_E_ModelError, "Encoded value must be a string");
        Py_DECREF(value);
        return -1;
    }

    Py_INCREF(tdi_g_empty_dict);
    Py_CLEAR(self->namedict);
    self->namedict = tdi_g_empty_dict;
    tmp_content = self->content;
    self->content = NULL;
    if (!tmp_content) {
        tmp_content = tdi_content_new();
    }
    else {
        Py_CLEAR(tmp_content->clean);
        Py_CLEAR(tmp_content->with_escapes);
    }
    tmp_content->clean = value;
    self->content = tmp_content;

    return 0;
}

static PyObject *
TDI_NodeType_getraw(tdi_node_t *self, void *closure)
{
    return tdi_raw_node_new(self);
}

static PyGetSetDef TDI_NodeType_getset[] = {
    {"content",
     (getter)TDI_NodeType_getcontent,
     (setter)TDI_NodeType_setcontent,
     PyDoc_STR(
"Node content\n\
\n\
The property can be set to a unicode or str value, which will be\n\
escaped and encoded (in case of unicode). It replaces the content or\n\
child nodes of the node completely.\n\
\n\
The property can be read and will either return the *raw* content of\n\
the node (it may even contain markup) - or ``None`` if the node has\n\
subnodes.\n\
\n\
:Type: ``basestring`` or ``None``"),
     NULL},

    {"hiddenelement",
     (getter)TDI_NodeType_gethidden,
     (setter)TDI_NodeType_sethidden,
     PyDoc_STR(
"Hidden node markup?\n\
\n\
:Type: ``bool``"),
     NULL},

    {"closedelement",
     (getter)TDI_NodeType_getclosed,
     NULL,
     PyDoc_STR(
"Self-closed element? (read-only)\n\
\n\
:Type: ``bool``"),
     NULL},

    {"raw",
     (getter)TDI_NodeType_getraw,
     NULL,
     PyDoc_STR(
"Raw node\n\
\n\
:Type: `RawNode`"),
     NULL},

    {NULL}  /* Sentinel */
};

static int
TDI_NodeType_traverse(tdi_node_t *self, visitproc visit, void *arg)
{
    Py_VISIT(self->sep);
    Py_VISIT(self->callback);
    Py_VISIT(self->overlays);
    Py_VISIT(self->nodes);
    Py_VISIT(self->namedict);
    Py_VISIT(self->modelscope);
    TDI_SCOPE_VISIT(self->scope);
    TDI_OVERLAY_VISIT(self->overlay);
    TDI_CONTENT_VISIT(self->content);
    Py_VISIT(self->complete);
    Py_VISIT(self->tagname);
    Py_VISIT(self->attr);
    Py_VISIT(self->endtag);
    Py_VISIT(self->name);
    Py_VISIT((PyObject *)self->encoder);
    Py_VISIT((PyObject *)self->decoder);
    Py_VISIT(self->ctx);
    Py_VISIT((PyObject *)self->model);

    return 0;
}

static int
TDI_NodeType_clear(tdi_node_t *self)
{
    if (self->weakreflist)
        PyObject_ClearWeakRefs((PyObject *)self);
    node_clear(self);

    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_NodeType)

PyDoc_STRVAR(TDI_NodeType__doc__,
"User visible node object\n\
\n\
This type cannot be instantiated directly, you get instances during the\n\
rendering phase, created from `TemplateNode`\\s.\n\
\n\
:IVariables:\n\
  `ctx` : ``tuple``\n\
    The node context (``None`` if there isn't one). Node contexts\n\
    are created on repetitions for all (direct and no-direct) subnodes of\n\
    the repeated node. The context is a ``tuple``, which contains for\n\
    repeated nodes the position within the loop (starting with ``0``), the\n\
    actual item and a tuple of the fixed parameters. The last two are also\n\
    passed to the repeat callback function directly. For separator\n\
    nodes, ``ctx[1]`` is a tuple containing the items before the separator\n\
    and after it. Separator indices are starting with ``0``, too.");

PyTypeObject TDI_NodeType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".Node",                            /* tp_name */
    sizeof(tdi_node_t),                                 /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_NodeType_dealloc,                   /* tp_dealloc */
    0,                                                  /* tp_print */
    0,                                                  /* tp_getattr */
    0,                                                  /* tp_setattr */
    0,                                                  /* tp_compare */
    0,                                                  /* tp_repr */
    0,                                                  /* tp_as_number */
    0,                                                  /* tp_as_sequence */
    &TDI_NodeType_as_mapping,                           /* tp_as_mapping */
    0,                                                  /* tp_hash */
    (ternaryfunc)TDI_NodeType_call,                     /* tp_call */
    0,                                                  /* tp_str */
    (getattrofunc)TDI_NodeType_getattro,                /* tp_getattro */
    0,                                                  /* tp_setattro */
    0,                                                  /* tp_as_buffer */
    Py_TPFLAGS_HAVE_WEAKREFS                            /* tp_flags */
    | Py_TPFLAGS_HAVE_CLASS
    | Py_TPFLAGS_HAVE_GC,
    TDI_NodeType__doc__,                                /* tp_doc */
    (traverseproc)TDI_NodeType_traverse,                /* tp_traverse */
    (inquiry)TDI_NodeType_clear,                        /* tp_clear */
    0,                                                  /* tp_richcompare */
    offsetof(tdi_node_t, weakreflist),                  /* tp_weaklistoffset */
    0,                                                  /* tp_iter */
    0,                                                  /* tp_iternext */
    TDI_NodeType_methods,                               /* tp_methods */
    TDI_NodeType_members,                               /* tp_members */
    TDI_NodeType_getset                                 /* tp_getset */
};

/* ---------------------- END TDI_NodeType DEFINITION ---------------------- */
