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

#ifndef TDI_OBJ_SOUP_ENCODER_H
#define TDI_OBJ_SOUP_ENCODER_H

#include "cext.h"
#include "tdi.h"

/*
 * Object structure for SoupEncoderType
 */
typedef struct {
    PyObject_HEAD
    PyObject *weakreflist;

    PyObject *encoding;
} tdi_soup_encoder_t;

extern PyTypeObject TDI_SoupEncoderType;


#define TDI_SoupEncoderType_Check(op) \
    PyObject_TypeCheck(op, &TDI_SoupEncoderType)

#define TDI_SoupEncoderType_CheckExact(op) \
    ((op)->ob_type == &TDI_SoupEncoderType)


PyObject *
tdi_soup_encode_starttag(tdi_node_t *node);

PyObject *
tdi_soup_encode_endtag(tdi_node_t *node);

PyObject *
tdi_soup_encode_name(PyObject *name, PyObject *encoding);

PyObject *
tdi_soup_encode_content(PyObject *value, PyObject *encoding);

PyObject *
tdi_soup_encode_attribute(PyObject *value, PyObject *encoding);

PyObject *
tdi_soup_encode_unicode(PyObject *value, PyObject *encoding);

PyObject *
tdi_soup_encode_escape(PyObject *value);

#endif
