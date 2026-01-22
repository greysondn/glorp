from ... import context

lexparse = context.glorp.lexparse

Lexer = lexparse.lexer.Lexer

Token = lexparse.token.Token
TokenType = lexparse.token.TokenType


def test_bare_minimum_lexer():
    # build a src file
    src:str = ""
    src = src + "def main():" + "\n"
    src = src + "    init()"
    
    # build the expected token list
    expected:list[Token] = []
    expected.append(Token(TokenType.DEF, "def"))
    expected.append(Token(TokenType.IDENTIFIER, "main"))
    expected.append(Token(TokenType.LPAREN, "("))
    expected.append(Token(TokenType.RPAREN, ")"))
    expected.append(Token(TokenType.COLON, ":"))
    expected.append(Token(TokenType.NEWLINE, "\n"))
    expected.append(Token(TokenType.INDENT, "4"))
    expected.append(Token(TokenType.IDENTIFIER, "init"))
    expected.append(Token(TokenType.LPAREN, "("))
    expected.append(Token(TokenType.RPAREN, ")"))
    expected.append(Token(TokenType.DEDENT, "4"))
    expected.append(Token(TokenType.EOF, "EOF"))
    
    # try to lex it
    lexer:Lexer = Lexer()
    res = lexer.tokenize(src)
    
    # compare against expected
    for i in range(len(res)):
        assert (res[i].type == expected[i].type)
        assert (res[i].value == expected[i].value)
    