import ast
from ast import *

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

class Uniqueify(NodeTransformer):
    def __init__(self):
        self.ctrs = {}
        self.defs = []
        self.scope = []
        self.free = set() #indexed by function name
        self.totals = {} #indexed by function name
        self.writes = {} #indexed by function name
        self.currentScope = None
        self.freePerFunc = {}
        self.funcMap = {}
        self.progMap = {}

    def visit_Module(self, node):
        self.scope.append(set())
        self.generic_visit(node)
        node.body = self.defs + node.body
        self.scope.pop()
        return node

    def visit_Name(self, node):
        if isinstance(node.parent, Call) and node.parent.func == node and (node.id in ['print', 'eval', 'input', 'int']):
            return node
        cnt = self.ctrs.get(node.id, 0)
        isAssignTarget = isinstance(node.parent, ast.Assign) and node.parent.targets[0] == node
        if isAssignTarget:
            cnt = self.progMap.get(node.id, 0)
            # print(node.id, self.scope[-1])
            if node.id not in self.scope[-1]:
                cnt += 1
                self.progMap.update({node.id : cnt})
                self.ctrs.update({node.id: cnt})
                self.scope[-1].add(node.id)
            node.id = node.id + '_' + str(cnt)
        elif isinstance(node.parent, ast.Call) and node == node.parent.func:
            if node.id in self.progMap.keys():
                node.id = node.id + '_' +str(self.progMap[node.id])
            else:
                cnt += 1
                self.funcMap.update({node.id : node.id+ '_' + str(cnt)})
                self.progMap.update({node.id : cnt})
                self.ctrs.update({node.id: cnt})
                node.id = node.id + '_' + str(cnt)
            if self.currentScope != None:
                self.totals[self.currentScope].add(node.id)
            self.scope[-1].add(node.id)
        else:
            node.id = node.id + '_' + str(cnt)
            print(node.id, self.currentScope)
            if self.currentScope != None:
                self.totals[self.currentScope]
        if not (isinstance(node.parent, Call) and node.parent.func == node):
            if self.currentScope != None:
                self.totals[self.currentScope].add(node.id)
                if isinstance(node.ctx, Store):
                    self.writes[self.currentScope].add(node.id)
        return node

    def visit_arg(self, node):
        cnt = self.progMap.get(node.arg, 0)
        cnt += 1
        self.progMap.update({node.arg : cnt})
        self.ctrs.update({node.arg: cnt})
        node.arg = node.arg + '_' + str(cnt)
        self.scope[-1].add(node.arg)
        return node

    def visit_Assign(self, node):
        node.value = self.visit(node.value)
        node.targets[0] = self.visit(node.targets[0])
        return node

    def visit_Lambda(self, node):
        unifiedDefNode = FunctionDef('lambda', node.args, [Return(node.body)], [])
        self.visit(unifiedDefNode)
        nameReturn = Name(unifiedDefNode.name, Load())
        nameReturn.isFunc = True
        nameReturn.parent = node.parent
        if self.currentScope != None:
            self.totals[self.currentScope].add(nameReturn.id)
        return nameReturn

    def visit_FunctionDef(self, node):
        cnt = self.progMap.get(node.name, 0)
        if node.name not in self.progMap.keys():
            cnt += 1
            self.progMap.update({node.name : cnt})
            self.ctrs.update({node.name: cnt})
            self.funcMap.update({node.name : node.name + '_' + str(cnt)})
            node.name = node.name + '_' + str(cnt)
        else:
            node.name = node.name + '_' + str(self.progMap[node.name])
        preFuncMap = dict(self.funcMap)
        self.writes[node.name] = set()
        self.totals[node.name] = set()
        
        self.scope.append(set([arg.arg for arg in node.args.args]))
        preCnts = dict(self.ctrs)
        preScope = self.currentScope
        self.currentScope = node.name

        node.args.args = [self.visit(child) for child in node.args.args]
        for arg in node.args.args:
            self.writes[node.name].add(arg.arg)
        prePostArgsCnts = dict(self.ctrs)
        newBody = []
        for i in range(len(node.body)):
            if isinstance(node.body[i], FunctionDef) or isinstance(node.body[i], Lambda):
                for arg in node.body[i].args.args:
                    self.ctrs.update({arg.arg : self.ctrs.get(arg.arg, 0) + 1})
                self.visit(node.body[i])
            else:
                forwardCnts = dict(self.ctrs)
                self.ctrs = prePostArgsCnts
                newBody.append(self.visit(node.body[i]))
                self.ctrs = forwardCnts
        node.body = newBody
        # node.body = [x for x in [self.visit(child) for child in node.body] if x != None]

        self.scope.pop()
        self.currentScope = preScope
        self.ctrs = preCnts
        self.freePerFunc[node.name] = self.totals[node.name] - self.writes[node.name]
        self.free = self.free.union(self.freePerFunc[node.name])
        self.funcMap = preFuncMap

        self.defs.append(node)
        return None



test = '''\
def f():
    def f():
        def f():
            return lambda f: f
        return f
    return f

print((lambda x: f()()()(x))(eval(input())))
'''

p = addParents()
tree = ast.parse(test)
p.visit(tree)
u = Uniqueify()
u.visit(tree)
fix_missing_locations(tree)
# print(ast.dump(tree, indent=4))
print(u.free)
print(ast.unparse(tree))

# class FuncTrace:
#     def __init__(self):
#         self.count = -1
#         self.var_dict = {}
#         self.func_dict = {}

#     def __enter__(self):
#         self.count = self.count + 1
#         return self.count

#     def __exit__(self, *args):
#         self.count = self.count - 1
#         for k, v in self.var_dict.items():
#             if v == self.count + 1:
#                 self.var_dict[k] = self.count

#     def visit_FunctionDef(self, node):
#             with self.FuncTrace as ft:
#                 self.FuncTrace.func_dict[node.name] = ft
#                 node.name = "{}_{}".format(node.name, ft)
#                 for arg in node.args.args:
#                     self.FuncTrace.var_dict[arg.arg] = ft
#                     arg.arg = "{}_{}".format(arg.arg, ft)
#                 [self.visit(stmt) for stmt in node.body]
#             return node