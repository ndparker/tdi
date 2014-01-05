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
#include "tdi_soup_parser.h"

#include "obj_soup_parser.h"

typedef struct soup_parser {
    PyObject_HEAD

    tdi_soup_parser *parser;
    PyObject *listener;
    PyObject *nestable;
    PyObject *cdata;
    PyObject *empty;
    PyObject *normalize;
} soup_parser;


static PyObject *
parser_normalize(void *self, PyObject *name)
{
    PyObject *tmp, *norm = ((soup_parser *)self)->normalize;
    PyObject *result;

    Py_INCREF(norm);
    tmp = PyObject_CallFunction(norm, "O", name);
    Py_DECREF(norm);
    if (!tmp)
        return NULL;

    result = PyObject_Str(tmp);
    Py_DECREF(tmp);

    return result;
}

static int
parser_nestable(void *self, PyObject *outer, PyObject *inner)
{
    PyObject *nestable = ((soup_parser *)self)->nestable;
    PyObject *tmp;
    int res;

    Py_INCREF(nestable);
    tmp = PyObject_CallFunction(nestable, "(OO)", outer, inner);
    Py_DECREF(nestable);
    if (!tmp)
        return -1;

    res = PyObject_IsTrue(tmp);
    Py_DECREF(tmp);
    return res;
}

static int
parser_cdata(void *self, PyObject *name)
{
    PyObject *cdata = ((soup_parser *)self)->cdata;
    PyObject *tmp;
    int res;

    Py_INCREF(cdata);
    tmp = PyObject_CallFunction(cdata, "(O)", name);
    Py_DECREF(cdata);
    if (!tmp)
        return -1;

    res = PyObject_IsTrue(tmp);
    Py_DECREF(tmp);
    return res;
}

static int
parser_empty(void *self, PyObject *name)
{
    PyObject *empty = ((soup_parser *)self)->empty;
    PyObject *tmp;
    int res;

    Py_INCREF(empty);
    tmp = PyObject_CallFunction(empty, "(O)", name);
    Py_DECREF(empty);
    if (!tmp)
        return -1;

    res = PyObject_IsTrue(tmp);
    Py_DECREF(tmp);
    return res;
}

static int
parser_callback(tdi_parser_event *event, void *self)
{
    PyObject *listener = ((soup_parser *)self)->listener;
    PyObject *result = NULL;

    Py_INCREF(listener);

    switch (event->type) {
    case TDI_PARSER_EVENT_TEXT:
        result = PyObject_CallMethod(listener, "handle_text", "(O)",
                                     event->info.text.data);
        break;

    case TDI_PARSER_EVENT_STARTTAG:
        result = PyObject_CallMethod(listener, "handle_starttag", "(OOOO)",
                                     event->info.starttag.name,
                                     event->info.starttag.attr,
                                     (event->info.starttag.closed
                                        ? (Py_INCREF(Py_True), Py_True)
                                        : (Py_INCREF(Py_False), Py_False)
                                     ),
                                     event->info.starttag.data);
        break;

    case TDI_PARSER_EVENT_ENDTAG:
        result = PyObject_CallMethod(listener, "handle_endtag", "(OO)",
                                     event->info.endtag.name,
                                     event->info.endtag.data);
        break;

    case TDI_PARSER_EVENT_COMMENT:
        result = PyObject_CallMethod(listener, "handle_comment", "(O)",
                                     event->info.comment.data);
        break;

    case TDI_PARSER_EVENT_MSECTION:
        result = PyObject_CallMethod(listener, "handle_msection", "(OOO)",
                                     event->info.msection.name,
                                     event->info.msection.value,
                                     event->info.msection.data);
        break;

    case TDI_PARSER_EVENT_DECL:
        result = PyObject_CallMethod(listener, "handle_decl", "(OOO)",
                                     event->info.decl.name,
                                     event->info.decl.value,
                                     event->info.decl.data);
        break;

    case TDI_PARSER_EVENT_PI:
        result = PyObject_CallMethod(listener, "handle_pi", "(O)",
                                     event->info.pi.data);
        break;

    case TDI_PARSER_EVENT_ESCAPE:
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
parser_error(tdi_soup_parser *parser)
{
    switch (tdi_soup_parser_error_get(parser)) {
    case TDI_PARSER_ERR_ENV:
        break;

    case TDI_PARSER_ERR_LEXER_EOF:
        PyErr_Format(TDI_E_LexerEOFError, "Unfinished parser state %s",
                     tdi_soup_parser_lexer_state_get(parser));
        break;

    case TDI_PARSER_ERR_LEXER_FINAL:
        PyErr_SetString(TDI_E_LexerFinalizedError,
                        "The lexer was already finalized");
        break;
    }
    return NULL;
}

/* ------------------ BEGIN TDI_SoupParserType DEFINITION ----------------- */

PyDoc_STRVAR(TDI_SoupParserType_finalize__doc__,
"finalize(self)\n\
\n\
:See: `ParserInterface`\n\
\n\
:Exceptions:\n\
  - `LexerEOFError` : EOF in the middle of a state");

static PyObject *
TDI_SoupParserType_finalize(soup_parser *self, PyObject *args)
{
    if (tdi_soup_parser_finalize(self->parser) == -1)
        return parser_error(self->parser);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(TDI_SoupParserType_feed__doc__,
":See: `ParserInterface`");

static PyObject *
TDI_SoupParserType_feed(soup_parser *self, PyObject *args, PyObject *kwds)
{
    PyObject *food;
    static char *kwlist[] = {"food", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "S", kwlist,
                                     &food))
        return NULL;

    if (tdi_soup_parser_feed(self->parser, food) == -1)
        return parser_error(self->parser);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(TDI_SoupParserType_xml__doc__,
"xml(cls, listener)\n\
\n\
Construct a parser using the `XMLDTD`\n\
\n\
:Parameters:\n\
  `listener` : `ListenerInterface`\n\
    The building listener\n\
\n\
:Return: The new parser instance\n\
:Rtype: `SoupParser`");

static PyObject *
TDI_SoupParserType_xml(PyObject *cls, PyObject *args, PyObject *kwds)
{
    PyObject *listener, *dtd, *tmp;
    static char *kwlist[] = {"listener", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", kwlist,
                                     &listener))
        return NULL;

    if (!(dtd = PyImport_ImportModule("tdi.markup.soup.dtd")))
        return NULL;

    tmp = PyObject_GetAttrString(dtd, "XMLDTD");
    Py_DECREF(dtd);
    if (!tmp)
        return NULL;

    dtd = PyObject_CallFunction(tmp, "");
    Py_DECREF(tmp);
    if (!dtd)
        return NULL;

    tmp = PyObject_CallFunction(cls, "(OO)", listener, dtd);
    Py_DECREF(dtd);
    return tmp;
}

PyDoc_STRVAR(TDI_SoupParserType_html__doc__,
"html(cls, listener)\n\
\n\
Construct a parser using the `HTMLDTD`\n\
\n\
:Parameters:\n\
  `listener` : `ListenerInterface`\n\
    The building listener\n\
\n\
:Return: The new parser instance\n\
:Rtype: `SoupParser`");

static PyObject *
TDI_SoupParserType_html(PyObject *cls, PyObject *args, PyObject *kwds)
{
    PyObject *listener, *dtd, *tmp;
    static char *kwlist[] = {"listener", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", kwlist,
                                     &listener))
        return NULL;

    if (!(dtd = PyImport_ImportModule("tdi.markup.soup.dtd")))
        return NULL;

    tmp = PyObject_GetAttrString(dtd, "HTMLDTD");
    Py_DECREF(dtd);
    if (!tmp)
        return NULL;

    dtd = PyObject_CallFunction(tmp, "");
    Py_DECREF(tmp);
    if (!dtd)
        return NULL;

    tmp = PyObject_CallFunction(cls, "(OO)", listener, dtd);
    Py_DECREF(dtd);
    return tmp;
}

static struct PyMethodDef TDI_SoupParserType_methods[] = {
    {"html",
     (PyCFunction)TDI_SoupParserType_html,    METH_CLASS | METH_KEYWORDS,
     TDI_SoupParserType_html__doc__},

    {"xml",
     (PyCFunction)TDI_SoupParserType_xml,     METH_CLASS | METH_KEYWORDS,
     TDI_SoupParserType_xml__doc__},

    {"feed",
     (PyCFunction)TDI_SoupParserType_feed,                 METH_KEYWORDS,
     TDI_SoupParserType_feed__doc__},

    {"finalize",
     (PyCFunction)TDI_SoupParserType_finalize,             METH_NOARGS,
     TDI_SoupParserType_finalize__doc__},

    {NULL, NULL}  /* Sentinel */
};


static PyObject *
TDI_SoupParserType_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"listener", "dtd", NULL};
    PyObject *listener, *dtd, *decoder;
    soup_parser *self;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO", kwlist,
                                     &listener, &dtd))
        return NULL;

    if (!(self = GENERIC_ALLOC(type)))
        return NULL;

    Py_INCREF(listener);
    self->listener = listener;

    if (!(self->nestable = PyObject_GetAttrString(dtd, "nestable")))
        goto error;

    if (!(self->cdata = PyObject_GetAttrString(dtd, "cdata")))
        goto error;

    if (!(self->empty = PyObject_GetAttrString(dtd, "empty")))
        goto error;

    if (!(decoder = PyObject_GetAttrString(listener, "decoder")))
        goto error;

    self->normalize = PyObject_GetAttrString(decoder, "normalize");
    Py_DECREF(decoder);
    if (!self->normalize)
        goto error;

    self->parser = tdi_soup_parser_new(
        parser_callback, self,
        parser_nestable, self,
        parser_cdata, self,
        parser_empty, self,
        parser_normalize, self
    );
    if (!self->parser)
        goto error;

    return (PyObject *)self;

error:
    Py_DECREF(self);
    return NULL;
}

static int
TDI_SoupParserType_traverse(soup_parser *self, visitproc visit, void *arg)
{
    Py_VISIT(self->listener);
    Py_VISIT(self->nestable);
    Py_VISIT(self->cdata);
    Py_VISIT(self->empty);
    Py_VISIT(self->normalize);

    return 0;
}

static int
TDI_SoupParserType_clear(soup_parser *self)
{
    TDI_SOUP_PARSER_CLEAR(self->parser);
    Py_CLEAR(self->listener);
    Py_CLEAR(self->nestable);
    Py_CLEAR(self->cdata);
    Py_CLEAR(self->empty);
    Py_CLEAR(self->normalize);

    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_SoupParserType)

PyDoc_STRVAR(TDI_SoupParserType__doc__,
"``SoupParser(listener, dtd)``\n\
\n\
(X)HTML Tagsoup Parser");

PyTypeObject TDI_SoupParserType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".SoupParser",                      /* tp_name */
    sizeof(soup_parser),                                /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_SoupParserType_dealloc,             /* tp_dealloc */
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
    TDI_SoupParserType__doc__,                          /* tp_doc */
    (traverseproc)TDI_SoupParserType_traverse,          /* tp_traverse */
    (inquiry)TDI_SoupParserType_clear,                  /* tp_clear */
    0,                                                  /* tp_richcompare */
    0,                                                  /* tp_weaklistoffset */
    0,                                                  /* tp_iter */
    0,                                                  /* tp_iternext */
    TDI_SoupParserType_methods,                         /* tp_methods */
    0,                                                  /* tp_members */
    0,                                                  /* tp_getset */
    0,                                                  /* tp_base */
    0,                                                  /* tp_dict */
    0,                                                  /* tp_descr_get */
    0,                                                  /* tp_descr_set */
    0,                                                  /* tp_dictoffset */
    0,                                                  /* tp_init */
    0,                                                  /* tp_alloc */
    TDI_SoupParserType_new,                             /* tp_new */
};

/* ------------------- END TDI_SoupParserType DEFINITION ------------------ */

