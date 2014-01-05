/*
 * Copyright 2013 - 2014
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
#include "tdi_soup_lexer.h"

#include "obj_soup_lexer.h"

typedef struct soup_lexer {
    PyObject_HEAD

    tdi_soup_lexer *lexer;
    PyObject *listener;
    PyObject *normalize;
} soup_lexer;


static PyObject *
lexer_normalize(void *self, PyObject *name)
{
    PyObject *normalize = ((soup_lexer *)self)->normalize;
    PyObject *tmp, *result;

    Py_INCREF(normalize);
    tmp = PyObject_CallFunction(normalize, "(O)", name);
    Py_DECREF(normalize);

    if (tmp) {
        result = PyObject_Str(tmp);
        Py_DECREF(tmp);
        return result;
    }

    return NULL;
}

static int
lexer_callback(tdi_lexer_event *event, void *self)
{
    PyObject *listener = ((soup_lexer *)self)->listener;
    PyObject *result = NULL;

    Py_INCREF(listener);

    switch (event->type) {
    case TDI_LEXER_EVENT_TEXT:
        result = PyObject_CallMethod(listener, "handle_text", "(O)",
                                     event->info.text.data);
        break;

    case TDI_LEXER_EVENT_STARTTAG:
        result = PyObject_CallMethod(listener, "handle_starttag", "(OOOO)",
                                     event->info.starttag.name,
                                     event->info.starttag.attr,
                                     (event->info.starttag.closed
                                        ? (Py_INCREF(Py_True), Py_True)
                                        : (Py_INCREF(Py_False), Py_False)
                                     ),
                                     event->info.starttag.data);
        break;

    case TDI_LEXER_EVENT_ENDTAG:
        result = PyObject_CallMethod(listener, "handle_endtag", "(OO)",
                                     event->info.endtag.name,
                                     event->info.endtag.data);
        break;

    case TDI_LEXER_EVENT_COMMENT:
        result = PyObject_CallMethod(listener, "handle_comment", "(O)",
                                     event->info.comment.data);
        break;

    case TDI_LEXER_EVENT_MSECTION:
        result = PyObject_CallMethod(listener, "handle_msection", "(OOO)",
                                     event->info.msection.name,
                                     event->info.msection.value,
                                     event->info.msection.data);
        break;

    case TDI_LEXER_EVENT_DECL:
        result = PyObject_CallMethod(listener, "handle_decl", "(OOO)",
                                     event->info.decl.name,
                                     event->info.decl.value,
                                     event->info.decl.data);
        break;

    case TDI_LEXER_EVENT_PI:
        result = PyObject_CallMethod(listener, "handle_pi", "(O)",
                                     event->info.pi.data);
        break;

    case TDI_LEXER_EVENT_ESCAPE:
        result = PyObject_CallMethod(listener, "handle_escape", "(OO)",
                                     event->info.escape.escaped,
                                     event->info.escape.data);
        break;
    }

    Py_DECREF(listener);
    if (!result)
        return -1;
    Py_DECREF(result);

    return 0;
}

static PyObject *
lexer_error(tdi_soup_lexer *lexer)
{
    switch (tdi_soup_lexer_error_get(lexer)) {
    case TDI_LEXER_ERR_ENV:
        break;

    case TDI_LEXER_ERR_EOF:
        PyErr_Format(TDI_E_LexerEOFError, "Unfinished parser state %s",
                     tdi_soup_lexer_state_get(lexer));
        break;

    case TDI_LEXER_ERR_FINAL:
        PyErr_SetString(TDI_E_LexerFinalizedError,
                        "The lexer was already finalized");
        break;
    }
    return NULL;
}

/* ------------------ BEGIN TDI_SoupLexerType DEFINITION ----------------- */

PyDoc_STRVAR(TDI_SoupLexerType_cdata__doc__,
"cdata(self)\n\
\n\
Set CDATA state");

static PyObject *
TDI_SoupLexerType_cdata(soup_lexer *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"normalize", "name", NULL};
    PyObject *normalize, *name;
    int res;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OS", kwlist,
                                     &normalize, &name))
        return NULL;

    Py_INCREF(normalize);
    Py_CLEAR(self->normalize);
    self->normalize = normalize;

    res = tdi_soup_lexer_state_cdata(self->lexer, lexer_normalize, self,
                                     name);
    if (res == -1)
        return lexer_error(self->lexer);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(TDI_SoupLexerType_finalize__doc__,
"finalize(self)\n\
\n\
Finalize the lexer\n\
\n\
This processes the rest buffer (if any)\n\
\n\
:Exceptions:\n\
  - `LexerEOFError` : The rest buffer could not be consumed");

static PyObject *
TDI_SoupLexerType_finalize(soup_lexer *self, PyObject *args)
{
    if (tdi_soup_lexer_finalize(self->lexer) == -1)
        return lexer_error(self->lexer);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(TDI_SoupLexerType_feed__doc__,
"feed(self, food)\n\
\n\
:Parameters:\n\
  `food` : ``str``\n\
    The data to process");

static PyObject *
TDI_SoupLexerType_feed(soup_lexer *self, PyObject *args, PyObject *kwds)
{
    PyObject *food;
    static char *kwlist[] = {"food", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "S", kwlist,
                                     &food))
        return NULL;

    if (tdi_soup_lexer_feed(self->lexer, food) == -1)
        return lexer_error(self->lexer);

    Py_RETURN_NONE;
}

static struct PyMethodDef TDI_SoupLexerType_methods[] = {
    {"feed",
     (PyCFunction)TDI_SoupLexerType_feed,             METH_KEYWORDS,
     TDI_SoupLexerType_feed__doc__},

    {"finalize",
     (PyCFunction)TDI_SoupLexerType_finalize,         METH_NOARGS,
     TDI_SoupLexerType_finalize__doc__},

    {"cdata",
     (PyCFunction)TDI_SoupLexerType_cdata,            METH_KEYWORDS,
     TDI_SoupLexerType_cdata__doc__},

    {NULL, NULL}  /* Sentinel */
};


static PyObject *
TDI_SoupLexerType_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"listener", "conditional_ie_comments", NULL};
    PyObject *listener, *ie_comments_o = NULL;
    soup_lexer *self;
    int ie_comments = 1;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O", kwlist,
                                     &listener, &ie_comments_o))
        return NULL;

    if (ie_comments_o && (ie_comments = PyObject_IsTrue(ie_comments_o)) == -1)
        return NULL;

    if (!(self = GENERIC_ALLOC(type)))
        return NULL;

    Py_INCREF(listener);
    self->listener = listener;
    self->normalize = NULL;

    self->lexer = tdi_soup_lexer_new(lexer_callback, self, ie_comments);
    if (!self->lexer) {
        Py_DECREF(self);
        return NULL;
    }

    return (PyObject *)self;
}

static int
TDI_SoupLexerType_traverse(soup_lexer *self, visitproc visit, void *arg)
{
    Py_VISIT(self->listener);
    Py_VISIT(self->normalize);

    return 0;
}

static int
TDI_SoupLexerType_clear(soup_lexer *self)
{
    TDI_SOUP_LEXER_CLEAR(self->lexer);
    Py_CLEAR(self->listener);
    Py_CLEAR(self->normalize);

    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_SoupLexerType)

PyDoc_STRVAR(TDI_SoupLexerType__doc__,
"``SoupLexer(listener, conditional_ie_comments=True)``\n\
\n\
(X)HTML Tagsoup Lexer");

PyTypeObject TDI_SoupLexerType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".SoupLexer",                       /* tp_name */
    sizeof(soup_lexer),                                 /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_SoupLexerType_dealloc,              /* tp_dealloc */
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
    | Py_TPFLAGS_HAVE_GC,
    TDI_SoupLexerType__doc__,                           /* tp_doc */
    (traverseproc)TDI_SoupLexerType_traverse,           /* tp_traverse */
    (inquiry)TDI_SoupLexerType_clear,                   /* tp_clear */
    0,                                                  /* tp_richcompare */
    0,                                                  /* tp_weaklistoffset */
    0,                                                  /* tp_iter */
    0,                                                  /* tp_iternext */
    TDI_SoupLexerType_methods,                          /* tp_methods */
    0,                                                  /* tp_members */
    0,                                                  /* tp_getset */
    0,                                                  /* tp_base */
    0,                                                  /* tp_dict */
    0,                                                  /* tp_descr_get */
    0,                                                  /* tp_descr_set */
    0,                                                  /* tp_dictoffset */
    0,                                                  /* tp_init */
    0,                                                  /* tp_alloc */
    TDI_SoupLexerType_new,                              /* tp_new */
};

/* ------------------- END TDI_SoupLexerType DEFINITION ------------------ */

