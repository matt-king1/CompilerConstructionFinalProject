from ast import *
import ast
from unique import Uniqueify
from heap import Heapify
from explicate import InjectFrom, TypeError, MultiNode, Let

class IsFunc(AST):
    def __init__(self, obj):
        self.obj = obj
        self._fields = ['obj']

    def __repr__(self):
        return 'is_funcion({})'.format(self.obj)

class Closeify(NodeTransformer):
    def __init__(self, freePerFunc, heapified):
        self.free = freePerFunc
        self.funcCount = 0
        self.funcMapping = {}
        self.scope = None
        self.tmpCtr = 0
        self.heapified = heapified
        # print('heap ' + str(self.heapified))

    def visit_FunctionDef(self, node):
        preScope = self.scope        
        self.scope = node.name
        self.generic_visit(node)
        self.scope = preScope
        name = node.name
        node.args.args = [arg('free_vars_' + str(self.funcCount))] + node.args.args
        node.name = 'closure_func_' + str(self.funcCount)
        # print('funcName: ' + name)

        self.funcMapping['_' + name] = node.name

        
        closedVars = []
        for i, var in enumerate(self.free[name]):
            assignNode = Assign([Name(var, Store())], Subscript(Name('free_vars_' + str(self.funcCount), Load()) ,Constant(i), Load()))
            closedVars.append(assignNode)
        
        node.body = closedVars + node.body
        assignNode = Name(name, Store())
        if name in self.heapified:
            assignNode.cts = Load()
            assignNode = Subscript(assignNode, Constant(0), Store())
        mn = MultiNode([node, Assign([assignNode], InjectFrom('big',Call(Name('create_closure', Load()), [Name(node.name, Load()), List([Name(free, Load()) for free in self.free[name]], Load())], [])))])
        # for child in mn.nodes:
        #     fix_missing_locations(child)
        #     print(unparse(child))
        self.funcMapping[name] = node.name
        self.funcCount += 1
        return mn
    
    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, Name) and node.func.id in ['print', 'eval', 'input', 'int']:
            return node
        
        temp = Name('tmp' + str(self.tmpCtr), Store())
        tempRead = Name('tmp' + str(self.tmpCtr), Load())
        self.tmpCtr += 1
        funcCheck = InjectFrom('int', IsFunc(temp))
        funcMapped = Let(temp, node.func, IfExp(funcCheck, temp, TypeError('tried to call non function')))
        temp.dont_rename = True
        tempRead.dont_rename = True
        innerCall = Call(Name('get_free_vars', Load()), [funcMapped], [])
        outerCall = Call(Call(Name('get_fun_ptr', Load()), [tempRead], []), [innerCall] + node.args, [])
        return outerCall



# class addParents(ast.NodeVisitor):
#     def generic_visit(self, node):
#         if isinstance(node, ast.While):
#             node._fields = (*node._fields, 'testtree')
#         for field, value in iter_fields(node):
#             if isinstance(value, list):
#                 for item in value:
#                     if isinstance(item, AST):
#                         item.parent = node
#                         self.visit(item)
#             elif isinstance(value, AST):
#                 value.parent=node
#                 self.visit(value)

# test = '''\
# def prod(a, b):
#     return 0 if b == 0 else a + prod(a, b + -1)

# def square(n):
#     return prod(n, n)

# print(square(eval(input())))
# '''

# p = addParents()
# u = Uniqueify()
# tree = parse(test)
# p.visit(tree)
# u.visit(tree)
# p.visit(tree)
# fix_missing_locations(tree)
# print(u.free)
# h = Heapify(u.free)
# h.visit(tree)
# p.visit(tree)
# fix_missing_locations(tree)
# # print(unparse(tree))
# c = Closeify(u.freePerFunc)
# c.visit(tree)
# fix_missing_locations(tree)
# print(unparse(tree))
# # print(dump(tree, indent=4))