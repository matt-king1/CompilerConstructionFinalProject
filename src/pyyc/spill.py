import re

class Spiller():
    def spill(self, ir, coloring, graph, tmpcount):
        if len(ir) == 0:
            return ([], [], 0, [])
        spill_code = []
        spilled = []
        new_graph = [[[], set()] for _ in range(len(graph))]
        # for irs in graph:
        #     for row in irs[0]:
        #         print(row)
        #     print(irs[1])
        #     print(' ')
        block = 0
        lenBlocks = [len(i[0]) for i in graph]
        blocksum = lenBlocks[0]
        lineNumber = 0
        for i in range(len(ir)):
            if i == blocksum:
                new_graph[block][1] = graph[block][1] 
                block += 1
                blocksum += lenBlocks[block]
            match ir[i][0]:
                case 'movl':
                    if not isinstance(ir[i][1], int):
                        if coloring[ir[i][1]] == coloring[ir[i][2]] and coloring[ir[i][1]] == 'stack':
                            # if coloring[ir[i][1]] != 'stack':
                            #     continue
                            # else:
                            new_graph[block][0].append(['movl', ir[i][1], 'tmp' + str(tmpcount), lineNumber])
                            spill_code.append(new_graph[block][0][-1])
                            lineNumber += 1
                            new_graph[block][0].append(['movl', 'tmp' + str(tmpcount), ir[i][2], lineNumber])
                            spill_code.append(new_graph[block][0][-1])
                            spilled.append('tmp' + str(tmpcount))
                            lineNumber += 1
                            tmpcount += 1
                        else:
                            new_graph[block][0].append([*ir[i][0:3], lineNumber])
                            spill_code.append(new_graph[block][0][-1])
                            lineNumber+=1
                    else:
                        new_graph[block][0].append([*ir[i][0:3], lineNumber])
                        spill_code.append(new_graph[block][0][-1])
                        lineNumber += 1
                case 'addl':
                    if not isinstance(ir[i][1], int):
                        if coloring[ir[i][1]] == coloring[ir[i][2]] and coloring[ir[i][1]] == 'stack':
                            if coloring[ir[i][1]] != 'stack':
                                new_graph[block][0].append([*ir[i][0:3], lineNumber])
                                spill_code.append(new_graph[block][0][-1])
                                lineNumber += 1
                            else:
                                new_graph[block][0].append(['movl', ir[i][1], 'tmp' + str(tmpcount), lineNumber])
                                spill_code.append(new_graph[block][0][-1])
                                lineNumber += 1
                                new_graph[block][0].append(['addl', 'tmp' + str(tmpcount), ir[i][2], lineNumber])
                                spill_code.append(new_graph[block][0][-1])
                                spilled.append('tmp' + str(tmpcount))
                                lineNumber += 1
                                tmpcount += 1 
                        else:
                            new_graph[block][0].append([*ir[i][0:3], lineNumber])
                            spill_code.append(new_graph[block][0][-1])
                            lineNumber += 1
                    else:
                        new_graph[block][0].append([*ir[i][0:3], lineNumber])
                        spill_code.append(new_graph[block][0][-1])
                        lineNumber += 1
                case 'negl':
                    if coloring[ir[i][1]] == 'stack':
                        new_graph[block][0].append(['movl', ir[i][1], 'tmp' + str(tmpcount), lineNumber])
                        spill_code.append(new_graph[block][0][-1])
                        lineNumber += 1
                        new_graph[block][0].append(['negl', 'tmp' + str(tmpcount), lineNumber])
                        spill_code.append(new_graph[block][0][-1])
                        lineNumber += 1
                        new_graph[block][0].append(['movl', 'tmp' + str(tmpcount), ir[i][1], lineNumber])
                        spill_code.append(new_graph[block][0][-1])
                        spilled.append('tmp' + str(tmpcount))
                        lineNumber += 1
                        tmpcount += 1
                    else:
                        new_graph[block][0].append([*ir[i][0:2], lineNumber])
                        spill_code.append(new_graph[block][0][-1])
                        lineNumber += 1
                case 'call':
                    for j in range(len(ir[i][2])):
                        source = ir[i][2][j]
                        if coloring.get(source, source) == 'stack':
                            new_graph[block][0].append(['movl', source, 'tmp' + str(tmpcount), lineNumber])
                            spill_code.append(new_graph[block][0][-1])
                            lineNumber += 1
                            spilled.append('tmp' + str(tmpcount))
                            ir[i][2][j] = 'tmp' + str(tmpcount)
                            tmpcount += 1
                    new_graph[block][0].append([*ir[i][0:4], lineNumber])
                    spill_code.append(new_graph[block][0][-1])
                    lineNumber += 1
                case 'cmpl':
                    bothStack = coloring.get(ir[i][1]) == 'stack' and coloring.get(ir[i][2]) == 'stack'
                    if bothStack:
                        if ir[i][1] == ir[i][2]:
                            new_graph[block][0].append(['movl', ir[i][1], 'tmp' + str(tmpcount), lineNumber])
                            spill_code.append(new_graph[block][0][-1])
                            lineNumber += 1
                            new_graph[block][0].append(['cmpl', 'tmp' + str(tmpcount), 'tmp' + str(tmpcount), lineNumber])
                            spill_code.append(new_graph[block][0][-1])
                            spilled.append('tmp' + str(tmpcount))
                            lineNumber += 1
                            tmpcount += 1
                        else:
                            new_graph[block][0].append(['movl', ir[i][1], 'tmp' + str(tmpcount), lineNumber])
                            spill_code.append(new_graph[block][0][-1])
                            lineNumber += 1
                            new_graph[block][0].append(['cmpl', 'tmp' + str(tmpcount), ir[i][2], lineNumber])
                            spill_code.append(new_graph[block][0][-1])
                            spilled.append('tmp' + str(tmpcount))
                            lineNumber += 1
                            tmpcount += 1
                    elif isinstance(ir[i][2], int):
                        if isinstance(ir[i][1], int):
                            new_graph[block][0].append(['movl', ir[i][2], 'tmp' + str(tmpcount), lineNumber])
                            spill_code.append(new_graph[block][0][-1])
                            lineNumber += 1
                            new_graph[block][0].append(['cmpl', 'tmp' + str(tmpcount), ir[i][1], lineNumber])
                            spill_code.append(new_graph[block][0][-1])
                            spilled.append('tmp' + str(tmpcount))
                            lineNumber += 1
                            tmpcount += 1
                        else:
                            tmpaddr = ir[i][2]
                            ir[i][2] = ir[i][1]
                            ir[i][1] = tmpaddr
                            new_graph[block][0].append([*ir[i][0:3], lineNumber])
                            spill_code.append(new_graph[block][0][-1])
                            lineNumber += 1
                    else:
                        new_graph[block][0].append([*ir[i][0:3], lineNumber])
                        spill_code.append(new_graph[block][0][-1])
                        lineNumber += 1
                case 'not':
                    if isinstance(ir[i][1], int) or coloring.get(ir[i][2]) == 'stack':
                        firstOp = ir[i][1]
                        secondOp = ir[i][2]
                        if isinstance(ir[i][1], int):
                            firstOp = 'tmp' + str(tmpcount)
                            new_graph[block][0].append(['movl', ir[i][1], firstOp, lineNumber])
                            spill_code.append(new_graph[block][0][-1])
                            spilled.append(firstOp)
                            lineNumber += 1
                            tmpcount += 1
                        if coloring.get(ir[i][2]) == 'stack':
                            secondOp = 'tmp' + str(tmpcount)
                            new_graph[block][0].append(['movl', ir[i][2], secondOp, lineNumber])
                            spill_code.append(new_graph[block][0][-1])
                            spilled.append(secondOp)
                            lineNumber += 1
                            tmpcount += 1
                        new_graph[block][0].append(['not', firstOp, secondOp, lineNumber])
                        spill_code.append(new_graph[block][0][-1])
                        lineNumber += 1
                        if coloring.get(ir[i][2]) == 'stack':
                            new_graph[block][0].append(['movl', secondOp, ir[i][2], lineNumber])
                            spill_code.append(new_graph[block][0][-1])
                            lineNumber += 1
                    else:
                        new_graph[block][0].append([*ir[i][0:3], lineNumber])
                        spill_code.append(new_graph[block][0][-1])
                        lineNumber += 1
                case 'sete':
                    if coloring.get(ir[i][1]) == 'stack':
                        new_graph[block][0].append(['sete', 'tmp' + str(tmpcount), lineNumber])
                        spill_code.append(new_graph[block][0][-1])
                        lineNumber += 1
                        new_graph[block][0].append(['movl', 'tmp' + str(tmpcount), ir[i][1], lineNumber])
                        spill_code.append(new_graph[block][0][-1])
                        spilled.append('tmp' + str(tmpcount))
                        lineNumber += 1
                        tmpcount += 1
                    else:
                        new_graph[block][0].append([*ir[i][0:2], lineNumber])
                        spill_code.append(new_graph[block][0][-1])
                        lineNumber += 1
                case 'setne':
                    if coloring.get(ir[i][1]) == 'stack':
                        new_graph[block][0].append(['setne', 'tmp' + str(tmpcount), lineNumber])
                        spill_code.append(new_graph[block][0][-1])
                        lineNumber += 1
                        new_graph[block][0].append(['movl', 'tmp' + str(tmpcount), ir[i][1], lineNumber])
                        spill_code.append(new_graph[block][0][-1])
                        spilled.append('tmp' + str(tmpcount))
                        lineNumber += 1
                        tmpcount += 1
                    else:
                        new_graph[block][0].append([*ir[i][0:2], lineNumber])
                        spill_code.append(new_graph[block][0][-1])
                        lineNumber += 1
                case 'jne':
                    new_graph[block][0].append([*ir[i][0:2], lineNumber])
                    spill_code.append(new_graph[block][0][-1])
                    lineNumber += 1
                case 'je':
                    new_graph[block][0].append([*ir[i][0:2], lineNumber])
                    spill_code.append(new_graph[block][0][-1])
                    lineNumber += 1
                case 'jmp':
                    new_graph[block][0].append([*ir[i][0:2], lineNumber])
                    spill_code.append(new_graph[block][0][-1])
                    lineNumber += 1
                case 'return':
                    new_graph[block][0].append([*ir[i][0:2], lineNumber])
                    spill_code.append(new_graph[block][0][-1])
                    lineNumber += 1
                case _:
                    m = re.search('(ifEnd\d*)|(whileEnd\d*)|(else\d*)|(then\d*)|(whiletag\d*)', ir[i][0])
                    if not m:
                        print("invalid instruction during spilling: " + ir[i][0])
                        exit(1)
                    else:
                        new_graph[block][0].append([*ir[i][0:1], lineNumber])
                        spill_code.append(new_graph[block][0][-1])
                        lineNumber += 1
        new_graph[-1][1] = graph[-1][1] 
        # for irs in new_graph:
        #     for row in irs[0]:
        #         print(row)
        #     print(irs[1])
        #     print(' ')
        return (spill_code, spilled, tmpcount, new_graph)
