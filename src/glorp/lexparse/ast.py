class ASTNode:
    pass

class ASTNodeWithBody(ASTNode):
    def __init__(self):
        self.body:list[ASTNode] = []
    
    def add_node(self, node:ASTNode) -> None:
        self.body.append(node)
    
class AST(ASTNodeWithBody):
    def __init__(self):
        super().__init__()

class ASTFunctionCall(ASTNode):
    def __init__(self):
        super().__init__()
        
        self.name:str = "NAME_NOT_SET"

class ASTFunctionDef(ASTNodeWithBody):
    def __init__(self):
        super().__init__()
        
        self.name:str = "NAME_NOT_SET"
        
