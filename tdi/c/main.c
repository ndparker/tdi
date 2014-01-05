/*
 * Copyright 2006 - 2014
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
#include "tdi_exceptions.h"
#include "tdi_globals.h"

#include "htmldecode.h"
#include "obj_attr.h"
#include "obj_attribute_analyzer.h"
#include "obj_base_event_filter.h"
#include "obj_decoder.h"
#include "obj_encoder.h"
#include "obj_html_decoder.h"
#include "obj_iterate_iter.h"
#include "obj_model_adapters.h"
#include "obj_node.h"
#include "obj_raw_node.h"
#include "obj_render_iter.h"
#include "obj_repeat_iter.h"
#include "obj_repr_iter.h"
#include "obj_root_node.h"
#include "obj_soup_encoder.h"
#include "obj_soup_encoding_detect_filter.h"
#include "obj_soup_lexer.h"
#include "obj_soup_parser.h"
#include "obj_template_node.h"
#include "obj_text_decoder.h"
#include "obj_text_encoder.h"
#include "obj_xml_decoder.h"

EXT_INIT_FUNC;

/* ------------------------ BEGIN MODULE DEFINITION ------------------------ */

PyDoc_STRVAR(htmldecode__doc__,
"decode(value, encoding='latin-1', errors='strict', entities=None):\n\
\n\
Decode HTML encoded text\n\
\n\
:Parameters:\n\
  `value` : ``basestring``\n\
    HTML content to decode\n\
\n\
  `encoding` : ``str``\n\
    Unicode encoding to be applied before value is being processed\n\
    further. If value is already a unicode instance, the encoding is\n\
    ignored. If omitted, 'latin-1' is applied (because it can't fail\n\
    and maps bytes 1:1 to unicode codepoints).\n\
\n\
  `errors` : ``str``\n\
    Error handling, passed to .decode() and evaluated for entities.\n\
    If the entity name or character codepoint could not be found or\n\
    not be parsed then the error handler has the following semantics:\n\
\n\
    ``strict`` (or anything different from the other tokens below)\n\
        A ``ValueError`` is raised.\n\
\n\
    ``ignore``\n\
        The original entity is passed through\n\
\n\
    ``replace``\n\
        The character is replaced by the replacement character\n\
        (U+FFFD)\n\
\n\
  `entities` : ``dict``\n\
    Entity name mapping (unicode(name) -> unicode(value)). If\n\
    omitted or ``None``, the `HTML5 entity list`_ is applied.\n\
\n\
    .. _HTML5 entity list: http://www.w3.org/TR/html5/\n\
       syntax.html#named-character-references\n\
\n\
:Return: The decoded content\n\
:Rtype: ``unicode``");

static PyObject *
htmldecode(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *value, *encoding = NULL, *errors = NULL, *entities = NULL;
    static char *kwlist[] = {"value", "encoding", "errors", "entities", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|SSO", kwlist,
                                     &value, &encoding, &errors, &entities))
        return NULL;

    return tdi_htmldecode(value, encoding, errors, entities, 0);
}

EXT_METHODS = {
    {"htmldecode",
        (PyCFunction)htmldecode, METH_KEYWORDS,
        htmldecode__doc__},

    {NULL}  /* Sentinel */
};

PyDoc_STRVAR(EXT_DOCS_VAR,
"=======================================\n\
 C implementation of the tdi node tree\n\
=======================================\n\
\n\
C implementation of the tdi node tree.");

EXT_DEFINE(EXT_MODULE_NAME, EXT_METHODS_VAR, EXT_DOCS_VAR);

#define STORE_EXC(module, source, name) do {                           \
    if (!(TDI_E_##name) &&                                             \
        !((TDI_E_##name) = PyObject_GetAttrString((source), #name))) { \
        Py_DECREF(source);                                             \
        EXT_INIT_ERROR(module);                                        \
    }                                                                  \
} while (0)

EXT_INIT_FUNC {
    PyObject *m, *exceptions;

    if (tdi_globals_init() < 0)
        EXT_INIT_ERROR(NULL);

    if (tdi_htmldecode_init() < 0)
        EXT_INIT_ERROR(NULL);

    /* Create the module and populate stuff */
    if (!(m = EXT_CREATE(&EXT_DEFINE_VAR)))
        EXT_INIT_ERROR(NULL);

    EXT_ADD_UNICODE(m, "__author__", "Andr\xe9 Malo", "latin-1");
    EXT_ADD_STRING(m, "__docformat__", "restructuredtext en");

    EXT_INIT_TYPE(m, &TDI_AttributeAnalyzerType);
    EXT_INIT_TYPE(m, &TDI_AttrType);
    EXT_INIT_TYPE(m, &TDI_BaseEventFilterType);
    EXT_INIT_TYPE(m, &TDI_DecoderWrapperType);
    EXT_INIT_TYPE(m, &TDI_EncoderWrapperType);
    EXT_INIT_TYPE(m, &TDI_HTMLDecoderType);
    EXT_INIT_TYPE(m, &TDI_IterateIteratorType);
    EXT_INIT_TYPE(m, &TDI_NodeType);
    EXT_INIT_TYPE(m, &TDI_PreRenderMethodType);
    EXT_INIT_TYPE(m, &TDI_PreRenderWrapperType);
    EXT_INIT_TYPE(m, &TDI_RawNodeType);
    EXT_INIT_TYPE(m, &TDI_RenderAdapterType);
    EXT_INIT_TYPE(m, &TDI_RenderIteratorType);
    EXT_INIT_TYPE(m, &TDI_RepeatIteratorType);
    EXT_INIT_TYPE(m, &TDI_ReprIteratorType);
    EXT_INIT_TYPE(m, &TDI_RootNodeType);
    EXT_INIT_TYPE(m, &TDI_SoupEncoderType);
    EXT_INIT_TYPE(m, &TDI_SoupEncodingDetectFilterType);
    EXT_INIT_TYPE(m, &TDI_SoupLexerType);
    EXT_INIT_TYPE(m, &TDI_SoupParserType);
    EXT_INIT_TYPE(m, &TDI_TemplateNodeType);
    EXT_INIT_TYPE(m, &TDI_TextDecoderType);
    EXT_INIT_TYPE(m, &TDI_TextEncoderType);
    EXT_INIT_TYPE(m, &TDI_XMLDecoderType);

    /* add user concerning types */
    EXT_ADD_TYPE(m, "AttributeAnalyzer", &TDI_AttributeAnalyzerType);
    EXT_ADD_TYPE(m, "BaseEventFilter", &TDI_BaseEventFilterType);
    EXT_ADD_TYPE(m, "HTMLDecoder", &TDI_HTMLDecoderType);
    EXT_ADD_TYPE(m, "Node", &TDI_NodeType);
    EXT_ADD_TYPE(m, "PreRenderWrapper", &TDI_PreRenderWrapperType);
    EXT_ADD_TYPE(m, "RawNode", &TDI_RawNodeType);
    EXT_ADD_TYPE(m, "RenderAdapter", &TDI_RenderAdapterType);
    EXT_ADD_TYPE(m, "Root", &TDI_RootNodeType);
    EXT_ADD_TYPE(m, "SoupEncoder", &TDI_SoupEncoderType);
    EXT_ADD_TYPE(m, "SoupEncodingDetectFilter",
        &TDI_SoupEncodingDetectFilterType);
    EXT_ADD_TYPE(m, "SoupLexer", &TDI_SoupLexerType);
    EXT_ADD_TYPE(m, "SoupParser", &TDI_SoupParserType);
    EXT_ADD_TYPE(m, "TemplateNode", &TDI_TemplateNodeType);
    EXT_ADD_TYPE(m, "TextDecoder", &TDI_TextDecoderType);
    EXT_ADD_TYPE(m, "TextEncoder", &TDI_TextEncoderType);
    EXT_ADD_TYPE(m, "XMLDecoder", &TDI_XMLDecoderType);

    /* We inherit our exceptions and warnings from the package */
    if (!(exceptions = PyImport_ImportModule("tdi._exceptions")))
        EXT_INIT_ERROR(m);

    /* memorize exceptions and warnings */
    STORE_EXC(m, exceptions, LexerEOFError);
    STORE_EXC(m, exceptions, LexerFinalizedError);
    STORE_EXC(m, exceptions, ModelError);
    STORE_EXC(m, exceptions, ModelMissingError);
    STORE_EXC(m, exceptions, NodeNotFoundError);
    STORE_EXC(m, exceptions, NodeTreeError);
    STORE_EXC(m, exceptions, NodeWarning);
    STORE_EXC(m, exceptions, TemplateAttributeEmptyError);
    STORE_EXC(m, exceptions, TemplateAttributeError);
    STORE_EXC(m, exceptions, TemplateEncodingError);
    Py_DECREF(exceptions);

    EXT_INIT_RETURN(m);
}

/* ------------------------- END MODULE DEFINITION ------------------------- */
