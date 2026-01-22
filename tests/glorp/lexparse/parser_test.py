from ... import context

lexparse = context.glorp.lexparse

Lexer = lexparse.lexer.Lexer

ast = lexparse.ast
Token = lexparse.token.Token
TokenType = lexparse.token.TokenType
Parser = lexparse.parser.Parser


def test_bare_minimum_parser():
    # build a src file
    src:str = ""
    src = src + "def main():" + "\n"
    src = src + "    init()"
    
    # lex it
    lexer:Lexer = Lexer()
    tokens = lexer.tokenize(src)
    
    # try to parse it
    parser:Parser = Parser()
    parser.parse(tokens)