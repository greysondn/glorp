from enum import Enum

from typing import (
    List,
    Optional,
)

class TokenType(Enum):
    # python keywords
    AND      = "and"            # future
    AS       = "as"             # forbidden
    ASSERT   = "assert"         # forbidden
    ASYNC    = "async"          # forbidden
    AWAIT    = "await"          # forbidden
    BREAK    = "break"          # forbidden
    CASE     = "case"           # forbidden
    CLASS    = "class"          # forbidden
    CONTINUE = "continue"       # forbidden
    DEF      = "def"            # future
    DEL      = "del"            # future
    ELIF     = "elif"           # future
    ELSE     = "else"           # future
    EXCEPT   = "except"         # forbidden
    FALSE    = "False"          # future
    FINALLY  = "finally"        # forbidden
    FOR      = "for"            # debatable, would require "in"
    FROM     = "from"           # forbidden
    GLOBAL   = "global"         # forbidden
    IF       = "if"             # future
    IMPORT   = "import"         # forbidden
    IN       = "in"             # forbidden
    IS       = "is"             # forbidden
    LAMBDA   = "lambda"         # forbidden
    MATCH    = "match"          # forbidden
    NONE     = "None"           # forbidden
    NONLOCAL = "nonlocal"       # forbidden
    NOT      = "not"            # future
    OR       = "or"             # future
    PASS     = "pass"           # future
    RAISE    = "raise"          # forbidden
    TRUE     = "True"           # future
    TRY      = "try"            # forbidden
    WHILE    = "while"          # future
    WITH     = "with"           # forbidden
    YIELD    = "yield"          # forbidden
    
    # types proper - still python, though
    IDENTIFIER = "identifier"
    LPAREN     = "("
    RPAREN     = ")"
    COLON      = ":"
    INDENT     = "indent"
    DEDENT     = "dedent"
    EOF        = "eof"
    
    # there are more planned, this is all for now though