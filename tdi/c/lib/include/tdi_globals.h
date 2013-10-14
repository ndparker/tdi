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

#ifndef TDI_GLOBALS_H
#define TDI_GLOBALS_H

#include "cext.h"

extern PyObject *tdi_g_rendermethod;   /* prefix of the render method */
extern PyObject *tdi_g_separatemethod; /* prefix of the separate method */
extern PyObject *tdi_g_empty;          /* empty string */
extern PyObject *tdi_g_newline;        /* newline */
extern PyObject *tdi_g_empty_tuple;    /* empty tuple */
extern PyObject *tdi_g_empty_dict;     /* empty dict */

/*
 * Init TDI globals
 */
int tdi_globals_init(void);

#endif
