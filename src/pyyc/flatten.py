import ast
from ast import *
from explicate import IsInt, IsBool, IsBig, TypeError, Let, ProjectTo, InjectFrom, Explicator
from closure import MultiNode, Closeify, IsFunc
from unique import Uniqueify
from heap import Heapify

class FlattenClass(ast.NodeTransformer):
    def __init__(self, newTree, tmpCtr):
        self.tmpCtr = tmpCtr
        self.newTree = newTree
        self.base = self.newTree.body
        self.parent = self.newTree
        self.get_length_parent = None
    
    def visit_Expr(self, node):
        self.generic_visit(node)
        if isinstance(node.parent, (ast.Module, ast.If, ast.While)):
            self.base.append(node)
        return node
        
    def visit_Assign(self, node):
        node.value = self.visit(node.value)
        # node.value = self.visit(node.value)
        # node.targets = [self.visit(node.targets[0])]
        # if isinstance(node.parent, (ast.Module, ast.If, ast.While)):
        if not isinstance(node.targets[0], ast.Subscript):
            self.base.append(node)
        node.targets = [self.visit(node.targets[0])]
        return node

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if not isinstance(node.parent, ast.Assign):
            nameNode = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
            newNode = ast.Name("tmp"+str(self.tmpCtr), ast.Load())
            self.tmpCtr += 1
            assignNode = ast.Assign([nameNode], node)
            nameNode.parent = assignNode
            assignNode.parent = self.parent
            self.base.append(assignNode)
            newNode.parent = node.parent
            return newNode
        return node
        
    def visit_UnaryOp(self, node):
        if isinstance(node, ast.Not):
            # if (not isinstance(node.parent, ast.Call)) or (not node.parent.func.id == 'int'):
            #     raise Exception('not expr must be wrapped in int')
            node.parent = node.parent.parent
        self.generic_visit(node)
        if not isinstance(node.parent, ast.Assign):
            nameNode = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
            assignNode = ast.Assign([nameNode], node)
            nameNode.parent = assignNode
            assignNode.parent = self.parent
            self.base.append(assignNode)
            newNode = ast.Name("tmp"+str(self.tmpCtr), ast.Load())
            newNode.parent = node.parent
            self.tmpCtr += 1
            return newNode
        return node

    def visit_Call(self, node):
        if isinstance(node.func, Name) and node.func.id == 'get_length':
            node.args[0] = Name(self.get_length_parent.id)
            node.args[0].parent = node
        node.args = [self.visit(arg) for arg in node.args]
        node.func = self.visit(node.func)
        if isinstance(node.func, Name):
            if node.func.id == 'int':
                val = node.args[0]
                code = '{0} = project_bool({0})\n{0} = inject_int({0})'.format(val.id)
                tree = ast.parse(code).body
                self.base += tree
                return val
            #case where input is wrapped in eval
            if node.func.id == "input" and isinstance(node.parent, ast.Call) and node.parent.func.id == "eval":
                return node
        if not isinstance(node.parent, ast.Assign) and not isinstance(node.parent, ast.Expr):
            nameNode = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
            assignNode = ast.Assign([nameNode], node)
            nameNode.parent = assignNode
            assignNode.parent = self.parent
            self.base.append(assignNode)
            newNode = ast.Name("tmp"+str(self.tmpCtr), ast.Load())
            self.tmpCtr += 1
            newNode.parent = node.parent
            return newNode
        return node

    def visit_BoolOp(self, node):
        self.generic_visit(node)
        # if not isinstance(node.parent, ast.Assign):
        
        nameNode = None
        newNode = None
        if isinstance(node.parent, ast.Assign):
            nameNode = ast.Name(node.parent.targets[0].id, ast.Store())
            newNode = ast.Name(node.parent.targets[0].id, ast.Load())
        else:   
            nameNode = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
            newNode = ast.Name("tmp"+str(self.tmpCtr), ast.Load())
            self.tmpCtr += 1
        
        parentIf = ast.If(None, [], [])
        parentIf.parent = self.parent
        #parentIfSaved = parentIf
        preBase = self.base
        preParent = self.parent
        testNode = None
        if isinstance(node.op, ast.And):
            for value in node.values:
                testNode = self.visit(value)
                # if isinstance(testNode, ast.Constant):
                #     constToName = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
                #     assignNode = ast.Assign([constToName], testNode)
                #     constToName.parent =assignNode
                #     assignNode.parent =self.parent
                #     self.base.append(assignNode)
                #     testNode = ast.Name("tmp"+str(self.tmpCtr), ast.Load())
                #     self.tmpCtr+=1

                testTemp = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
                self.tmpCtr+=1
                testAssign = ast.Assign([testTemp], ast.Call(ast.Name("is_true", ast.Load()), [testNode], []))
                self.base.append(testAssign)
                testCompare = ast.Compare(testTemp, [ast.NotEq()], [ast.Constant(0)])
                testCompare.parent = parentIf
                parentIf.test = testCompare
                self.base.append(parentIf)

                # if not isinstance(testNode, ast.Compare):
                #     parentIf.test = ast.Compare(testNode, [ast.NotEq()], [ast.Constant(0)])
                #     parentIf.test.parent = parentIf
                # else:
                #     parentIf.test = testNode
                # self.base.append(parentIf)

                assignElse = ast.Assign([nameNode], value)
                assignElse.parent = parentIf
                parentIf.orelse = [assignElse]
                parentIf.body = []
                self.base = parentIf.body
                self.parent = parentIf
                newIf = ast.If(None, [], [])
                newIf.parent = parentIf
                parentIf = newIf
            if isinstance(testNode, ast.Name):
                assignRight = ast.Name(testNode.id, ast.Store())
            else:
                assignRight = testNode
            finalAssign = ast.Assign([nameNode], assignRight)
            nameNode.parent = finalAssign
            assignRight.parent = finalAssign
            parentIf = parentIf.parent
            finalAssign.parent = parentIf
            parentIf.body = [finalAssign]
            self.base = preBase
            self.parent = preParent
            #self.base.append(parentIfSaved)

        else: # Or statement
            default = node.values[-1]
            for value in node.values:
                testNode = self.visit(value)
                # if isinstance(testNode, ast.Constant):
                #     constToName = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
                #     assignNode = ast.Assign([constToName], testNode)
                #     constToName.parent =assignNode
                #     assignNode.parent =self.parent
                #     self.base.append(assignNode)
                #     testNode = ast.Name("tmp"+str(self.tmpCtr), ast.Load())
                #     self.tmpCtr+=1          
                
                testTemp = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
                self.tmpCtr+=1
                testAssign = ast.Assign([testTemp], ast.Call(ast.Name("is_true", ast.Load()), [testNode], []))
                self.base.append(testAssign)
                testCompare = ast.Compare(testTemp, [ast.NotEq()], [ast.Constant(0)])
                testCompare.parent = parentIf
                parentIf.test = testCompare
                self.base.append(parentIf)

                # if not isinstance(testNode, ast.Compare):
                #     parentIf.test = ast.Compare(testNode, [ast.NotEq()], [ast.Constant(0)])
                #     parentIf.test.parent = parentIf
                # else:
                #     parentIf.test = testNode
                # self.base.append(parentIf)

                assignIf = ast.Assign([nameNode], testNode)
                assignIf.parent = parentIf
                parentIf.body = [assignIf]
                parentIf.orelse = []
                self.base = parentIf.orelse
                self.parent = parentIf
                newIf = ast.If(None, [], [])
                newIf.parent = parentIf
                parentIf = newIf
            if isinstance(testNode, ast.Name):
                assignRight = ast.Name(testNode.id, ast.Store())
            else:
                assignRight = testNode
            finalAssign = ast.Assign([nameNode], assignRight)
            nameNode.parent = finalAssign
            assignRight.parent = finalAssign
            parentIf = parentIf.parent
            finalAssign.parent = parentIf
            parentIf.body = [finalAssign]
            finalAssignElse = ast.Assign([nameNode], default)
            finalAssignElse.parent = parentIf
            parentIf.orelse = [finalAssignElse]
            self.base = preBase
            self.parent = preParent
        
        newNode.parent = node.parent
        return newNode
        # return node

    def visit_Compare(self, node):
        # if (not isinstance(node.parent, ast.Call)) or (not node.parent.func.id == 'int'):
        #     raise Exception('comparators must be wrapped in int')
        node.parent = node.parent.parent

        '''
        op1 = self.visit(node.left)
        op2 = self.visit(node.comparators[0])
        op = node.ops[0]
        lval = 
        Call(equal if op == "==" else "not_equal", [lval, rval], [])
        '''

        self.generic_visit(node)
        #isNotIfTest = (not isinstance(node.parent, ast.If)) or (isinstance(node.parent.test, ast.Call) and node.parent.test.args[0] != node)
        #isNotWhileTest = (not isinstance(node.parent, ast.While)) or (isinstance(node.parent.test, ast.Call) and node.parent.test.args[0] != node)

        if (not isinstance(node.parent, ast.Assign)): #and not isinstance(node.parent, ast.BoolOp)) and isNotIfTest and isNotWhileTest:
            nameNode = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
            assignNode = ast.Assign([nameNode], node)
            nameNode.parent = assignNode
            assignNode.parent = self.parent
            self.base.append(assignNode)
            newNode = ast.Name("tmp"+str(self.tmpCtr), ast.Load())
            newNode.parent = node.parent
            self.tmpCtr += 1
            return newNode
        return node
    
    def visit_If(self, node):
        preBase = self.base
        preParent = self.parent

        testNode = self.visit(node.test)

        testTemp = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
        self.tmpCtr+=1
        testAssign = ast.Assign([testTemp], ast.Call(ast.Name("is_true", ast.Load()), [testNode], []))
        self.base.append(testAssign)
        testCompare = ast.Compare(testTemp, [ast.NotEq()], [ast.Constant(0)])
        testCompare.parent = node
        node.test = testCompare

        self.parent = node
        oldbody = node.body
        node.body = []
        self.base = node.body
        for child in oldbody:
            self.visit(child)
        
        oldelse = node.orelse
        node.orelse = []
        self.base = node.orelse
        for child in oldelse:
            self.visit(child)
        
        self.base = preBase
        self.parent = preParent
        self.base.append(node)
        return node

    def visit_While(self, node):
        preBase = self.base
        preParent = self.parent

        node.testtree = []
        self.base = node.testtree
        self.parent = node

        testNode = self.visit(node.test)

        testTemp = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
        self.tmpCtr+=1
        testAssign = ast.Assign([testTemp], ast.Call(ast.Name("is_true", ast.Load()), [testNode], []))
        self.base.append(testAssign)
        testCompare = ast.Compare(testTemp, [ast.NotEq()], [ast.Constant(0)])
        testCompare.parent = node
        node.test = testCompare


        oldbody = node.body
        node.body = []
        self.base = node.body
        for child in oldbody:
            self.visit(child)
        
        self.base = preBase
        self.parent = preParent
        self.base.append(node)
        for child in node.orelse:
            self.visit(child)
        node.orelse = []
        # node.body = node.testtree + node.body
        # print(ast.dump(node, indent=4))
        return node
    
    def visit_IfExp(self, node):
        preBase = self.base
        preParent = self.parent

        ifNode = ast.If(None, [], [])
        testNode=self.visit(node.test)
        # if not isinstance(testNode, ast.Compare):
        #     ifNode.test = ast.Compare(testNode, [ast.NotEq()], [ast.Constant(0)])
        #     ifNode.test.parent = ifNode
        # else:
        #     ifNode.test = testNode

        testTemp = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
        self.tmpCtr+=1
        testAssign = ast.Assign([testTemp], ast.Call(ast.Name("is_true", ast.Load()), [testNode], []))
        self.base.append(testAssign)
        testCompare = ast.Compare(testTemp, [ast.NotEq()], [ast.Constant(0)])
        testCompare.parent = ifNode
        ifNode.test = testCompare

        
        self.base = ifNode.body
        self.parent = ifNode
        ifVal=self.visit(node.body)
        
        self.base = ifNode.orelse
        elseVal=self.visit(node.orelse)

        newTmp = None
        if not ((hasattr(node.parent, 'body') and ((isinstance(node.parent.body, List) and node in node.parent.body)))\
                or (hasattr(node.parent, 'orelse') and ((isinstance(node.parent.orelse, List) and node in node.parent.orelse)))):
            newTmp = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
            self.tmpCtr += 1
            ifAssign = ast.Assign([newTmp], ifVal)
            ifVal.parent = ifAssign
            ifAssign.parent = ifNode
            ifNode.body.append(ifAssign)

            elseAssign = ast.Assign([newTmp], elseVal)
            elseVal.parent = elseAssign
            elseAssign.parent = ifNode
            ifNode.orelse.append(elseAssign)
        else:
            # print(node.parent, (hasattr(node.parent, 'body') and (node == node.parent.body or (isinstance(node.parent.body, List) and node in node.parent.body))))
            # print('hello')
            ifNode.body.append(ifVal)
            ifNode.orelse.append(elseVal)
            
        ifNode.parent = preParent
        self.base = preBase
        self.parent = preParent
        self.base.append(ifNode)
        return newTmp

    def visit_List(self, node):
        self.generic_visit(node)
        vals = node.elts
        # create_list = Call(Name('create_list'), [Constant(len(vals))], [], None, None])
        # set_subs = [Call(Name('set_subscript'), [create_list, Constant(i), vals[i]], [], None, None) for i in range(len(vals))]
        # add it to your node
        ### NEED TO BOX LENGTH AND KEYS

        listExplicate = 'tmp{tmp1}=inject_int({listLength})\ntmp{tmp0} = create_list(tmp{tmp1})\ntmp{tmp0}=inject_big(tmp{tmp0})'.format(tmp1=self.tmpCtr+1,tmp0=self.tmpCtr, listLength=len(vals))
        for i in range(len(vals)):
            listExplicate += '\ntmp{tmp1}=inject_int({cnt})\nset_subscript(tmp{tmp0}, tmp{tmp1}, {val}, 0, 0)'.format(tmp1=self.tmpCtr+2, tmp0=self.tmpCtr, cnt=i, val=vals[i].id)
        explicateTree = ast.parse(listExplicate).body
        self.base += explicateTree
        nameNode = Name('tmp' + str(self.tmpCtr), ast.Load())
        self.tmpCtr += 3
        return nameNode

    def visit_String(self, node):
        self.generic_visit(node)
        stringExplicate = 'tmp{tmp1}=inject_int({listLength})\ntmp{tmp0} = create_string(tmp{tmp1})\ntmp{tmp0}=inject_big(tmp{tmp0})'.format(tmp1=self.tmpCtr+1,tmp0=self.tmpCtr, listLength=len(node.string))
        for i in range(len(node.string)):
            stringExplicate += '\ntmp{tmp1}=inject_int({cnt})\nset_subscript(tmp{tmp0}, tmp{tmp1}, {val}, 0, 0)'.format(tmp1=self.tmpCtr+2, tmp0=self.tmpCtr, cnt=i, val=node.string[i].id)
        explicateTree = ast.parse(stringExplicate).body
        self.base += explicateTree
        nameNode = Name('tmp' + str(self.tmpCtr), ast.Load())
        self.tmpCtr += 3
        return nameNode
    # from explicate import InjectFrom
    
    # def visit_InjectFrom(self, node):
    #     return Call(Name(node.type), [self.visit(node.arg)], [], None, None)
    
    def visit_Dict(self, node):
        self.generic_visit(node)
        kvs = [(k, v) for (k, v) in zip(node.keys, node.values)]
        dictExplicate = 'tmp{tmp0} = create_dict()\ntmp{tmp0}=inject_big(tmp{tmp0})'.format(tmp0=self.tmpCtr)
        ### NEED TO BOX KEYS AND PTR FROM CREATE_DICT
        for i in range(len(kvs)):
            # if isinstance(kvs[i][0], ast.Constant):
            #     dictExplicate += '\nset_subscript(tmp{tmp0}, {key}, {val})'.format(tmp0=self.tmpCtr, key=kvs[i][0].value , val=kvs[i][1].value)
            # elif isinstance(kvs[i][0], ast.Name):
            dictExplicate += '\nset_subscript(tmp{tmp0}, {key}, {val}, 0, 0)'.format(tmp0=self.tmpCtr, key=kvs[i][0].id, val=kvs[i][1].id)
        explicateTree = ast.parse(dictExplicate).body
        self.base += explicateTree
        nameNode = Name('tmp' + str(self.tmpCtr), ast.Load())
        nameNode.parent = self.parent
        self.tmpCtr += 1
        return nameNode

    def visit_Slice(self, node):
        node.step = self.visit(node.step)
        node.lower = self.visit(node.lower)
        self.get_length_parent = node.parent.value
        node.upper = self.visit(node.upper)
        return node


    def visit_Subscript(self, node):
        node.value = self.visit(node.value)
        node.slice = self.visit(node.slice)
        obj = node.value.id
        if isinstance(node.ctx, ast.Store):
            start = node.slice.lower.id if isinstance(node.slice, ast.Slice) else node.slice.id
            step = 0
            end = 0
            # print(ast.dump(node))
            if isinstance(node.slice, ast.Slice):
                step = node.slice.step.id
                end = node.slice.upper.id
            val = node.parent.value.id
            explicateString = f'set_subscript({obj}, {start}, {val}, {end}, {step})'
            explicateTree = ast.parse(explicateString).body
            self.base += explicateTree
            return node.value
        else: #load
            start = node.slice.lower.id if isinstance(node.slice, ast.Slice) else node.slice.id
            step = 0
            end = 0
            # print(ast.dump(node))
            if isinstance(node.slice, ast.Slice):
                step = node.slice.step.id
                end = node.slice.upper.id
            explicateString = f'get_subscript({obj},{start},{end},{step})'
            explicateTree = ast.parse(explicateString).body
            if not isinstance(node.parent, ast.Assign) or isinstance(node.parent.targets[0], ast.Subscript):
                tmpVar = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
                self.tmpCtr += 1
                assignNode = Assign([tmpVar], explicateTree[0].value)
                assignNode.parent = self.parent
                self.base.append(assignNode)
                return tmpVar
            return explicateTree[0].value

    def visit_Return(self, node):
        self.generic_visit(node)
        self.base.append(node)
        return node

    def visit_FunctionDef(self, node):
        preBase = self.base
        preParent = self.parent

        newBody = []
        self.base = newBody
        self.parent = node

        self.generic_visit(node)
        node.body = newBody
        
        self.base = preBase
        self.parent = preParent
        self.base.append(node)
        return node
        
        
    def visit_InjectFrom(self, node):
        tmpVar = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
        tmpVarRet = ast.Name("tmp" + str(self.tmpCtr), ast.Load())
        tmpVarRet.parent = node.parent
        self.tmpCtr += 1
        arg = self.visit(node.arg)
        assignNode = ast.Assign([tmpVar], ast.Call(ast.Name("inject_"+node.type, ast.Load()), [arg], []))
        tmpVar.parent = assignNode
        assignNode.parent = self.parent
        self.base.append(assignNode)
        # print(node.parent)
        return tmpVarRet
    
    def visit_ProjectTo(self, node):
        tmpVar = ast.Name("tmp"+str(self.tmpCtr), ast.Load())
        self.tmpCtr += 1
        tmpVar.parent = self.parent
        arg = self.visit(node.arg)
        self.base.append(ast.Assign([tmpVar], ast.Call(ast.Name("project_"+node.type, ast.Load()), [arg], [])))
        return tmpVar

    def visit_IsInt(self, node):
        var = self.visit(node.obj)
        if isinstance(node.parent, ast.Assign):
            return ast.Call(ast.Name("is_int", ast.Load()), [var], [])
        tmpVar = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
        self.tmpCtr += 1
        self.base.append(ast.Assign([tmpVar], ast.Call(ast.Name("is_int", ast.Load()), [var], [])))
        return tmpVar
    
    def visit_IsBool(self, node):
        var = self.visit(node.obj)
        if isinstance(node.parent, ast.Assign):
            return ast.Call(ast.Name("is_bool", ast.Load()), [var], [])
        tmpVar = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
        self.tmpCtr += 1
        self.base.append(ast.Assign([tmpVar], ast.Call(ast.Name("is_bool", ast.Load()), [var], [])))
        return tmpVar
    
    def visit_IsBig(self, node):
        var = self.visit(node.obj)
        if isinstance(node.parent, ast.Assign):
            return ast.Call(ast.Name("is_big", ast.Load()), [var], [])
        tmpVar = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
        self.tmpCtr += 1
        self.base.append(ast.Assign([tmpVar], ast.Call(ast.Name("is_big", ast.Load()), [var], [])))
        return tmpVar

    def visit_IsFunc(self, node):
        var = self.visit(node.obj)
        if isinstance(node.parent, ast.Assign):
            return ast.Call(ast.Name("is_function", ast.Load()), [var], [])
        tmpVar = ast.Name("tmp"+str(self.tmpCtr), ast.Store())
        self.tmpCtr += 1
        self.base.append(ast.Assign([tmpVar], ast.Call(ast.Name("is_function", ast.Load()), [var], [])))
        return tmpVar

    def visit_Let(self, node):
        node.var = self.visit(node.var)
        node.rhs = self.visit(node.rhs)
        self.base.append(ast.Assign([node.var], node.rhs))
        return self.visit(node.body)

    def visit_MultiNode(self, node):
        for child in node.nodes:
            self.visit(child)
        return None

    def visit_TypeError(self, node):
        self.base.append(ast.Call(ast.Name("error_pyobj", ast.Load()), [ast.Constant(0)], []))
        return ast.Constant(0)

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
# nl = lambda x: lambda y: x + y
# print(nl(23)(42))
# '''

# p = addParents()
# u = Uniqueify()
# tree = parse(test)
# p.visit(tree)
# u.visit(tree)
# p.visit(tree)
# fix_missing_locations(tree)
# h = Heapify(u.free, u.freePerFunc)
# h.visit(tree)
# p.visit(tree)
# c = Closeify(u.freePerFunc, u.free)
# c.visit(tree)
# p.visit(tree)
# e = Explicator(0)
# e.visit(tree)
# p.visit(tree)
# newTree = Module([],[])
# f = FlattenClass(newTree, e.tmpCtr)
# f.generic_visit(tree)
# fix_missing_locations(newTree)
# print(unparse(newTree))