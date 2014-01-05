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

#include "obj_avoid_gc.h"
#include "obj_attr.h"
#include "obj_encoder.h"
#include "obj_node.h"
#include "obj_soup_encoder.h"
#include "obj_text_encoder.h"


/* ---------------- BEGIN TDI_EncoderWrapperType DEFINITION ---------------- */

#ifndef TDI_AVOID_GC
static int
TDI_EncoderWrapperType_traverse(tdi_encoder_t *self, visitproc visit,
                                void *arg)
{
    Py_VISIT(self->encoder);
    Py_VISIT(self->encoding);
    Py_VISIT(self->starttag_method);
    Py_VISIT(self->endtag_method);
    Py_VISIT(self->name_method);
    Py_VISIT(self->content_method);
    Py_VISIT(self->attribute_method);
    Py_VISIT(self->encode_method);
    Py_VISIT(self->escape_method);

    return 0;
}
#endif

static int
TDI_EncoderWrapperType_clear(tdi_encoder_t *self)
{
    Py_CLEAR(self->encoder);
    Py_CLEAR(self->encoding);
    Py_CLEAR(self->starttag_method);
    Py_CLEAR(self->endtag_method);
    Py_CLEAR(self->name_method);
    Py_CLEAR(self->content_method);
    Py_CLEAR(self->attribute_method);
    Py_CLEAR(self->encode_method);
    Py_CLEAR(self->escape_method);

    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_EncoderWrapperType)

PyTypeObject TDI_EncoderWrapperType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".Encoder",                         /* tp_name */
    sizeof(tdi_encoder_t),                              /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_EncoderWrapperType_dealloc,         /* tp_dealloc */
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
    | TDI_IF_GC(Py_TPFLAGS_HAVE_GC),
    0,                                                  /* tp_doc */
    (traverseproc)TDI_IF_GC(TDI_EncoderWrapperType_traverse), /* tp_traverse */
    (inquiry)TDI_IF_GC(TDI_EncoderWrapperType_clear)    /* tp_clear */
};

/* ----------------- END TDI_EncoderWrapperType DEFINITION ----------------- */

/*
 * Create encoder object from alien encoder
 */
tdi_encoder_t *
tdi_encoder_wrapper_new(PyObject *encoder)
{
    tdi_encoder_t *self;

    if (!(self = GENERIC_ALLOC(&TDI_EncoderWrapperType)))
        return NULL;

    if (TDI_SoupEncoderType_CheckExact(encoder)) {
        tdi_soup_encoder_t *soupencoder = (tdi_soup_encoder_t *)encoder;
        Py_INCREF(soupencoder->encoding);
        self->encoding = soupencoder->encoding;
        Py_INCREF(encoder);
        self->encoder = encoder;
        self->starttag = tdi_soup_encode_starttag;
        self->endtag = tdi_soup_encode_endtag;
        self->name = tdi_soup_encode_name;
        self->content = tdi_soup_encode_content;
        self->attribute = tdi_soup_encode_attribute;
        self->encode = tdi_soup_encode_unicode;
        self->escape = tdi_soup_encode_escape;
    }
    else if (TDI_TextEncoderType_CheckExact(encoder)) {
        tdi_text_encoder_t *textencoder = (tdi_text_encoder_t *)encoder;
        Py_INCREF(textencoder->encoding);
        self->encoding = textencoder->encoding;
        Py_INCREF(encoder);
        self->encoder = encoder;
        self->starttag = tdi_text_encode_starttag;
        self->endtag = tdi_text_encode_endtag;
        self->name = tdi_text_encode_name;
        self->content = tdi_text_encode_content;
        self->attribute = tdi_text_encode_attribute;
        self->encode = tdi_text_encode_unicode;
        self->escape = tdi_text_encode_escape;
    }
    else {
        PyObject *tmp;

        Py_INCREF(encoder);
        self->encoder = encoder;
        if (!(tmp = PyObject_GetAttrString(encoder, "encoding")))
            goto error;
        self->encoding = PyObject_Str(tmp);
        Py_DECREF(tmp);
        if (!self->encoding)
            goto error;
        self->starttag_method = PyObject_GetAttrString(encoder, "starttag");
        if (!self->starttag_method)
            goto error;

        self->endtag_method = PyObject_GetAttrString(encoder, "endtag");
        if (!self->endtag_method)
            goto error;

        self->name_method = PyObject_GetAttrString(encoder, "name");
        if (!self->name_method)
            goto error;

        self->content_method = PyObject_GetAttrString(encoder, "content");
        if (!self->content_method)
            goto error;

        self->attribute_method = PyObject_GetAttrString(encoder, "attribute");
        if (!self->attribute_method)
            goto error;

        self->encode_method = PyObject_GetAttrString(encoder, "encode");
        if (!self->encode_method)
            goto error;

        self->escape_method = PyObject_GetAttrString(encoder, "escape");
        if (!self->escape_method)
            goto error;
    }

    return self;

error:
    Py_DECREF(self);
    return NULL;
}


PyObject *
tdi_encoder_starttag_wrapper(tdi_node_t *node)
{
    PyObject *attr, *attrlist, *tup;
    tdi_attr_t *item;
    Py_ssize_t j, length;
    int res;

    if (!(attr = PyDict_Values(node->attr)))
        return NULL;

    if (!(attrlist = PyList_New(0))) {
        Py_DECREF(attr);
        return NULL;
    }

    length = PyList_GET_SIZE(attr);
    for (j = 0; j < length; ++j) {
        item = (tdi_attr_t *)PyList_GET_ITEM(attr, j);
        if (!(tup = PyTuple_New(2))) {
            Py_DECREF(attrlist);
            Py_DECREF(attr);
            return NULL;
        }
        Py_INCREF(item->key);
        PyTuple_SET_ITEM(tup, 0, item->key);
        Py_INCREF(item->value);
        PyTuple_SET_ITEM(tup, 1, item->value);
        res = PyList_Append(attrlist, tup);
        Py_DECREF(tup);
        if (res == -1) {
            Py_DECREF(attrlist);
            Py_DECREF(attr);
            return NULL;
        }
    }
    Py_DECREF(attr);

    tup = PyObject_CallFunction(node->encoder->starttag_method, "(OOO)",
        node->tagname,
        attrlist,
        (node->flags & NODE_CLOSED)? Py_True: Py_False);
    Py_DECREF(attrlist);

    return tup;
}
