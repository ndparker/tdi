/*
 * Copyright 2010
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

#ifndef TDI_EXCEPTIONS_H
#define TDI_EXCEPTIONS_H

#include "cext.h"

/*
 * Exceptions and Warnings (imported and refcounted at module init time)
 */
extern PyObject *TDI_E_NodeTreeError;
extern PyObject *TDI_E_NodeNotFoundError;
extern PyObject *TDI_E_ModelError;
extern PyObject *TDI_E_ModelMissingError;
extern PyObject *TDI_E_TemplateEncodingError;
extern PyObject *TDI_E_LexerEOFError;
extern PyObject *TDI_E_LexerFinalizedError;
extern PyObject *TDI_E_TemplateAttributeError;
extern PyObject *TDI_E_TemplateAttributeEmptyError;

/* Warnings */
extern PyObject *TDI_E_NodeWarning;

#endif
