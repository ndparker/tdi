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

#ifndef TDI_SOUP_PARSER_H
#define TDI_SOUP_PARSER_H

#include "tdi_parser.h"

typedef struct tdi_soup_parser tdi_soup_parser;

/*
 * nestable callback
 */
typedef int (tdi_soup_parser_nestable_callback)(void *, PyObject *,
                                                PyObject *);

typedef int (tdi_soup_parser_cdata_callback)(void *, PyObject *);

typedef int (tdi_soup_parser_empty_callback)(void *, PyObject *);

typedef PyObject * (tdi_soup_parser_normalize_callback)(void *, PyObject *);


/* API */
tdi_soup_parser *
tdi_soup_parser_new(tdi_parser_callback *cb,
                    void *cb_ctx,
                    tdi_soup_parser_nestable_callback *nestable,
                    void *nestable_ctx,
                    tdi_soup_parser_cdata_callback *cdata,
                    void *cdata_ctx,
                    tdi_soup_parser_empty_callback *empty,
                    void *empty_ctx,
                    tdi_soup_parser_normalize_callback *normalize,
                    void *normalize_ctx
);

void
tdi_soup_parser_del(tdi_soup_parser *);

#define TDI_SOUP_PARSER_CLEAR(parser) do {  \
    tdi_soup_parser *tmp__ = (parser);      \
    if (tmp__) {                            \
        (parser) = NULL;                    \
        tdi_soup_parser_del(tmp__);         \
    }                                       \
} while (0)


/*
 * Feed the parser some data
 */
int
tdi_soup_parser_feed(tdi_soup_parser *, PyObject *food);


/*
 * Finish the parser
 */
int
tdi_soup_parser_finalize(tdi_soup_parser *);


/*
 * Return the current lexer state as string
 */
const char *
tdi_soup_parser_lexer_state_get(tdi_soup_parser *);


/*
 * Return the last parser error
 */
tdi_parser_error
tdi_soup_parser_error_get(tdi_soup_parser *);


#endif
