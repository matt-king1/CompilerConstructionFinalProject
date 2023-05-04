import ast
from ast import *
from unique import Uniqueify

class Heapify(NodeTransformer):
    def __init__(self, frees, freePerFunc):
        self.frees = frees
        self.heapified = set()
        self.additons = []
        self.freePerFunc = freePerFunc
        self.scope = None

    def visit_Module(self, node):
        self.generic_visit(node)
        for addition in self.additons:
            addition[0].body = addition[1] + addition[0].body
        freeToTop = []
        for i, free in enumerate(self.frees):
            assignNode = Assign([Name(free, Store())], List([Constant(0)], Load()))
            assignNode.lineno = i
            freeToTop.append(assignNode)
        node.body = freeToTop + node.body

    def visit_Name(self, node):
        if node.id in self.frees:
            if self.scope != None:
                self.freePerFunc[self.scope].add(node.id)
            return Subscript(node, Constant(0), node.ctx)
        return node

    def visit_arg(self, node):
        if node.arg in self.frees:
            parentDef = node.parent.parent
            self.additons.append([parentDef, [Assign([Subscript(Name(node.arg, Load()), Constant(0), Store())], List([Name(node.arg, Load())], Load()))]])
            self.heapified.add(node.arg)
        return node

    def visit_Assign(self, node):
        target = node.targets[0]
        # if isinstance(target, Name) and (target.id in self.frees) and not (target.id in self.heapified):
        #     node.value = List([self.visit(node.value)], Load())
        #     self.heapified.add(target.id)
        # else:
        node.targets[0] = self.visit(target)
        node.value = self.visit(node.value)
        return node
    
    def visit_FunctionDef(self, node):
        preScope = self.scope
        self.scope = node.name
        self.generic_visit(node)
        self.scope = preScope
        return node


class addParents(ast.NodeVisitor):
    def generic_visit(self, node):
        if isinstance(node, ast.While):
            node._fields = (*node._fields, 'testtree')
        for field, value in iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, AST):
                        item.parent = node
                        self.visit(item)
            elif isinstance(value, AST):
                value.parent=node
                self.visit(value)

test = '''\
def prod(a, b):
    return 0 if b == 0 else a + prod(a, b + -1)

def square(n):
    return prod(n, n)

print(square(eval(input())))
'''

p = addParents()
u = Uniqueify()
tree = ast.parse(test)
p.visit(tree)
u.visit(tree)
p.visit(tree)
fix_missing_locations(tree)
print(u.free)
h = Heapify(u.free, u.freePerFunc)
h.visit(tree)
fix_missing_locations(tree)
print(ast.unparse(tree))