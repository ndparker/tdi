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

#include "obj_avoid_gc.h"
#include "obj_decoder.h"
#include "obj_html_decoder.h"
#include "obj_text_decoder.h"
#include "obj_xml_decoder.h"

/* ---------------- BEGIN TDI_DecoderWrapperType DEFINITION ---------------- */

#ifndef TDI_AVOID_GC
static int
TDI_DecoderWrapperType_traverse(tdi_decoder_t *self, visitproc visit,
                                void *arg)
{
    Py_VISIT(self->decoder);
    Py_VISIT(self->encoding);
    Py_VISIT(self->normalize_method);

    return 0;
}
#endif

static int
TDI_DecoderWrapperType_clear(tdi_decoder_t *self)
{
    Py_CLEAR(self->decoder);
    Py_CLEAR(self->encoding);
    Py_CLEAR(self->normalize_method);

    return 0;
}

DEFINE_GENERIC_DEALLOC(TDI_DecoderWrapperType)

PyTypeObject TDI_DecoderWrapperType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                  /* ob_size */
    EXT_MODULE_PATH ".Decoder",                         /* tp_name */
    sizeof(tdi_decoder_t),                              /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)TDI_DecoderWrapperType_dealloc,         /* tp_dealloc */
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
    (traverseproc)TDI_IF_GC(TDI_DecoderWrapperType_traverse), /* tp_traverse */
    (inquiry)TDI_IF_GC(TDI_DecoderWrapperType_clear)    /* tp_clear */
};

/* ----------------- END TDI_DecoderWrapperType DEFINITION ----------------- */

/*
 * Create decoder object from alien decoder
 */
tdi_decoder_t *
tdi_decoder_wrapper_new(PyObject *decoder)
{
    tdi_decoder_t *self;
    PyObject *tmp;

    if (!(self = GENERIC_ALLOC(&TDI_DecoderWrapperType)))
        return NULL;

    Py_INCREF(decoder);
    self->decoder = decoder;

    if (TDI_HTMLDecoderType_CheckExact(decoder)) {
        Py_INCREF((((tdi_html_decoder_t *)decoder)->encoding));
        self->encoding = ((tdi_html_decoder_t *)decoder)->encoding;
        self->normalize = tdi_html_decoder_normalize;
    }
    else if (TDI_XMLDecoderType_CheckExact(decoder)) {
        Py_INCREF((((tdi_xml_decoder_t *)decoder)->encoding));
        self->encoding = ((tdi_xml_decoder_t *)decoder)->encoding;
        self->normalize = tdi_xml_decoder_normalize;
    }
    else if (TDI_TextDecoderType_CheckExact(decoder)) {
        Py_INCREF((((tdi_text_decoder_t *)decoder)->encoding));
        self->encoding = ((tdi_text_decoder_t *)decoder)->encoding;
        self->normalize = tdi_text_decoder_normalize;
    }
    else {
        if (!(tmp = PyObject_GetAttrString(decoder, "encoding")))
            goto error;
        self->encoding = PyObject_Str(tmp);
        Py_DECREF(tmp);
        if (!self->encoding)
            goto error;

        self->normalize_method = PyObject_GetAttrString(decoder, "normalize");
        if (!self->normalize_method)
            goto error;
    }

    return self;

error:
    Py_DECREF(self);
    return NULL;
}
