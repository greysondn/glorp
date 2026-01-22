from .token import (
    Token,
    TokenType,
)

from .ast import (
    AST,
    ASTFunctionCall,
    ASTFunctionDef,
    ASTNode,
    ASTNodeWithBody,
)

class Parser():
    def __init__(self):
        self.source:list[Token] = []
        self.position:int = 0
        self.ast:AST = AST()
    
    def _reset(self):
        self.source = []
        self.position = 0
        self.ast = AST()
    
    @property
    def current_token(self) -> Token:
        return self.source[self.position]
    
    def _advance(self) -> None:
        self.position += 1
    
    def _expect(self, type_:TokenType, value:str|None = None) -> None:
        # so we're just going to try to invalidate this, right?
        correct_token:bool = True
        
        # wrong type
        if (self.current_token.type != type_):
            correct_token = False
        
        # value
        if (value is not None):
            if (self.current_token.value != value):
                correct_token = False
        
        if (correct_token):
            self._advance()
        else:
            raise ValueError(f"Expected symbol of type [{type_.name}] with value [{value}] at {self.current_token.line}:{self.current_token.column}")
    
    def _handle_def(self) -> None:
        # set up function def
        swp:ASTFunctionDef = ASTFunctionDef()
        
        # okay, we expect the def to be where we're at, so ingest it
        self._expect(TokenType.DEF)
        
        # now the tricky wicket
        swp_token:Token = self.current_token
        self._expect(TokenType.IDENTIFIER)
        
        # that would leave us with the identifier if the expect didn't fail
        swp.name = swp_token.value
        
        # we don't do args, so we just expect three symbols and a newline
        # TODO: Do args, duh.
        self._expect(TokenType.LPAREN)
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.COLON)
        self._expect(TokenType.NEWLINE)
        
        # indent here, so we pull it into our function
        swp_token = self.current_token
        self._expect(TokenType.INDENT)
        swp.body_indent = int(swp_token.value)
        
        # still inside setup
        still_inside:bool = True
        
        while (still_inside):
            # and now we start expecting declarations that aren't top level.
            if (self.current_token.type == TokenType.IDENTIFIER):
                # we don't know if it's a function or a var yet
                # but
                # assume it's function because that's all we're doing for now
                # TODO: handle vars, classes, whatever here
                swp_inner:ASTFunctionCall = ASTFunctionCall()
                
                # we can just set the name and advance
                swp_inner.name = self.current_token.value
                self._expect(TokenType.IDENTIFIER)
                
                # no args, so we expect two symbols here I think?
                # TODO: Handle args
                self._expect(TokenType.LPAREN)
                self._expect(TokenType.RPAREN)
                
                # inject into body
                swp.add_node(swp_inner)
            elif (self.current_token.type == TokenType.DEDENT):
                # we need that to be the correct type to move on
                if (int(self.current_token.value) == swp.body_indent):
                    # escape!
                    self._expect(TokenType.DEDENT)
                    still_inside = False
            else:
                raise NotImplementedError("Unsupported Token!")

        # finally built this node, send it out
        self.ast.add_node(swp)
    
    def parse(self, source:list[Token]) -> AST:
        # reinit
        self._reset()
        self.source = source
        
        # start eating tokens
        while (self.position < len(self.source)):
            # def
            if (self.current_token.type == TokenType.DEF):
                self._handle_def()
            elif (self.current_token.type == TokenType.EOF):
                # we can just throw that away, reckon
                self._expect(TokenType.EOF)
            
            # advance?
            self._advance()
        
        # return
        return self.ast