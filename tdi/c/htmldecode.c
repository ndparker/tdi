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

#include "htmldecode.h"

#define U(c) ((Py_UNICODE)(c))
#define REPLCHAR (U(0xFFFD))

#define ERR_STRICT (0)
#define ERR_IGNORE (-1)
#define ERR_REPLACE (1)

static PyObject *htmlentities;


static PyObject *
resolve_entity(Py_UNICODE *source, Py_ssize_t length, int herror,
               PyObject *entities)
{
    PyObject *key, *value;
    Py_UNICODE *sentinel = source + length;
    Py_ssize_t elength;
    char *target;

    /* Check entity dict */
    if (!(source < sentinel) || *source != U('#')) {
        if (!(key = PyUnicode_FromUnicode(source, length)))
            return NULL;
        value = PyObject_GetItem(entities, key);
        Py_DECREF(key);
        if (value)
            return value;
        if (!PyErr_ExceptionMatches(PyExc_KeyError))
            return NULL;
        PyErr_Clear();
    }
    /* Check numeric references */
    else {
        Py_UNICODE *nsource = source + 1;
        Py_ssize_t nlength = length - 1;
        PyObject *base;
        long ordinal;

        if (nsource < sentinel) {
            if (*nsource == U('x') || *nsource == U('X')) {
                base = PyInt_FromLong(16);
                ++nsource;
                --nlength;
            }
            else {
                base = PyInt_FromLong(10);
            }
            if (!base)
                return NULL;
            if (!(key = PyUnicode_FromUnicode(nsource, nlength))) {
                Py_DECREF(base);
                return NULL;
            }
            value = PyObject_CallFunction((PyObject *)&PyInt_Type, "(OO)",
                                          key, base);
            Py_DECREF(key);
            Py_DECREF(base);
            if (!value) {
                if (!PyErr_ExceptionMatches(PyExc_ValueError))
                    return NULL;
                PyErr_Clear();
            }
            else {
                ordinal = PyInt_AsLong(value);
                if (PyErr_Occurred()) {
                    PyErr_Clear();
                }
                Py_DECREF(value);
                if (ordinal >= 0 && ordinal <= 0x10ffff) {
                    if (!(value = PyUnicode_FromOrdinal((int)ordinal))) {
                        if (!PyErr_ExceptionMatches(PyExc_ValueError))
                            return NULL;
                    }
                    else {
                        return value;
                    }
                }
            }
        }
    }

    switch (herror) {
    case ERR_IGNORE:
        /* assumes & before and ; after */
        return PyUnicode_FromUnicode(source - 1, length + 2);

    case ERR_REPLACE:
        if (!(value = PyUnicode_FromUnicode(NULL, 1)))
            return NULL;
        (PyUnicode_AS_UNICODE(value))[0] = REPLCHAR;
        return value;

    default: /* strict */
        /* assumes & before and ; after */
        if (!(value = PyUnicode_FromUnicode(source - 1, length + 2)))
            return NULL;
        key = PyObject_Repr(value);
        Py_DECREF(value);
        if (!key)
            return NULL;

#define PART "Unresolved entity "
        if ((elength = PyString_Size(key)) == -1) {
            Py_DECREF(key);
            return NULL;
        }
        elength += sizeof(PART) - 1;
        if (!(value = PyString_FromStringAndSize(NULL, elength))) {
            Py_DECREF(key);
            return NULL;
        }
        target = PyString_AS_STRING(value);
        (void)memcpy(target, PART, sizeof(PART) - 1);
        target += sizeof(PART) - 1;
        (void)memcpy(target, PyString_AS_STRING(key),
                     PyString_GET_SIZE(key));
        Py_DECREF(key);
        PyErr_SetObject(PyExc_ValueError, value);
        Py_DECREF(value);
        return NULL;
    }
}

static int
replace_entity(Py_UNICODE **source_, Py_UNICODE **target_,
               Py_UNICODE *sentinel, Py_UNICODE *tsentinel, int herror,
               PyObject *entities)
{
    Py_UNICODE *source = *source_, *target = *target_, *uvalue, *svalue;
    PyObject *value;

    while (source < sentinel && target < tsentinel) {
        switch (*source++) {
        case U(';'):
            /* Possible entity found */
            value = resolve_entity(*source_,
                                   (Py_ssize_t)(source - *source_ - 1),
                                   herror,
                                   entities);
            if (!value)
                return -1;
            uvalue = PyUnicode_AS_UNICODE(value);
            svalue = uvalue + PyUnicode_GET_SIZE(value);
            while (uvalue < svalue && target < tsentinel)
                *target++ = *uvalue++;
            if (!(uvalue < svalue))
                *source_ = source;
            *target_ = target;
            Py_DECREF(value);
            return 0;

        case U('&'):
        case U(' '):
        case U('\r'):
        case U('\n'):
        case U('\t'):
        case U('\f'):
            goto no_entity;
        }
    }

    /* No entity, copy & literally and continue */
no_entity:
    if (target < tsentinel) {
        *target++ = U('&');
        *target_ = target;
    }
    return 0;
}


static Py_ssize_t
decode_buffer(Py_UNICODE *target, Py_ssize_t target_length,
              Py_UNICODE *source, Py_ssize_t source_length,
              PyObject *entities, int herror)
{
    Py_UNICODE *sentinel, *tsentinel, *tstart;
    Py_UNICODE c;

    sentinel = source + source_length;
    tstart = target;
    tsentinel = target + target_length;

    while (source < sentinel && target < tsentinel) {
        if ((c = *source++) != U('&')) {
            *target++ = c;
            continue;
        }
        if (replace_entity(&source, &target, sentinel, tsentinel, herror,
                           entities) == -1)
            return -1;
    }

    return
        (Py_ssize_t)(target - tstart) + (Py_ssize_t)(sentinel - source);
}


/*
 * Public tdi_htmldecode function
 */
PyObject *
tdi_htmldecode(PyObject *value, PyObject *encoding, PyObject *errors,
               PyObject *entities, int quoted)
{
    PyObject *result;
    Py_UNICODE *source_buf;
    Py_ssize_t length, source_length, result_length;
    const char *errors_s, *encoding_s;
    int herror = ERR_STRICT;

    if (encoding) {
        if (!(encoding_s = PyString_AsString(encoding)))
            return NULL;
    }
    else {
        encoding_s = "latin-1";
    }

    if (errors) {
        if (!(errors_s = PyString_AsString(errors)))
            return NULL;
        if (!strcmp(errors_s, "ignore"))
            herror = ERR_IGNORE;
        else if (!strcmp(errors_s, "replace"))
            herror = ERR_REPLACE;
    }
    else {
        errors_s = "strict";
    }

    if (!entities)
        entities = htmlentities;

    if (!(PyUnicode_CheckExact(value) || PyUnicode_Check(value))) {
        PyObject *tmp;
        tmp = PyObject_Str(value);
        value = PyUnicode_FromEncodedObject(tmp, encoding_s, errors_s);
        Py_DECREF(tmp);
        if (!value)
            return NULL;
    }
    else {
        Py_INCREF(value);
    }

    /* Initialize buffers and call the decoder function */
    if ((source_length = PyUnicode_GetSize(value)) == -1)
        goto error;
    if (source_length == 0)
        return value;
    if (!(source_buf = PyUnicode_AsUnicode(value)))
        goto error;
    if (quoted) {
        if (*source_buf == U('"') || *source_buf == U('\'')) {
            if (source_length <= 2) {
                Py_DECREF(value);
                return PyUnicode_DecodeASCII("", 0, "strict");
            }
            ++source_buf;
            source_length -= 2;
        }
    }
    result_length = source_length;
    if (!(result = PyUnicode_FromUnicode(NULL, result_length)))
        goto error;

    /* Loop until result buffer is big enough
     * Usually this will be at the first run. It may need to grow, if the
     * entities resolve to something bigger, though.
     */
    while(1) {
        length = decode_buffer(PyUnicode_AS_UNICODE(result), result_length,
                               source_buf, source_length,
                               entities, herror);
        if (length > result_length) {
            result_length = length;
            if (PyUnicode_Resize(&result, length) == -1) {
                Py_DECREF(result);
                goto error;
            }
            continue;
        }
        break;
    }
    Py_DECREF(value);

    if ((length < 0)
        || (length != result_length
            && PyUnicode_Resize(&result, length) == -1)) {
        Py_DECREF(result);
        return NULL;
    }

    return result;

error:
    Py_DECREF(value);
    return NULL;
}


/*
 * Globally initialize statics for tdi_htmldecode
 */
int
tdi_htmldecode_init(void)
{
    /* Load html entities from module */
    if (!htmlentities) {
        PyObject *mod, *ent;

        if (!(mod = PyImport_ImportModule("tdi._htmlentities")))
            return -1;
        ent = PyObject_GetAttrString(mod, "htmlentities");
        Py_DECREF(mod);
        if (!ent)
            return -1;
        htmlentities = PyObject_CallFunction((PyObject *)&PyDict_Type,
                                             "(O)", ent);
        Py_DECREF(ent);
        if (!htmlentities)
            return -1;
    }

    return 0;
}
