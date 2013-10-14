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

#ifndef TDI_OBJ_DECODER_H
#define TDI_OBJ_DECODER_H

#include "cext.h"
#include "tdi.h"


/*
 * Object structure for DecoderWrapperType
 */
struct tdi_decoder_t {
    PyObject_HEAD

    PyObject *encoding;
    PyObject *decoder;

    PyObject *(*normalize)(PyObject *);

    PyObject *normalize_method;
};

extern PyTypeObject TDI_DecoderWrapperType;

#define DECODER_NORMALIZE(node, name) ((node)->decoder->normalize \
    ? (node)->decoder->normalize((name))                          \
    : PyObject_CallFunction((node)->decoder->normalize_method, "(O)", (name)))


tdi_decoder_t *
tdi_decoder_wrapper_new(PyObject *decoder);

#endif
