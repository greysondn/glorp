from .token import (
    Token,
    TokenType,
)

class Lexer:
    def __init__(self):
        self.source:str = ""
        self.position:int = 0
        self.line:int = 1
        self.column:int = 1
        self.indent_stack:list[int] = [0]
        self.current_indent:int = 0
        self.pending_newline:bool = False
        self.stream:list[Token] = []
    
    @property
    def current_symbol(self) -> str:
        return self.source[self.position]
    
    def _reset(self):
        """Reset instance vars to initial values"""
        self.source = ""
        self.position = 0
        self.line = 1
        self.column = 1
        self.indent_stack = [0]
        self.current_indent = 0
        self.pending_newline = False
        self.stream = []
    
    def _advance(self) -> None:
        """Advance the file pointer one character"""
        
        # do we even still have a space to go?
        if (self.position < len(self.source)):
            if (self.current_symbol == "\n"):
                # newline
                self.line += 1
                self.column = 1
            else:
                # non-newline
                self.column += 1

        # regardless of all that, the position moved forwards one character
        # (yes, we want this to go over by one, it's checked elsewhere)
        self.position += 1
    
    def _handle_newline(self) -> None:
        # enforce whitelist for when to call
        if (self.current_symbol != "\n"):
            raise RuntimeError("Asked to handle newline on non-newline symbol!")
        else:
            # okay, we're good, now handle it
            
            # handle a pending newline from something or another if it exists
            # handle a normal newline if it doesn't
            if (self.pending_newline):
                self.pending_newline = False
            else:
                self.stream.append(Token(TokenType.NEWLINE, value="\n", line=self.line, column=self.column))
            
            # actually advance the symbol pointer past the newline now
            self._advance()
            self.current_indent = 0
            
            # now we try to ingest whitespace characters
            keep_eating_whitespace:bool = True
            
            while (keep_eating_whitespace):
                # check for illegal tab
                if (self.current_symbol == "\t"):
                    raise SyntaxError(f"Tabs are not allowed! See: ln {self.line}, col {self.column}")
                # okay, check to make sure it's not another newline, though?
                elif (self.current_symbol == "\n"):
                    self.pending_newline = True
                    self._handle_newline()
                # okay, but is it whitespace tho?
                elif (self.current_symbol.isspace()):
                    self.current_indent += 1
                    self._advance()
                else:
                    # reached the end of the line
                    keep_eating_whitespace = False
                    
                    # figure out the indent state
                    
                    # further in is easy
                    if (self.current_indent > self.indent_stack[-1]):
                        self.stream.append(Token(TokenType.INDENT, value=str(self.current_indent), line=self.line, column=1))
                        self.indent_stack.append(self.current_indent)
                    # less in is hard
                    if (self.current_indent < self.indent_stack[-1]):
                        # pop them off until we're not less any more
                        while self.current_indent < self.indent_stack[-1]:
                            self.indent_stack.pop()
                        
                        # and now two things are possible
                        # it can be equal - yay, a match!
                        if (self.current_indent == self.indent_stack[-1]):
                            self.stream.append(Token(TokenType.DEDENT, value=str(self.current_indent), line=self.line, column=1))
                        # or it's greater than
                        else:
                            raise ValueError(f"Dedent did not match any previous indent at line {self.line}!")
    
    def tokenize(self, source:str) -> list[Token]:
        # reset self
        self._reset()
        self.source = source
        
        # now start eating characters
        while (self.position < len(self.source)):
            # get current character
            char:str =  self.source[self.position]
            
            # handle newline and indent
            if (char == "\n"):
                self._handle_newline()
                
        # return stream
        return self.stream