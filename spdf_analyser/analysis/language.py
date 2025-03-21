from .. import *


# Definition of the language with its tokens or groups of lexicons (in order of priority)
# https://www.indexnine.com/naming-design-tokens/#:~:text=Token%20names%20should%20be%20given,overlap%20in%20terminology%20as%20possible.
SPDF_LANGUAGE: Dict[str, str] = {
    # MARGIN
    "MARGIN__HEADER": r"%SPDF-(\d+)\.(\d+)", # Higher priority
    "MARGIN__EOF": r"%%EOF",

    # STREAM_BLOCK
    "STREAM_BLOCK": r"stream[\s]([\s\S]*?)[\s]endstream",

    # REFERENCE
    "REFERENCE": r"(\d+)[\s](\d+)[\s]R",
    "XREF_ELEMENT": r"(\d{10})[\s](\d{5})[\s][fn]",

    #COMMENT
    "COMMENT": r"\%.*",

    #PUNCTUATOR
    "PUNCTUATOR__OPEN_ARRAY": r"\[",
    "PUNCTUATOR__CLOSE_ARRAY": r"\]",
    "PUNCTUATOR__OPEN_CONTENT": r"\<\<",
    "PUNCTUATOR__CLOSE_CONTENT": r"\>\>",

    #KEYWORD
    # "KEYWORD__R": r"R",
    # "KEYWORD__FN": r"f|n",
    "KEYWORD__OBJ": r"obj",
    "KEYWORD__ENDOBJ": r"endobj",
    "KEYWORD__TRAILER": r"trailer",
    "KEYWORD__XREF": r"xref",
    "KEYWORD__STARTXREF": r"startxref",
    "KEYWORD__BOOL": r"true|false",
    "KEYWORD__NULL": r"null",

    # LITERAL
    "LITERAL__FLOAT": r"((\+|\-)?(\d+)\.(\d+))",
    "LITERAL__INTEGER": r"((\+|\-)(\d+))",
    "LITERAL__UNSIGNED_INTEGER": r"(\d+)",
    "LITERAL__STRING": r"\(([^\)]*)\)",

    # NAME
    "NAME": r"/([A-Z][a-zA-Z0-9]*)", # Lower priority
}
SPDF_LANGUAGE_PATTERNS: Dict[str, Pattern[str]] = {key: compile(value) for key, value in SPDF_LANGUAGE.items()}

# Definition of the grammar with its production rules
SPDF_GRAMMAR: Tuple[Tuple[str, str]] = (
    ("START", "MARGIN__HEADER EXPRS EXPR__XREF EXPR__TRAILER MARGIN__EOF"), # Start production rule

    # EXPRESSIONS
    ("EXPRS", "EXPRS EXPR"),
    ("EXPRS", ""),
    ("EXPR", "EXPR__COMMENT"),
    ("EXPR", "EXPR__OBJ"),
    ("EXPR", ""),
    ("EXPR__COMMENT", "COMMENT"),
    ("EXPR__OBJ", "LITERAL__UNSIGNED_INTEGER LITERAL__UNSIGNED_INTEGER KEYWORD__OBJ STRUCT__CONTENT KEYWORD__ENDOBJ"),
    ("EXPR__OBJ", "LITERAL__UNSIGNED_INTEGER LITERAL__UNSIGNED_INTEGER KEYWORD__OBJ STRUCT__CONTENT STREAM_BLOCK KEYWORD__ENDOBJ"),
    ("EXPR__XREF", "KEYWORD__XREF LITERAL__UNSIGNED_INTEGER LITERAL__UNSIGNED_INTEGER STRUCT__XREF_ELEMENTS"),
    ("EXPR__TRAILER", "KEYWORD__TRAILER STRUCT__CONTENT KEYWORD__STARTXREF LITERAL__UNSIGNED_INTEGER"),

    # STRUCTURES
    ("STRUCT__CONTENT", "PUNCTUATOR__OPEN_CONTENT STRUCT__DICT_PAIRS PUNCTUATOR__CLOSE_CONTENT"),
    ("STRUCT__DICT_PAIRS", "STRUCT__DICT_PAIRS STRUCT__DICT_PAIR"),
    ("STRUCT__DICT_PAIRS", ""),
    ("STRUCT__DICT_PAIR", "NAME VALUE__DICT"),
    ("STRUCT__DICT_PAIR", ""),
    ("STRUCT__ARRAY", "PUNCTUATOR__OPEN_ARRAY STRUCT__ARRAY_ELEMENTS PUNCTUATOR__CLOSE_ARRAY"),
    ("STRUCT__ARRAY_ELEMENTS", "STRUCT__ARRAY_ELEMENTS STRUCT__ARRAY_ELEMENT"),
    ("STRUCT__ARRAY_ELEMENTS", ""),
    ("STRUCT__ARRAY_ELEMENT", "VALUE__ARRAY"),
    ("STRUCT__ARRAY_ELEMENT", ""),
    # ("STRUCT__REFERENCE", "LITERAL__UNSIGNED_INTEGER LITERAL__UNSIGNED_INTEGER KEYWORD__R"),
    ("STRUCT__XREF_ELEMENTS", "STRUCT__XREF_ELEMENTS STRUCT__XREF_ELEMENT"),
    ("STRUCT__XREF_ELEMENTS", ""),
    ("STRUCT__XREF_ELEMENT", "XREF_ELEMENT"), # ("STRUCT__XREF_ELEMENT", r"\"\d{10}\" \"\d{5}\" KEYWORD__FN"),
    ("STRUCT__XREF_ELEMENT", ""),

    # VALUES
    ("VALUE__DICT", "STRUCT__CONTENT"),
    ("VALUE__DICT", "STRUCT__ARRAY"),
    ("VALUE__DICT", "REFERENCE"), # ("VALUE__DICT", "STRUCT__REFERENCE"),
    ("VALUE__DICT", "KEYWORD__BOOL"),
    ("VALUE__DICT", "KEYWORD__NULL"),
    ("VALUE__DICT", "LITERAL__FLOAT"),
    ("VALUE__DICT", "LITERAL__INTEGER"),
    ("VALUE__DICT", "LITERAL__UNSIGNED_INTEGER"),
    ("VALUE__DICT", "LITERAL__STRING"),
    ("VALUE__DICT", "NAME"),
    ("VALUE__ARRAY", "STRUCT__CONTENT"),
    # ("VALUE__ARRAY", "STRUCT__ARRAY"),
    ("VALUE__ARRAY", "REFERENCE"), # ("VALUE__ARRAY", "STRUCT__REFERENCE"),
    ("VALUE__ARRAY", "KEYWORD__BOOL"),
    ("VALUE__ARRAY", "KEYWORD__NULL"),
    ("VALUE__ARRAY", "LITERAL__FLOAT"),
    ("VALUE__ARRAY", "LITERAL__INTEGER"),
    ("VALUE__ARRAY", "LITERAL__UNSIGNED_INTEGER"),
    ("VALUE__ARRAY", "LITERAL__STRING"),
    ("VALUE__ARRAY", "NAME"),
)