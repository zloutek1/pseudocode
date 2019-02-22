
class Generator:
    def __init__(self):
        pass

    def generate(self, ast):
        if type(ast) is not list:
            return ast
        if len(ast) == 2:
            return self.binOp(ast)
        if len(ast) == 1:
            return self.generate(ast[0])

    def binOp(self, ast):
        assert len(ast) == 2, "ast length != 2"
        left, right = ast

        print("LEFT", self.generate(left))
        print("RIGHT", self.generate(right))
