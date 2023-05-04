#!/usr/bin/env python3.10

import ast
from ast import *
import re

class IRClass(ast.NodeVisitor):
    def __init__(self):
        self.ifs = 0
        self.whiles = 0
        self.addTags = True
        self.graphs = {}
    
    def get_ir_graph(self, tree):
        ir = self.get_ir(tree.body)
        graph = self.get_graph(ir)
        return [ir, graph]

    def get_graph(self, ir):
        graph = []
        block = []
        tagLinks = {}
        # for i in ir:
        #     print(i)
        for i in range(len(ir)):
            line = ir[i]
            line.append(i)
            if line[0] == 'jne' or line[0] == 'je':
                block.append(line)
                graph.append([block, set()])
                block = []
            elif line[0] == 'jmp':
                block.append(line)
                graph.append([block, set()])
                block = []
            elif re.search('(whiletag\d+)|(ifEnd\d*)',line[0]) != None:
                if len(block):
                    graph.append([block, set()])
                block = [line]
                tagLinks.update({line[0][:-1]: len(graph)})
            else:
                block.append(line)
                tag = re.search('(whileEnd\d*)|(else\d*)', line[0])
                if tag != None:
                    tagLinks.update({tag.group(): len(graph)})
        if len(block):
            graph.append([block, set()])
        for i in range(len(graph)):
            startInst = graph[i][0][-1][0]
            jmpTarg = graph[i][0][-1][1]
            if startInst == 'jmp':
                graph[tagLinks[jmpTarg]][1].add(i)
            elif startInst == 'jne' or startInst == 'je':
                graph[tagLinks[jmpTarg]][1].add(i)
                if i+1 != len(graph):
                    graph[i+1][1].add(i)
            else:
                if i+1 != len(graph):
                    graph[i+1][1].add(i)
        return graph

    def get_ir(self, body):
        programIr = []
        for node in body:
            code = self.visit(node)
            if code != None:
                programIr += code
        return programIr
    
    def visit_Module(self, node):
        self.graphs['main'] = self.get_ir_graph(node) + [[]]

    def visit_If(self, node):
        ifs = self.ifs
        self.ifs += 1
        elseCode = self.get_ir(node.orelse)
        bodyCode = self.get_ir(node.body)
        cmpLine = self.visit(node.test)
        jumpOp = 'jne' if isinstance(node.test.ops[0], ast.Eq) else 'je'
        jumpString = 'else'+str(ifs) if len(elseCode) else 'ifEnd' + str(ifs)
        lines = [*cmpLine, [jumpOp, jumpString]]
        lines.append(['then'+str(ifs)+':'])
        bodyAppend = ['jmp', 'ifEnd' + str(ifs)]
        bodyCode.append(bodyAppend)
        lines += bodyCode
        if len(elseCode):
            lines.append(['else' + str(ifs)+':'])
            lines += elseCode
        lines.append(['ifEnd' + str(ifs) + ':'])
        return lines
    
    def visit_While(self, node):
        lines = [['whiletag' + str(self.whiles) + ':']]
        cmpOp = 'jne' if isinstance(node.test.ops[0], ast.Eq) else 'je'
        testAppendLine = [cmpOp, 'whileEnd' + str(self.whiles)]
        bodyAppend = [['jmp', 'whiletag' + str(self.whiles)],['whileEnd' + str(self.whiles)+':']]
        self.whiles += 1
        bodyCode = self.get_ir(node.body)
        testCode = self.get_ir(node.testtree)
        cmpLine = self.visit(node.test)
        testCode += cmpLine
        testCode.append(testAppendLine)
        lines += testCode
        bodyCode += bodyAppend
        lines += bodyCode
        return lines
    
    def visit_BinOp(self, node):
        lines = []
        left = node.left.id if isinstance(node.left, ast.Name) else node.left.n
        right = node.right.id if isinstance(node.right, ast.Name) else node.right.n
        if left == node.parent.targets[0].id:
            lines.append(['addl', right, left])
            return lines
        elif right == node.parent.targets[0].id:
            lines.append(['addl', left, right])
            return lines
        lines.append(['movl', left, node.parent.targets[0].id])
        if not isinstance(node.op, ast.Add):
            print("ERROR: p0 is add only\n")
            exit(1)
        lines.append(['addl', right, node.parent.targets[0].id])
        return lines
    
    def visit_Compare(self, node):
        lines = []
        left = node.left.id if isinstance(node.left, ast.Name) else node.left.n
        right = node.comparators[0].id if isinstance(node.comparators[0], ast.Name) else node.comparators[0].n
        lines.append(['cmpl', right, left])
        if isinstance(node.parent, ast.Assign):
            if isinstance(node.ops[0], ast.Eq):
                lines.append(['sete', node.parent.targets[0].id])
            else:
                lines.append(['setne', node.parent.targets[0].id])
        return lines
        
        
    def visit_UnaryOp(self, node):
        lines = []
        if (isinstance(node.operand, ast.Num)):
            lines.append(['movl', -node.operand.n if isinstance(node.op, ast.USub) else int(not node.operand.n), node.parent.targets[0].id])
        elif (isinstance(node.op, ast.USub)):
            if node.operand.id != node.parent.targets[0].id:
                lines.append(['movl', node.operand.id, node.parent.targets[0].id])
            lines.append(['negl', node.parent.targets[0].id])
        else:
            lines.append(['not', node.operand.id, node.parent.targets[0].id])
        if not isinstance(node.op, (ast.USub, ast.Not)):
            print("ERROR: p0 is sub and not only")
            exit(1)
        return lines
        
    def visit_Call(self, node):
        lines = []
        if (node.func.id == "print"):
            # print(ast.dump(node.args[0], indent=4))
            if (isinstance(node.args[0], ast.Name)):
                lines.append(['call','print_any', [node.args[0].id], None])
            else:
                print("ERROR: Unknown print input type")
                exit(1)
        elif (node.func.id == "input"):
            line = ['call', 'eval_input_pyobj', [], None]
            if isinstance(node.parent.parent, ast.Assign):
                line[3] = node.parent.parent.targets[0].id
            lines.append(line)
        elif (node.func.id == "eval"):
            return self.visit(node.args[0])
        else:
            args = []
            for arg in node.args:
                if isinstance(arg, ast.Name):
                    args.append(arg.id)
                else:
                    args.append(arg.value)
            line = ['call', node.func.id, args, None]
            if isinstance(node.parent, ast.Assign):
                line[3] = node.parent.targets[0].id
            lines.append(line)
        return lines
        

    def visit_Assign(self, node):
        lines = self.visit(node.value)
        if lines == None or len(lines) == 0:
            lines = []
            operand = node.value.id if isinstance(node.value , ast.Name) else node.value.n
            lines.append(['movl', operand, node.targets[0].id])
        return lines
    
    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit_Return(self, node):
        return [['return', node.value.id]]

    def visit_FunctionDef(self, node):
        self.graphs[node.name] = self.get_ir_graph(node)
        self.graphs[node.name].append([arg.arg for arg in node.args.args])
        return []

