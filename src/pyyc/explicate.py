import ast
from ast import *

class MultiNode(AST):
    def __init__(self, nodes):
        self.nodes = nodes
        self._fields = ['nodes']

    def __repr__(self):
        # ret = ''
        return "\n".join([repr(node) for node in self.nodes])
        # for node in self.nodes:
        #     ret += node.__repr__() + '\n'
        # return ret

class String(AST):
    def __init__(self, s):
        self.string = s
        self._fields = ['string']
    
    def __repr__(self):
        return 'string({})'.format(self.string)

class InjectFrom(AST):
    def __init__(self, type, arg):
        self.type = type
        self.arg = arg
        self._fields = ['type', 'arg']

    def __repr__(self):
        return 'inject_{}({})'.format(self.type, self.arg)
    
class ProjectTo(AST):
    def __init__(self, type, arg):
        self.type = type
        self.arg = arg
        self._fields = ['type', 'arg']

    def __repr__(self):
        return 'project_{}({})'.format(self.type, self.arg)
    
class IsInt(AST):
    def __init__(self, obj):
        self.obj = obj
        self._fields = ['obj']

    def __repr__(self):
        return 'is_int({})'.format(self.obj)
    
class IsBool(AST):
    def __init__(self, obj):
        self.obj = obj
        self._fields = ['obj']

    def __repr__(self):
        return 'is_bool({})'.format(self.obj)
    
class IsBig(AST):
    def __init__(self, obj):
        self.obj = obj
        self._fields = ['obj']

    def __repr__(self):
        return 'is_big({})'.format(self.obj)
    
class IsString(AST):
    def __init__(self, obj):
        self.obj = obj
        self._fields = ['obj']

    def __repr__(self):
        return 'is_string({})'.format(self.obj)
    
class Let(AST):
    def __init__(self, var, rhs, body):
        self.var = var
        self.rhs = rhs
        self.body = body
        self._fields = ['var', 'rhs', 'body']

    def __repr__(self):
        return 'let {} = {} in {}'.format(self.var, self.rhs, self.body)

class TypeError(AST):
    def __init__(self, msg):
        self.msg = msg
        self._fields = ['msg']

    def __repr__(self):
        return 'TypeError: {}'.format(self.msg)

class Explicator(NodeTransformer):
    def __init__(self, tmpCtr):
        # self.newTree = newTree
        # self.base = self.newTree.body
        self.tmpCtr = tmpCtr

    def visit_Name(self, node):
        if hasattr(node, 'visited') or hasattr(node, 'dont_rename'):
            return node
        if isinstance(node.parent, ast.Call) and (node.parent.func == node):
            return node
        if isinstance(node.parent, ast.Call) and isinstance(node.parent.func, Name) and node.parent.func.id == 'create_closure' and node.parent.args[0] == node:
            return node
        newNode = ast.Name("_" + node.id, node.ctx)
        newNode.parent = node.parent
        newNode.visited = True
        return newNode

    def visit_arg(self, node):
        newNode = ast.arg("_" + node.arg)
        newNode.parent = node.parent
        return newNode

    def visit_Constant(self, node):
        if hasattr(node, 'visited'):
            # print('visited')
            return node
        node.visited = True
        if isinstance(node.value, bool):
            node.value = int(node.value)
            return InjectFrom('bool', node)

        if isinstance(node.value, str):
            return String([InjectFrom('int', Constant(ord(val))) for val in node.value])
            
        return InjectFrom('int', node)

    def visit_BinOp(self, node):
        ltemp = Name('tmp' + str(self.tmpCtr), Store())
        self.tmpCtr += 1
        rtemp = Name('tmp' + str(self.tmpCtr), Store())
        self.tmpCtr += 1
        ltemp_big_check = InjectFrom('int', IsBig(ltemp))
        rtemp_big_check = InjectFrom('int', IsBig(rtemp))
        ltemp_int_check = InjectFrom('int', IsInt(ltemp))
        rtemp_int_check = InjectFrom('int', IsInt(rtemp))
        ltemp_bool_check = InjectFrom('int', IsBool(ltemp))
        rtemp_bool_check = InjectFrom('int', IsBool(rtemp))
        letNode = Let(ltemp, self.visit(node.left), Let(rtemp, self.visit(node.right), IfExp(ltemp_int_check,
                                                                                            IfExp(rtemp_int_check,
                                                                                                    InjectFrom('int', BinOp(ProjectTo('int', ltemp), node.op, ProjectTo('int', rtemp))),
                                                                                                    IfExp(rtemp_bool_check,
                                                                                                        InjectFrom('int', BinOp(ProjectTo('int', ltemp), node.op, ProjectTo('bool', rtemp))),
                                                                                                        TypeError('Unsupported Types for Addition'))),
                                                                                            IfExp(ltemp_bool_check,
                                                                                                    IfExp(rtemp_int_check,
                                                                                                        InjectFrom('int', BinOp(ProjectTo('bool', ltemp), node.op, ProjectTo('int', rtemp))),
                                                                                                        IfExp(rtemp_bool_check,
                                                                                                                InjectFrom('int', BinOp(ProjectTo('bool', ltemp), node.op, ProjectTo('bool', rtemp))),
                                                                                                                TypeError('Unsupported Types for Addition'))),
                                                                                                    IfExp(ltemp_big_check,
                                                                                                        IfExp(rtemp_big_check,
                                                                                                                InjectFrom('big', Call(Name('add', Load()), [ProjectTo('big', ltemp), ProjectTo('big', rtemp)], [])),
                                                                                                                TypeError('Unsupported Types for Addition')),
                                                                                                        TypeError('Unsupported Types for Addition'))))))
        return letNode
        # return Let(ltemp, self.visit(node.left), Let(rtemp, self.visit(node.right), IfExp(BoolOp(And(), [ltemp_bool_check, rtemp_bool_check]),
        #                                                                                     InjectFrom('int', BinOp(ProjectTo('bool', ltemp), node.op, ProjectTo('bool', rtemp))),
        #                                                                                     IfExp(BoolOp(And(), [ltemp_int_check, rtemp_int_check]),
        #                                                                                         InjectFrom('int', BinOp(ProjectTo('int', ltemp), node.op, ProjectTo('int', rtemp))),
        #                                                                                         IfExp(BoolOp(And(), [ltemp_bool_check, rtemp_int_check]), 
        #                                                                                             InjectFrom('int', BinOp(ProjectTo('bool', ltemp), node.op, ProjectTo('int', rtemp))),
        #                                                                                             IfExp(BoolOp(And(), [ltemp_int_check, rtemp_bool_check]),
        #                                                                                                 InjectFrom('int', BinOp(ProjectTo('int', ltemp), node.op, ProjectTo('bool', rtemp))),
        #                                                                                                 IfExp(big_check,
        #                                                                                                     InjectFrom('big', Call(Name('add', Load()), [ProjectTo('big', ltemp), ProjectTo('big', rtemp)], [])),
        #                                                                                                     TypeError('Unsupported Types for Addition/Concatenation'))))))))
    
    def visit_UnaryOp(self, node):
        temp = Name('tmp' + str(self.tmpCtr), Store())
        self.tmpCtr += 1
        if isinstance(node.op, Not):
            return Let(temp, self.visit(node.operand), InjectFrom('bool', UnaryOp(Not(), Call(Name('is_true', Load()), [temp], []))))
        return Let(temp, self.visit(node.operand), IfExp(InjectFrom('int', IsInt(temp)), 
                                                    InjectFrom('int', UnaryOp(node.op, ProjectTo('int', temp))), 
                                                    IfExp(InjectFrom('int', IsBool(temp)), 
                                                        InjectFrom('int', UnaryOp(node.op, ProjectTo('bool', temp))), 
                                                        TypeError('Unsupported Type for UnaryOp'))))

    def visit_Compare(self, node):
        ltemp = Name('tmp' + str(self.tmpCtr), Store())
        self.tmpCtr += 1
        rtemp = Name('tmp' + str(self.tmpCtr), Store())
        self.tmpCtr += 1
        #big_check = BoolOp(And(), [InjectFrom('int', IsBig(ltemp)), InjectFrom('int', IsBig(rtemp))])
        ltemp_big_check = InjectFrom('int', IsBig(ltemp))
        rtemp_big_check = InjectFrom('int', IsBig(rtemp))
        ltemp_int_check = InjectFrom('int', IsInt(ltemp))
        rtemp_int_check = InjectFrom('int', IsInt(rtemp))
        ltemp_bool_check = InjectFrom('int', IsBool(ltemp))
        rtemp_bool_check = InjectFrom('int', IsBool(rtemp))
        print(node.ops[0])
        equation = 'equal' if isinstance(node.ops[0], Eq) else 'not_equal'
        if isinstance(node.ops[0], ast.Is):
            letNode = Let(ltemp, self.visit(node.left), Let(rtemp, self.visit(node.comparators[0]), IfExp(ltemp_big_check,
                                                                                                        IfExp(rtemp_big_check,
                                                                                                            InjectFrom('bool', Compare(ltemp, [Eq()], [rtemp])),
                                                                                                            InjectFrom('bool', Constant(0))),
                                                                                                        InjectFrom('bool', Constant(0)))))
            return letNode
        letNode =  Let(ltemp, self.visit(node.left), Let(rtemp, self.visit(node.comparators[0]), IfExp(ltemp_bool_check,
                                                                                                    IfExp(rtemp_bool_check,
                                                                                                        InjectFrom('bool', Compare(ProjectTo('bool', ltemp), [node.ops[0]], [ProjectTo('bool', rtemp)])),
                                                                                                        IfExp(rtemp_int_check,
                                                                                                            InjectFrom('bool', Compare(ProjectTo('bool', ltemp), [node.ops[0]], [ProjectTo('int', rtemp)])),
                                                                                                            TypeError('Unsupported Types for Comparison'))),
                                                                                                    IfExp(ltemp_int_check,
                                                                                                        IfExp(rtemp_bool_check,
                                                                                                            InjectFrom('bool', Compare(ProjectTo('int', ltemp), [node.ops[0]], [ProjectTo('bool', rtemp)])),
                                                                                                            IfExp(rtemp_int_check,
                                                                                                                InjectFrom('bool', Compare(ProjectTo('int', ltemp), [node.ops[0]], [ProjectTo('int', rtemp)])),
                                                                                                                TypeError('Unsupported Types for Comparison'))),
                                                                                                        IfExp(ltemp_big_check,
                                                                                                            IfExp(rtemp_big_check,
                                                                                                                InjectFrom('bool', Call(Name(equation, Load()), [ProjectTo('big', ltemp), ProjectTo('big', rtemp)], [])),
                                                                                                                TypeError('Unsupported Types for Comparison')),
                                                                                                            TypeError('Unsupported Types for Comparison'))))))
        return letNode

    def visit_Slice(self, node):
        self.generic_visit(node)
        if node.step == None:
            node.step = Constant(1)
            node.step = self.visit(node.step)
        # if node.lower == None and node.upper == None:
        #     ltemp = Name('tmp' + str(self.tmpCtr), Store())
        #     self.tmpCtr += 1
        #     rtemp = Name('tmp' + str(self.tmpCtr), Store())
        #     self.tmpCtr += 1
        #     node.lower = Let(ltemp, Name(node.parent.value.id), IfExp(Call(Name('is_negative', Load()), [node.step], []),
        #                                                         InjectFrom('int', BinOp(Call(Name('get_length', Load()), [ltemp], []), Add(), InjectFrom('int', Constant(-1)))),
        #                                                             InjectFrom('int', Constant(0))))
        #     node.upper = Let(rtemp, Name(node.parent.value.id), IfExp(Call(Name('is_negative', Load()), [node.step], []), 
        #                                                         InjectFrom('int', Constant(0)),
        #                                                             Call(Name('get_length', Load()), [node.parent.value], [])))
        #     # node.lower = IfExp(InjectFrom('int', Call(Name('is_negative', Load()), [node.step], [])),  
        #     #                         BinOp(Call(Name('get_length', Load()), [node.parent.value], []), Add(), Constant(-1)), 
        #     #                             Constant(0))
        #     # node.upper = IfExp(InjectFrom('int', Call(Name('is_negative', Load()), [node.step], [])), 
        #     #                     Constant(0),
        #     #                         Call(Name('get_length', Load()), [node.parent.value], []))
        #     # node.lower = self.visit(node.lower)
        #     # node.upper = self.visit(node.upper)
        if node.lower == None:
            ltemp = Name('tmp' + str(self.tmpCtr), Store())
            self.tmpCtr += 1
            node.lower = Let(ltemp, Name(node.parent.value.id), IfExp(Call(Name('is_negative', Load()), [node.step], []), 
                                                                    InjectFrom('int', Constant(-1)), 
                                                                        InjectFrom('int', Constant(0))))
            # node.lower = self.visit(node.lower)
        if node.upper == None:
            ltemp = Name('tmp' + str(self.tmpCtr), Store())
            self.tmpCtr += 1
            node.upper = Let(ltemp, Name(node.parent.value.id), IfExp(Call(Name('is_negative', Load()), [node.step], []),
                                                                    InjectFrom('int', UnaryOp(USub(), BinOp(Call(Name('get_length', Load()), [Name(node.parent.value.id)], []), Add(), Constant(1)))),
                                                                        InjectFrom('int', Call(Name('get_length', Load()), [Name(node.parent.value.id)], []))))
        return node

    def visit_Subscript(self, node):
        node.value = self.visit(node.value)
        node.slice = self.visit(node.slice)
        return node

    def visit_MultiNode(self, node):
        for i in range(len(node.nodes)):
            node.nodes[i] = self.visit(node.nodes[i])
        return node
    