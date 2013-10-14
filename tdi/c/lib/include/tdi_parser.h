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

#ifndef TDI_PARSER_H
#define TDI_PARSER_H

#include "cext.h"

typedef enum {
    TDI_PARSER_EVENT_TEXT,
    TDI_PARSER_EVENT_STARTTAG,
    TDI_PARSER_EVENT_ENDTAG,
    TDI_PARSER_EVENT_COMMENT,
    TDI_PARSER_EVENT_MSECTION,
    TDI_PARSER_EVENT_DECL,
    TDI_PARSER_EVENT_PI,
    TDI_PARSER_EVENT_ESCAPE
} tdi_parser_event_type;

typedef enum {
    TDI_PARSER_ERR_ENV = 1, /* error from environment */
    TDI_PARSER_ERR_LEXER_EOF,
    TDI_PARSER_ERR_LEXER_FINAL
} tdi_parser_error;

typedef struct tdi_parser_event {
    tdi_parser_event_type type;
    union {
        struct {
            PyObject *data;
        } text;

        struct {
            PyObject *data;
            PyObject *name;
            PyObject *attr;
            int closed;
        } starttag;

        struct {
            PyObject *data;
            PyObject *name;
        } endtag;

        struct {
            PyObject *data;
        } comment;

        struct {
            PyObject *data;
            PyObject *name;
            PyObject *value;
        } msection;

        struct {
            PyObject *data;
            PyObject *name;
            PyObject *value;
        } decl;

        struct {
            PyObject *data;
        } pi;

        struct {
            PyObject *data;
            PyObject *escaped;
        } escape;
    } info;
} tdi_parser_event;

/*
 * Function type used to pass back parser events
 */
typedef int (tdi_parser_callback)(tdi_parser_event *, void *);


#endif
