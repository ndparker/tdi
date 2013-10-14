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

#ifndef TDI_OBJ_XML_DECODER_H
#define TDI_OBJ_XML_DECODER_H

#include "cext.h"
#include "tdi.h"

/*
 * Object structure for XMLDecoderType
 */
typedef struct {
    PyObject_HEAD
    PyObject *weakreflist;

    PyObject *encoding;
} tdi_xml_decoder_t;

extern PyTypeObject TDI_XMLDecoderType;


#define TDI_XMLDecoderType_Check(op) \
    PyObject_TypeCheck(op, &TDI_XMLDecoderType)

#define TDI_XMLDecoderType_CheckExact(op) \
    ((op)->ob_type == &TDI_XMLDecoderType)


PyObject *
tdi_xml_decoder_normalize(PyObject *);

#endif
