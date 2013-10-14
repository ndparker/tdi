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

#include "obj_soup_encoding_detect_filter.h"

typedef struct encoding_detect_filter {
    PyObject_HEAD
    PyObject *weakreflist;

    PyObject *builder;
    PyObject *normalize;
    PyObject *meta;
} encoding_detect_filter;

/* --------------------------- END DECLARATIONS -------------------------- */

/*
 * Extract bare, stripped value from attribute
 */
static PyObject *
bare_value(PyObject *value)
{
    const char *p, *ps, *o, *os;
    PyObject *result;

    if (value == Py_None)
        return PyString_FromString("");

    if (!(value = PyObject_Str(value)))
        return NULL;

    o = p = PyString_AS_STRING(value);
    os = ps = p + PyString_GET_SIZE(value);
    if ((*p == '"' || *p == '\'') && !(++p < --ps)) {
        Py_DECREF(value);
        return PyString_FromString("");
    }
    while (p < ps) {switch (*p) {
    case ' ': case '\t': case '\r': case '\n': case '\f': ++p; continue;
    } break;}
    while (p < ps) {switch (*(ps - 1)) {
    case ' ': case '\t': case '\r': case '\n': case '\f': --ps; continue;
    } break;}

    if (o == p && os == ps)
        return value;

    result = PyString_FromStringAndSize(p, ps - p);
    Py_DECREF(value);
    return result;
}


/*
 * Extract charset from content type
 */
static PyObject *
ctype_charset(PyObject *ctype)
{
    const char *p, *ps, *k, *ks, *v, *vs;
    PyObject *tmp, *result;
    char c;

    p = PyString_AS_STRING(ctype);
    ps = p + PyString_GET_SIZE(ctype);

    /* Skip the ctype */
    /* ************** */

    /* main type */
    while (p < ps) {switch (*p++) {
    case '/':
        break;

    case ' ': case '\t': case '\r': case '\n': case '\f': case '\v':
    case ';':
        return NULL;

    default:
        continue;
    } break;}
    if (!(p < ps)) return NULL;

    /* subtype */
    while (p < ps) {switch (*p++) {
    case ';':
        --p;
        break;

    case '/':
        return NULL;

    default:
        continue;
    } break;}
    if (!(p < ps)) return NULL;


    /* Extract parameters */
    /* ****************** */

    /* main loop */
    while (p < ps) {
        /* WS before ; */
        while (p < ps) {switch (*p++) {
        case ' ': case '\t': case '\r': case '\n': case '\f': case '\v':
            continue;

        default:
            --p; break;
        } break;}
        if (!(p < ps) || *p++ != ';') return NULL;

        /* WS before key */
        while (p < ps) {switch (c = *p++) {
        case ' ': case '\t': case '\r': case '\n': case '\f': case '\v':
            continue;

        case '(': case ')': case '<': case '>': case '@': case ',': case ';':
        case ':': case '\\': case '"': case '/': case '[': case ']': case '?':
            return NULL;

        default:
            if (c < 32) return NULL;
            --p;
            break;
        } break;}
        if (!(p < ps)) return NULL;

        /* key */
        k = p;
        while (p < ps) {switch (c = *p++) {
        case ' ': case '\t': case '\r': case '\n': case '\f': case '\v':
        case '=':
            ks = --p;
            break;

        case '(': case ')': case '<': case '>': case '@': case ',': case ';':
        case ':': case '\\': case '"': case '/': case '[': case ']': case '?':
            return NULL;

        default:
            if (c < 32) return NULL;
            continue;
        } break;}
        if (!(p < ps)) return NULL;

        /* WS before = */
        while (p < ps) {switch (*p++) {
        case ' ': case '\t': case '\r': case '\n': case '\f': case '\v':
            continue;

        default:
            --p; break;
        } break;}
        if (!(p < ps) || *p++ != '=') return NULL;

        /* WS after = */
        while (p < ps) {switch (*p++) {
        case ' ': case '\t': case '\r': case '\n': case '\f': case '\v':
            continue;

        default:
            --p; break;
        } break;}
        if (!(p < ps)) return NULL;

        /* value */
        v = p;
        if (*p == '"') { /* quoted string */
            ++p;
            while (p < ps) {switch (*p++) {
            case '\0': return NULL;
            case '\\':
                if (!(p < ps) || *p++ != '"') return NULL;
                continue;

            case '"':
                vs = p--;
                break;

            default:
                continue;
            } break;}
            if (!(p < ps)) return NULL;
            if (!strncasecmp(k, "charset", ks - k)) {
                if (!(tmp = PyString_FromStringAndSize(v, vs - v)))
                    return NULL;
                result = bare_value(tmp);
                Py_DECREF(tmp);
                return result;
            }
        }
        else {         /* token */
            while (p < ps) {switch (c = *p++) {
            case ' ': case '\t': case '\r': case '\n': case '\f': case '\v':
            case ';':
                vs = --p;
                break;

            case '(': case ')': case '<': case '>': case '@': case ',':
            case ':': case '\\': case '"': case '/': case '[': case ']':
            case '?':
                return NULL;

            default:
                if (c < 32) return NULL;
                continue;
            } break;}
            if (!(p < ps)) vs = p;
            if (!strncasecmp(k, "charset", ks - k))
                return PyString_FromStringAndSize(v, vs - v);
        }

    }
    return NULL;
}


/*
 * Call handle_encoding on builder
 */
static int
handle_encoding(encoding_detect_filter *self, PyObject *charset,
                PyObject *ctype)
{
    PyObject *result, *final = NULL;

    if (charset)
        final = (Py_INCREF(charset), charset);
    else if (ctype) {
        if (!(final = ctype_charset(ctype)) && PyErr_Occurred())
            return -1;
    }

    if (final && PyString_GET_SIZE(final) > 0) {
        result = PyObject_CallMethod(self->builder, "handle_encoding", "O",
                                     final);
        Py_DECREF(final);
        if (!result)
            return -1;
        Py_DECREF(result);
    }

    return 0;
}

/* ----------------------------- meta PARSER ----------------------------- */

static int
check_meta(encoding_detect_filter *self, PyObject *attr)
{
    PyObject *key, *value, *tup, *iter, *tmp;
    PyObject *charset, *charset_value = NULL;
    PyObject *http_equiv, *content, *ctype_value = NULL;
    int res, cmp, equiv = 0;

    if (!(charset = PyObject_CallFunction(self->normalize, "s", "charset")))
        return -1;
    if (!(http_equiv = PyObject_CallFunction(self->normalize, "s",
                                             "http-equiv")))
        goto error_charset;
    if (!(content = PyObject_CallFunction(self->normalize, "s", "content")))
        goto error_http_equiv;

    if (!(iter = PyObject_GetIter(attr)))
        goto error_statics;

    while ((tup = PyIter_Next(iter))) {
        if (PyArg_Parse(tup, "(OO)", &key, &value) == -1)
            goto error_tup;
        if (!(key = PyObject_CallFunction(self->normalize, "O", key)))
            goto error_tup;

        /* <meta charset="xxx"> */
        if (PyObject_Cmp(key, charset, &cmp) == -1)
            goto error_key;
        if (!cmp) {
            if (charset_value) {
                Py_DECREF(charset_value);
            }
            if (!(charset_value = bare_value(value)))
                goto error_key;
        }

        /* <meta http-equiv="content-type" content="xxx"> */
        else {
            if (PyObject_Cmp(key, http_equiv, &cmp) == -1)
                goto error_key;
            if (!cmp) {
                if (!(value = bare_value(value)))
                    goto error_key;
                if (!(tmp = PyObject_CallMethod(value, "lower", "")))
                    goto error_value;
                cmp = strcmp(PyString_AS_STRING(tmp), "content-type");
                Py_DECREF(tmp);
                if (!cmp) equiv = 1;
            }
            else {
                if (PyObject_Cmp(key, content, &cmp) == -1)
                    goto error_key;
                if (!cmp) {
                    if (ctype_value) {
                        Py_DECREF(ctype_value);
                    }
                    if (!(ctype_value = bare_value(value)))
                        goto error_key;
                }
            }
        }

        Py_DECREF(key);
        Py_DECREF(tup);
    }
    if (PyErr_Occurred())
        goto error_iter;
    Py_DECREF(iter);

    res = handle_encoding(self, charset_value, equiv ? ctype_value : NULL);

    Py_DECREF(content);
    Py_DECREF(http_equiv);
    Py_DECREF(charset);
    Py_XDECREF(ctype_value);
    Py_XDECREF(charset_value);
    return res;

error_value:
    Py_DECREF(value);
error_key:
    Py_DECREF(key);
error_tup:
    Py_DECREF(tup);
error_iter:
    Py_DECREF(iter);
error_statics:
    Py_DECREF(content);
    Py_XDECREF(ctype_value);
error_http_equiv:
    Py_DECREF(http_equiv);
error_charset:
    Py_DECREF(charset);
    Py_XDECREF(charset_value);
    return -1;
}

/* --------------------------- END meta PARSER --------------------------- */

/* ------------------------------ pi PARSER ------------------------------ */

static int check_pi(encoding_detect_filter *self, PyObject *data)
{
    const char *p, *ps, *k, *ks, *v, *vs;
    PyObject *tmp, *value;
    int res;

    p = PyString_AS_STRING(data);
    ps = p + PyString_GET_SIZE(data);
    if (ps - p < 8) return 0;
    if (*p++ != '<') return 0;
    if (*p++ != '?') return 0;

    /* WS */
    while (p < ps) {switch (*p++) {
    case ' ': case '\t': case '\r': case '\n': case '\f': case '\v':
        continue;
    default: --p; break;
    } break;}
    if (ps - p < 4) return 0;

    /* xml */
    if (*p != 'x' && *p != 'X') return 0;
    ++p;
    if (*p != 'm' && *p != 'M') return 0;
    ++p;
    if (*p != 'l' && *p != 'L') return 0;
    if (!(++p < ps)) return 0;

    /* WS */
    switch (*p++) {
    case ' ': case '\t': case '\r': case '\n': case '\f': case '\v': break;
    default: return 0;
    }

    /* attr loop */
    while (p < ps) {
        while (p < ps) {switch (*p++) {
        case ' ': case '\t': case '\r': case '\n': case '\f': case '\v':
            continue;
        default: --p; break;
        } break;}
        if (!(p < ps)) return 0;
        /* Finish */
        if (*p == '?') {
            if (!(++p < ps)) return 0;
            if (*p != '>') return 0;
            if (!(tmp = PyString_FromString("utf-8")))
                return -1;
            res = handle_encoding(self, tmp, NULL);
            Py_DECREF(tmp);
            return res;
        }

        /* key */
        k = p;
        while (p < ps) {switch (*p++) {
        case ' ': case '\t': case '\r': case '\n': case '\f': case '\v':
        case '=':
            ks = --p; break;
        case '?':
            return 0;
        default:
            continue;
        } break;}
        if (!(p < ps)) return 0;

        /* WS before = */
        while (p < ps) {switch (*p++) {
        case ' ': case '\t': case '\r': case '\n': case '\f': case '\v':
            continue;
        default: --p; break;
        } break;}
        if (!(p < ps) || *p++ != '=') return 0;

        /* WS after = */
        while (p < ps) {switch (*p++) {
        case ' ': case '\t': case '\r': case '\n': case '\f': case '\v':
            continue;
        default: --p; break;
        } break;}
        if (!(p < ps)) return 0;

        /* value */
        v = p;
        if (!(*p == '"' || *p == '\''))
            return 0;
        ++p;
        while (p < ps) {if (*p++ == *v) {vs = p; break;}}
        if (!(p < ps)) return 0;

        /* yo! */
        if (!strncmp(k, "encoding", ks - k)) {
            if (!(tmp = PyString_FromStringAndSize(v, vs - v)))
                return -1;
            value = bare_value(tmp);
            Py_DECREF(tmp);
            if (!value)
                return -1;
            if (PyString_GET_SIZE(value) == 0) {
                Py_DECREF(value);
                if (!(value = PyString_FromString("utf-8")))
                    return -1;
            }
            res = handle_encoding(self, value, NULL);
            Py_DECREF(value);
            return res;
        }
    }

    return 0;
}

/* ---------------------------- END pi PARSER ---------------------------- */

/* ------------ BEGIN TDI_EncodingDetectFilterType DEFINITION ------------ */

PyDoc_STRVAR(TDI_EncodingDetectFilterType_handle_starttag__doc__,
"handle_starttag(self, name, attr, closed, data)\n\
\n\
Extract encoding from HTML meta element\n\
\n\
Here are samples for the expected formats::\n\
\n\
  <meta charset=\"utf-8\"> <!-- HTML5 -->\n\
\n\
  <meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">\n\
\n\
The event is passed to the builder nevertheless.\n\
\n\
:See: `BuildingListenerInterface`");

static PyObject *
TDI_EncodingDetectFilterType_handle_starttag(encoding_detect_filter *self,
                                             PyObject *args, PyObject *kwds)
{
    PyObject *name, *attr, *closed, *data, *normname;
    static char *kwlist[] = {"name", "attr", "closed", "data", NULL};
    int cmp, res;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOOO", kwlist,
                                     &name, &attr, &closed, &data))
        return NULL;

    if (!(normname = PyObject_CallFunction(self->normalize, "(O)", name)))
        return NULL;

    res = PyObject_Cmp(normname, self->meta, &cmp);
    Py_DECREF(normname);
    if (res == -1)
        return NULL;

    if (!cmp)
        res = check_meta(self, attr);
    if (res == -1)
        return NULL;

    return PyObject_CallMethod(self->builder, "handle_starttag", "(OOOO)",
                               name, attr, closed, data);
}

PyDoc_STRVAR(TDI_EncodingDetectFilterType_handle_pi__doc__,
"handle_pi(self, data)\n\
\n\
Extract encoding from xml declaration\n\
\n\
Here's a sample for the expected format::\n\
\n\
  <?xml version=\"1.0\" encoding=\"ascii\" ?>\n\
\n\
The event is passed to the builder nevertheless.\n\
\n\
:See: `BuildingListenerInterface`");

static PyObject *
TDI_EncodingDetectFilterType_handle_pi(encoding_detect_filter *self,
                                       PyObject *args, PyObject *kwds)
{
    PyObject *data;
    static char *kwlist[] = {"data", NULL};
    int res;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", kwlist,
                                     &data))
        return NULL;

    if (!(data = PyObject_Str(data)))
        return NULL;

    res = check_pi(self, data);
    Py_DECREF(data);
    if (res == -1)
        return NULL;

    return PyObject_CallMethod(self->builder, "handle_pi", "(O)", data);
}

static struct PyMethodDef TDI_EncodingDetectFilterType_methods[] = {
    {"handle_starttag",
     (PyCFunction)TDI_EncodingDetectFilterType_handle_starttag, METH_KEYWORDS,
     TDI_EncodingDetectFilterType_handle_starttag__doc__},

    {"handle_pi",
     (PyCFunction)TDI_EncodingDetectFilterType_handle_pi,       METH_KEYWORDS,
     TDI_EncodingDetectFilterType_handle_pi__doc__},

    {NULL, NULL}  /* Sentinel */
};

static PyObject *
TDI_EncodingDetectFilterType_getattro(encoding_detect_filter *self,
                                      PyObject *name)
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
TDI_EncodingDetectFilterType_traverse(encoding_detect_filter *self,
                                      visitproc visit, void *arg)
{
    Py_VISIT(self->builder);
    Py_VISIT(self->normalize);
    Py_VISIT(self->meta);

    return 0;
}

static int
TDI_EncodingDetectFilterType_clear(encoding_detect_filter *self)
{
    if (self->weakreflist)
        PyObject_ClearWeakRefs((PyObject *)self);

    Py_CLEAR(self->builder);
    Py_CLEAR(self->normalize);
    Py_CLEAR(self->meta);

    return 0;
}

static int
TDI_EncodingDetectFilterType_init(encoding_detect_filter *self, PyObject *args,
                                  PyObject *kwds)
{
    static char *kwlist[] = {"builder", NULL};
    PyObject *builder, *decoder;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", kwlist, &builder))
        return -1;

    self->builder = (Py_INCREF(builder), builder);

    if (!(decoder = PyObject_GetAttrString(self->builder, "decoder")))
        return -1;

    self->normalize = PyObject_GetAttrString(decoder, "normalize");
    Py_DECREF(decoder);
    if (!self->normalize)
        return -1;

    if (!(self->meta = PyObject_CallFunction(self->normalize, "s", "meta")))
        return -1;

    return 0;
}

static PyObject *
TDI_EncodingDetectFilterType_new(PyTypeObject *type, PyObject *args,
                                 PyObject *kwds)
{
    return (PyObject *)GENERIC_ALLOC(type);
}

DEFINE_GENERIC_DEALLOC(TDI_EncodingDetectFilterType)

PyDoc_STRVAR(TDI_EncodingDetectFilterType__doc__,
"Extract template encoding and pass it properly to the builder");

PyTypeObject TDI_SoupEncodingDetectFilterType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".SoupEncodingDetectFilter",        /* tp_name */
    sizeof(encoding_detect_filter),                     /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_EncodingDetectFilterType_dealloc,   /* tp_dealloc */
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
    (getattrofunc)TDI_EncodingDetectFilterType_getattro,/* tp_getattro */
    0,                                                  /* tp_setattro */
    0,                                                  /* tp_as_buffer */
    Py_TPFLAGS_HAVE_WEAKREFS                            /* tp_flags */
    | Py_TPFLAGS_HAVE_CLASS
    | Py_TPFLAGS_BASETYPE
    | Py_TPFLAGS_HAVE_GC
    ,
    TDI_EncodingDetectFilterType__doc__,                /* tp_doc */
    (traverseproc)TDI_EncodingDetectFilterType_traverse,/* tp_traverse */
    (inquiry)TDI_EncodingDetectFilterType_clear,        /* tp_clear */
    0,                                                  /* tp_richcompare */
    offsetof(encoding_detect_filter, weakreflist),      /* tp_weaklistoffset */
    0,                                                  /* tp_iter */
    0,                                                  /* tp_iternext */
    TDI_EncodingDetectFilterType_methods,               /* tp_methods */
    0,                                                  /* tp_members */
    0,                                                  /* tp_getset */
    0,                                                  /* tp_base */
    0,                                                  /* tp_dict */
    0,                                                  /* tp_descr_get */
    0,                                                  /* tp_descr_set */
    0,                                                  /* tp_dictoffset */
    (initproc)TDI_EncodingDetectFilterType_init,        /* tp_init */
    0,                                                  /* tp_alloc */
    TDI_EncodingDetectFilterType_new,                   /* tp_new */
};

/* ------------- END TDI_EncodingDetectFilterType DEFINITION ------------- */
