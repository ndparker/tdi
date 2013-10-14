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

#ifndef TDI_SOUP_LEXER_H
#define TDI_SOUP_LEXER_H

#include "tdi_lexer.h"

typedef struct tdi_soup_lexer tdi_soup_lexer;

tdi_soup_lexer *
tdi_soup_lexer_new(tdi_lexer_callback *cb, void *cb_ctx,
                   int conditional_ie_comments);

/*
 * Function type used to normalize names for cdata endtags
 */
typedef PyObject * (tdi_soup_lexer_cdata_callback)(void *, PyObject *);

void
tdi_soup_lexer_del(tdi_soup_lexer *);

#define TDI_SOUP_LEXER_CLEAR(lexer) do {  \
    tdi_soup_lexer *tmp__ = (lexer);      \
    if (tmp__) {                          \
        (lexer) = NULL;                   \
        tdi_soup_lexer_del(tmp__);        \
    }                                     \
} while (0)


/*
 * Feed the lexer some data
 */
int
tdi_soup_lexer_feed(tdi_soup_lexer *, PyObject *food);


/*
 * Finish the lexer
 */
int
tdi_soup_lexer_finalize(tdi_soup_lexer *);


/*
 * Return the current lexer state as string
 */
const char *
tdi_soup_lexer_state_get(tdi_soup_lexer *);


/*
 * Set state to CDATA
 */
int
tdi_soup_lexer_state_cdata(tdi_soup_lexer *,
                           tdi_soup_lexer_cdata_callback *cb,
                           void *cb_ctx,
                           PyObject *name);


/*
 * Return the last lexer error
 */
tdi_lexer_error
tdi_soup_lexer_error_get(tdi_soup_lexer *);


#endif
