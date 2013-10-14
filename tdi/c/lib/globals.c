/*
 * Copyright 2010 - 2013
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

#include "tdi_globals.h"


/*
 * Global objects (allocated once at module init time)
 */
PyObject *tdi_g_rendermethod;     /* prefix of the render model method */
PyObject *tdi_g_separatemethod;   /* prefix of the separate model method */
PyObject *tdi_g_empty;            /* empty string */
PyObject *tdi_g_newline;          /* newline */
PyObject *tdi_g_empty_tuple;      /* empty tuple */
PyObject *tdi_g_empty_dict;       /* empty dict */

/*
 * Exceptions and Warnings (imported and refcounted at module init time)
 */
PyObject *TDI_E_NodeTreeError;
PyObject *TDI_E_NodeNotFoundError;
PyObject *TDI_E_ModelError;
PyObject *TDI_E_ModelMissingError;
PyObject *TDI_E_TemplateEncodingError;
PyObject *TDI_E_LexerEOFError;
PyObject *TDI_E_LexerFinalizedError;
PyObject *TDI_E_TemplateAttributeError;
PyObject *TDI_E_TemplateAttributeEmptyError;

/* Warnings */
PyObject *TDI_E_NodeWarning;


#define INIT_PYSTRING(NAME, VALUE) do {                \
    if (!NAME && !(NAME = PyString_FromString(VALUE))) \
        return -1;                                     \
} while (0)

/*
 * Initialize global variables
 */
int
tdi_globals_init(void)
{
    INIT_PYSTRING(tdi_g_rendermethod, "render");
    INIT_PYSTRING(tdi_g_separatemethod, "separate");
    INIT_PYSTRING(tdi_g_empty, "");
    INIT_PYSTRING(tdi_g_newline, "\n");

    if (!tdi_g_empty_tuple && !(tdi_g_empty_tuple = PyTuple_New(0)))
        return -1;
    if (!tdi_g_empty_dict && !(tdi_g_empty_dict = PyDict_New()))
        return -1;

    return 0;
}
