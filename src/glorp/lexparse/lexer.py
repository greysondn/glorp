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
    
    def _handle_identifier(self) -> None:
        # stash some helpful stuff
        start_pos:int = self.position
        start_column:int = self.column
         
        # find the end of the identifier
        keep_eating:bool = True
        while (self.position < len(self.source) and keep_eating):
            # clumsily eat potentially valid symbols
            if ((self.current_symbol.isidentifier()) or (self.current_symbol.isdigit())):
                 self._advance()
            else:
                keep_eating = False
            
        # should be there, so slice it out
        end_pos:int = self.position
        word:str = self.source[start_pos:end_pos]
        
        # is that an identifier?
        if (word.isidentifier()):
            # set up a swap object
            swp:Token = Token(TokenType.AND, value=word, line=self.line, column=start_column)
            
            # Okay. Now we do something a bit screwy to move forwards
            # if we call an invalid token type, it'll throw a ValueError so
            # we can just throw the token type, right?
            try:
                swp.type = TokenType(word)
            except ValueError:
                swp.type = TokenType.IDENTIFIER
            finally:
                # now, we check to see if we caught a type we don't want to
                # set, like ones that could still be an identifier
                _avoid_list:list[TokenType] = [
                    TokenType.DEDENT,
                    TokenType.EOF,
                    TokenType.INDENT,
                    TokenType.NEWLINE,
                ]
                
                if(swp.type in _avoid_list):
                    swp.type = TokenType.IDENTIFIER
                
                # we should be good to add this now
                self.stream.append(swp)
                
        else:
            raise SyntaxError(f"Unexpected symbol at line {self.line}, column {start_pos}")
    
    
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
                elif (self.current_symbol == " "):
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
                        while (self.current_indent < self.indent_stack[-1]):
                            self.indent_stack.pop()
                        
                        # and now two things are possible
                        # it can be equal - yay, a match!
                        if (self.current_indent == self.indent_stack[-1]):
                            self.stream.append(Token(TokenType.DEDENT, value=str(self.current_indent), line=self.line, column=1))
                        # or it's greater than
                        else:
                            raise ValueError(f"Dedent did not match any previous indent at line {self.line}!")
    
    def _skip_whitespace(self) -> None:
        while (self.current_symbol == " "):
            self._advance()
    
    def tokenize(self, source:str) -> list[Token]:
        # reset self
        self._reset()
        self.source = source
        
        # now start eating characters
        while (self.position < len(self.source)):
            # handle newline and indent/dedent
            if (self.current_symbol == "\n"):
                self._handle_newline()
            
            # eat whitespace for days
            self._skip_whitespace()
            
            # handle symbol: "("
            if (self.current_symbol == "("):
                self.stream.append(Token(TokenType.LPAREN, value="(", line=self.line, column=self.column))
                self._advance()
            # handle symbol: ")"
            elif (self.current_symbol == ")"):
                self.stream.append(Token(TokenType.RPAREN, value=")", line=self.line, column=self.column))
                self._advance()
            # handle symbol: ":"
            elif(self.current_symbol == ":"):
                self.stream.append(Token(TokenType.COLON, value=":", line=self.line, column=self.column))
                self._advance()
            # handle keywords and identifiers, right?
            elif ((self.current_symbol.isalpha()) or (self.current_symbol == "_")):
                self._handle_identifier()
            else:
                raise SyntaxError(f"Unexpected character {self.current_symbol} at line {self.line}, column {self.column}")
        
        # end of file
        
        # staple dedents so stuff is easier later
        while (len(self.indent_stack) > 1):
            self.stream.append(Token(TokenType.DEDENT, value=str(self.indent_stack[-1]), line=self.line, column=self.column))
            self.indent_stack.pop()
        
        # staple end of file, we had to have reached it
        self.stream.append(Token(TokenType.EOF, value="EOF", line=self.line, column=self.column))
        
        # return stream
        return self.stream
