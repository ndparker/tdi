/*
 * Copyright 2010 - 2012
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

#ifndef TDI_OBJ_ENCODER_H
#define TDI_OBJ_ENCODER_H

#include "cext.h"
#include "tdi.h"

#include "obj_soup_encoder.h"


/*
 * Object structure for EncoderWrapperType
 */
struct tdi_encoder_t {
    PyObject_HEAD

    PyObject *encoding;
    PyObject *encoder;

    PyObject *(*starttag)(tdi_node_t *);
    PyObject *(*endtag)(tdi_node_t *);
    PyObject *(*name)(PyObject *, PyObject *);
    PyObject *(*content)(PyObject *, PyObject *);
    PyObject *(*attribute)(PyObject *, PyObject *);
    PyObject *(*encode)(PyObject *, PyObject *);
    PyObject *(*escape)(PyObject *);

    PyObject *starttag_method;
    PyObject *endtag_method;
    PyObject *name_method;
    PyObject *content_method;
    PyObject *attribute_method;
    PyObject *encode_method;
    PyObject *escape_method;
};

extern PyTypeObject TDI_EncoderWrapperType;


#define ENCODE_STARTTAG(node) ((node)->encoder->starttag \
    ? (node)->encoder->starttag(node)                    \
    : tdi_encoder_starttag_wrapper(node))

#define ENCODE_ENDTAG(node) ((node)->encoder->endtag               \
    ? (node)->encoder->endtag(node)                                \
    : PyObject_CallFunction((node)->encoder->endtag_method, "(O)", \
        (node)->tagname))

#define ENCODE_NAME(node, value) ((node)->encoder->name         \
    ? (node)->encoder->name((value), (node)->encoder->encoding) \
    : PyObject_CallFunction((node)->encoder->name_method, "(O)", (value)))

#define ENCODE_CONTENT(node, value) ((node)->encoder->content      \
    ? (node)->encoder->content((value), (node)->encoder->encoding) \
    : PyObject_CallFunction((node)->encoder->content_method, "(O)", (value)))

#define ENCODE_ATTRIBUTE(node, value) ((node)->encoder->attribute    \
    ? (node)->encoder->attribute((value), (node)->encoder->encoding) \
    : PyObject_CallFunction((node)->encoder->attribute_method, "(O)", (value)))

#define ENCODE_UNICODE(node, value) ((node)->encoder->encode    \
    ? (node)->encoder->encode((value), (node)->encoder->encoding) \
    : PyObject_CallFunction((node)->encoder->encode_method, "(O)", (value)))

#define ENCODE_ESCAPE(node, value) ((node)->encoder->escape    \
    ? (node)->encoder->escape(value) \
    : PyObject_CallFunction((node)->encoder->escape_method, "(O)", (value)))


tdi_encoder_t *
tdi_encoder_wrapper_new(PyObject *encoder);

PyObject *
tdi_encoder_starttag_wrapper(tdi_node_t *node);

#endif
