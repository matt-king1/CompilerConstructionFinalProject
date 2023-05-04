#!/usr/bin/env python3.10

import ast
import sys
from ast import *
import re

from flatten import FlattenClass
from ir import IRClass
from liveness import LivenessAnalyzer
from graphbuild import GraphBuilder
from color import GraphColorer
from spill import Spiller
from explicate import Explicator
from unique import Uniqueify
from heap import Heapify
from closure import Closeify

newFileName = sys.argv[1].split(".")[0] + ".s"
try:
    assem = open(newFileName, "x")
except:
    print("file exists, not creating new file")
assem = open(newFileName, "w")

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

class CompilerClass():
    def __init__(self, allFuncs):
        self.varlocs = dict()
        self.esploc = -4
        self.newlines = []
        self.allFuncs = allFuncs
        self.finalLines = []
        
    def to_x86(self, lines, coloring, funcName, args):
        global assem
        # self.newlines.append(".section .data")
        # self.newlines.append('''msg: .string "Type Error\\n"''')
        # self.newlines.append(".section .text")
        self.varlocs = dict()
        self.esploc = -4
        self.newlines = []
        self.lines = lines
        self.coloring = coloring
        if funcName == 'main':
            self.newlines.append('.globl main')
        self.newlines.append(funcName + ':')
        indent = 1
        
        self.newlines.append('    '+"pushl %ebp")
        self.newlines.append('    '+"movl %esp, %ebp")

        if sum(map(('%ebx').__eq__, self.coloring.values())) > 1:
            self.newlines.append('    '+"pushl %ebx")
        if sum(map(('%esi').__eq__, self.coloring.values())) > 1:
            self.newlines.append('    '+"pushl %esi")
        if sum(map(('%edi').__eq__, self.coloring.values())) > 1:
            self.newlines.append('    '+"pushl %edi")
        returned = False
        for i, arg in enumerate(args):
            color = coloring.get(arg)
            # print(arg, color)
            if color == 'stack':
                if arg not in self.varlocs:
                    self.varlocs[arg] = self.esploc
                    self.esploc -= 4
                self.newlines.append('    '+"movl " +str(i*4+8)+"(%ebp), %eax")
                self.newlines.append('    '+"movl %eax, " + str(self.varlocs.get(arg)) + '(%ebp)')
            else:
                self.newlines.append('    '+"movl " +str(i*4+8)+ "(%ebp), " + color)

        self.newlines.append("\n")
        last = None
        for line in self.lines:
            match line[0]:
                case "movl":
                    sourceColoring = self.coloring.get(line[1], '$'+str(line[1]))
                    targetColoring = self.coloring.get(line[2], '$'+str(line[2]))
                    if not sourceColoring == targetColoring:
                        if sourceColoring == 'stack':
                            self.newlines.append(('    '*indent)+"movl " + str(self.varlocs.get(line[1])) + '(%ebp)' + ', ' + targetColoring)    
                        elif targetColoring == 'stack':
                            if line[2] not in self.varlocs:
                                self.varlocs[line[2]] = self.esploc
                                self.esploc -= 4
                            self.newlines.append(('    '*indent)+"movl " + sourceColoring + ', ' + str(self.varlocs.get(line[2])) + '(%ebp)')
                        else:
                            self.newlines.append(('    '*indent)+"movl " + sourceColoring + ', ' + targetColoring)
                            
                case "addl":
                    sourceColoring = self.coloring.get(line[1], '$'+str(line[1]))
                    targetColoring = self.coloring.get(line[2], '$'+str(line[2]))
                    if sourceColoring == 'stack':
                        self.newlines.append(('    '*indent)+"addl " + str(self.varlocs.get(line[1])) + '(%ebp)' + ', ' + targetColoring)
                    elif targetColoring == 'stack':
                        if line[2] not in self.varlocs:
                            self.varlocs[line[2]] = self.esploc
                            self.esploc -= 4
                        self.newlines.append(('    '*indent)+"addl " + sourceColoring + ', ' + str(self.varlocs.get(line[2])) + '(%ebp)')
                    else:
                        self.newlines.append(('    '*indent)+"addl " + sourceColoring + ', ' +  targetColoring)
                        
                case "negl":
                    self.newlines.append(('    '*indent)+"negl " + self.coloring.get(line[1]))

                case "call":
                    if line[1] == 'error_pyobj':
                        self.newlines.append(('    '*indent)+"pushl $0")
                        self.newlines.append(('    '*indent)+"call " + line[1])
                        self.newlines.append(('    '*indent)+"addl $4, %esp")
                    elif line[1][0:3] != 'tmp':
                        for arg in line[2][::-1]:
                            self.newlines.append(('    '*indent)+"pushl " + self.coloring.get(arg, '$'+str(arg)))
                        self.newlines.append(('    '*indent)+"call " + line[1])
                        if len(line[2]) > 0:
                            self.newlines.append(('    '*indent)+"addl $" + str(len(line[2]) * 4) + ", %esp")
                        if line[3] != None:
                            targetColoring = self.coloring.get(line[3])
                            if targetColoring != '%eax':
                                if targetColoring == 'stack':
                                    if self.varlocs.get(line[3]) == None:
                                        self.varlocs[line[3]] = self.esploc
                                        self.esploc -= 4
                                    targetColoring = str(self.varlocs.get(line[3])) + '(%ebp)'
                                self.newlines.append(('    '*indent)+"movl %eax, " + targetColoring)
                    else:
                        coloring = self.coloring.get(line[1])
                        if coloring == 'stack':
                            coloring =  str(self.varlocs.get(line[1])) + '(%ebp)'
                            #self.newlines.append('    '*indent+'pushl ' + str(self.varlocs.get(line[1])) + '(%ebp)')
                        #else:
                        #     self.newlines.append('    '*indent+'pushl ' + coloring)
                        # self.newlines.append('    '*indent+'call get_function')
                        # self.newlines.append(('    '*indent)+"addl $4, %esp")
                        for arg in line[2][::-1]:
                            self.newlines.append(('    '*indent)+"pushl " + self.coloring.get(arg, '$'+str(arg)))
                        self.newlines.append('    '*indent+'call *' + coloring)
                        if len(line[2]) > 0:
                            self.newlines.append(('    '*indent)+"addl $" + str(len(line[2]) * 4) + ", %esp")
                        if line[3] != None:
                            targetColoring = self.coloring.get(line[3])
                            if targetColoring != '%eax':
                                if targetColoring == 'stack':
                                    if self.varlocs.get(line[3]) == None:
                                        self.varlocs[line[3]] = self.esploc
                                        self.esploc -= 4
                                    targetColoring = str(self.varlocs.get(line[3])) + '(%ebp)'
                                self.newlines.append(('    '*indent)+"movl %eax, " + targetColoring)
                case 'jmp':
                    self.newlines.append(('    '*indent)+"jmp " + line[1])
                case 'jne':
                    self.newlines.append(('    '*indent)+"jne " + line[1])
                case 'je':
                    self.newlines.append(('    '*indent)+"je " + line[1])
                case 'setne':
                    self.newlines.append(('    '*indent)+"setne %al")
                    position = self.coloring.get(line[1], '$'+str(line[1]))
                    if position == 'stack':
                        stackPosition = self.varlocs.get(line[1], None)
                        if stackPosition == None:
                            self.varlocs[line[1]] = self.esploc
                            position = str(self.esploc) + '(%ebp)'
                            self.esploc -= 4
                        else:
                            position = str(stackPosition)+ '(%ebp)'
                    # print(position)
                    self.newlines.append(('    '*indent)+"movzbl %al, " + position)
                case 'sete':
                    self.newlines.append(('    '*indent)+"sete %al")
                    position = self.coloring.get(line[1], '$'+str(line[1]))
                    if position == 'stack':
                        stackPosition = self.varlocs.get(line[1], None)
                        if stackPosition == None:
                            self.varlocs[line[1]] = self.esploc
                            position = str(self.esploc) + '(%ebp)'
                            self.esploc -= 4
                        else:
                            position = str(stackPosition)+ '(%ebp)'
                    self.newlines.append(('    '*indent)+"movzbl %al, " + position)
                case 'cmpl':
                    sourceColoring = self.coloring.get(line[1], '$'+str(line[1]))
                    targetColoring = self.coloring.get(line[2], '$'+str(line[2]))
                    if sourceColoring == 'stack':
                        if line[1] not in self.varlocs:
                            self.varlocs[line[1]] = self.esploc
                            self.esploc -= 4
                        sourceColoring =  str(self.varlocs[line[1]]) + '(%ebp)'
                        self.newlines.append(('    '*indent)+"cmpl " + str(self.varlocs.get(line[1])) + '(%ebp)' + ', ' + targetColoring)
                    elif targetColoring == 'stack':
                        if line[2] not in self.varlocs:
                            self.varlocs[line[2]] = self.esploc
                            self.esploc -= 4
                        targetColoring =  str(self.varlocs[line[2]]) + '(%ebp)'
                        self.newlines.append(('    '*indent)+"cmpl " + sourceColoring + ', ' + str(self.varlocs.get(line[2])) + '(%ebp)')
                    else:
                        self.newlines.append(('    '*indent)+"cmpl " + sourceColoring + ', ' +  targetColoring)
                case "not":
                    sourceColoring = self.coloring.get(line[1])
                    targetColoring = self.coloring.get(line[2]) #neither can be immediate
                    if sourceColoring == 'stack':
                        if line[1] not in self.varlocs:
                            self.varlocs[line[1]] = self.esploc
                            self.esploc -= 4
                        sourceColoring = str(self.varlocs[line[1]]) + '(%ebp)'
                    if targetColoring == 'stack':
                        if line[2] not in self.varlocs:
                            self.varlocs[line[2]] = self.esploc
                            self.esploc -= 4
                        targetColoring = str(self.varlocs[line[2]]) + '(%ebp)'
                    self.newlines.append(('    '*indent)+"cmpl $0, " + sourceColoring)
                    self.newlines.append(('    '*indent + "sete %al"))
                    self.newlines.append(('    '*indent + "movzbl %al, "+ targetColoring))
                case "return":
                    sourceColoring = self.coloring.get(line[1])
                    if sourceColoring == 'stack':
                        if line[1] not in self.varlocs:
                            self.varlocs[line[1]] = self.esploc
                            self.esploc -= 4
                        sourceColoring = str(self.varlocs[line[1]]) + '(%ebp)'
                    self.newlines.append(('    '*indent)+"movl " + sourceColoring + ", %eax")
                    returned = True
                case _:
                    searchTabStart = re.search('(whiletag\d*)|(then\d*)', line[0])
                    searchTabNone = re.search('(else\d*)', line[0])
                    searchTabEnd = re.search('(whileEnd\d*)|(ifEnd\d*)', line[0])
                    if searchTabStart:
                        self.newlines.append(('    '*indent)+ line[0])
                        indent += 1
                        last = 'start'
                    elif searchTabEnd:
                        indent -= 1
                        self.newlines.append(('    '*indent)+ line[0])
                        last = 'end'
                    elif searchTabNone:
                        if last == 'none':
                            indent -= 1
                        self.newlines.append((indent-1)*'    ' + line[0])
                        last = 'none'
                    else:
                        print("invalid instruction during compilation: " + line[0])
                        exit(1)
        
        self.esploc += 4
        if funcName == 'main':
            self.newlines.insert(4,"    subl $" + str(abs(self.esploc)) + ", %esp\n")
        else:
            self.newlines.insert(3,"    subl $" + str(abs(self.esploc)) + ", %esp\n")
        self.newlines.append("\n")
        if not returned:
            self.newlines.append("    movl $0, %eax")

        if sum(map(('%edi').__eq__, self.coloring.values())) > 1:
            self.newlines.append('    '+"popl %edi")
        if sum(map(('%esi').__eq__, self.coloring.values())) > 1:
            self.newlines.append('    '+"popl %esi")
        if sum(map(('%ebx').__eq__, self.coloring.values())) > 1:
            self.newlines.append('    '+"popl %ebx")

        self.newlines.append("    movl %ebp, %esp")
        self.newlines.append("    popl %ebp")

        self.newlines.append("    ret")

        self.finalLines += self.newlines

if(len(sys.argv) != 2):
    print("Usage: ./pyyc [test]")
    exit(1)
prog = ""
with open(sys.argv[1]) as file:
    prog = file.read() + '\n'
    tree = ast.parse(prog)
p = addParents()
p.visit(tree)

u = Uniqueify()
u.visit(tree)
p.visit(tree)

h = Heapify(u.free, u.freePerFunc)
h.visit(tree)
p.visit(tree)

cl = Closeify(u.freePerFunc, u.free)
cl.visit(tree)
p.visit(tree)

e = Explicator(cl.tmpCtr)
e.visit(tree)

p.visit(tree)
newTree = ast.Module([], [])
f = FlattenClass(newTree, e.tmpCtr)
f.visit(tree)
ast.fix_missing_locations(newTree)

p.visit(newTree)
# print(ast.dump(newTree, indent=4))
# print(ast.unparse(newTree))
# exit(0)
# print(ast.unparse(newTree))

ir = IRClass()
ir.visit(newTree)
graphs = ir.graphs

# for line in progIr:
#     print(line)

funcNames = list(graphs.keys())
# print(funcNames)
comp = CompilerClass(funcNames)

for funcName, graph in graphs.items():
    didSpill = True
    lines = graph[0]
    irGraph = graph[1]
    stacked: list[str] = list()
    tmpcnt = f.tmpCtr
    coloring = dict()
    s = Spiller()
    # if funcName != 'main':
    #     print(graph[-1])
    #     for block in irGraph[0]:
    #         for line in block:
    #             print(line)
    #         print(irGraph[1])
    while didSpill:

        l = LivenessAnalyzer(lines)
        l.analyze(irGraph, lines, len(irGraph)-1, set(graph[-1]), funcName)
        gb = GraphBuilder(lines, l.liveness)
        gb.build(graph[-1])
        c = GraphColorer(gb.graph, stacked)
        c.color()

        spilled = s.spill(lines, c.registers, irGraph, tmpcnt)
        didSpill = spilled[2] != tmpcnt
        stacked += spilled[1]
        tmpcnt = spilled[2]
        lines = spilled[0]
        irGraph = spilled[3]
        coloring = c.registers
    # if funcName != 'main':
    #     print(funcName, coloring)
    comp.to_x86(lines, coloring, funcName, graph[-1])
    

for line in comp.finalLines:
    # print(line)
    assem.write(line)
    assem.write('\n')

assem.close()