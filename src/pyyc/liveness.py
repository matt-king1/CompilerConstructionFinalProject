import re

class LivenessAnalyzer():
    def __init__(self, ir):
        self.liveness = [set() for _ in range(len(ir) + 1)]
        self.visited = set()
        self.livenessAtJumps = {}

    def analyze(self, graph, ir, idx, args, funcName, incLiveness=set()):
        if idx < 0:
            return
        self.livenessAtJumps.update({idx:incLiveness})
        self.visited.add(idx)
        node = graph[idx]
        for i in reversed(range(len(node[0]))):
            self.liveness[node[0][i][-1]] = self.liveness[node[0][i][-1]].union(incLiveness)
            match node[0][i][0]:
                case 'call':
                    if node[0][i][3] !=  None and node[0][i][3] in self.liveness[node[0][i][-1]]:
                        self.liveness[node[0][i][-1]].remove(node[0][i][3])
                    unionSet = set([i for i in node[0][i][2] if isinstance(i, str)]) \
                        if node[0][i][1] != 'create_closure' else \
                            set([i for i in node[0][i][2][1::] if isinstance(i, str)])
                    if node[0][i][1][0:3] == 'tmp':
                        unionSet.add(node[0][i][1])
                    self.liveness[node[0][i][-1]] = self.liveness[node[0][i][-1]].union(unionSet)
                case 'movl':
                    if node[0][i][2] in self.liveness[node[0][i][-1]]:
                        self.liveness[node[0][i][-1]].remove(node[0][i][2])
                    if isinstance(node[0][i][1], str):
                        self.liveness[node[0][i][-1]].add(node[0][i][1])
                case 'addl':
                    self.liveness[node[0][i][-1]].add(node[0][i][2])
                    if isinstance(node[0][i][1], str):
                        self.liveness[node[0][i][-1]].add(node[0][i][1])
                case 'negl':
                    self.liveness[node[0][i][-1]].add(node[0][i][1])
                case 'setne':
                    if node[0][i][1] in self.liveness[node[0][i][-1]]:
                        self.liveness[node[0][i][-1]].remove(node[0][i][1])
                case 'sete':
                    if node[0][i][1] in self.liveness[node[0][i][-1]]:
                        self.liveness[node[0][i][-1]].remove(node[0][i][1])
                case 'cmpl':
                    if isinstance(node[0][i][1], str):
                        self.liveness[node[0][i][-1]].add(node[0][i][1])
                    if isinstance(node[0][i][2], str):
                        self.liveness[node[0][i][-1]].add(node[0][i][2])
                case 'not':
                    if node[0][i][2] in self.liveness[node[0][i][-1]]:
                        self.liveness[node[0][i][-1]].remove(node[0][i][2])
                    self.liveness[node[0][i][-1]].add(node[0][i][1])
                case 'return':
                    self.liveness[node[0][i][-1]].add(node[0][i][1])
                case 'jmp':
                    ...
                case 'jne':
                    ...
                case 'je':
                    ...
                case _:
                    m = re.search('(ifEnd\d*)|(whileEnd\d*)|(else\d*)|(then\d*)|(whiletag\d*)', node[0][i][0])
                    if not m:
                        print("invalid instruction during liveness analysis: " + node[0][i][0])
                        exit(1)
            incLiveness = self.liveness[node[0][i][-1]]
        # if self.livenessAtJumps.get(idx, None) != incLiveness:
        #     # print(idx, self.livenessAtJumps.get(idx, None), incLiveness)
        #     self.livenessAtJumps.update({idx:incLiveness})
        # for line in node[0]:
        #     print(line)
        # print(idx, incLiveness)
        for i in node[1]:
            if self.livenessAtJumps.get(i, None) != incLiveness or i not in self.visited:
                self.analyze(graph, ir, i, args, funcName, incLiveness=incLiveness)
        self.visited.add(idx)
        if len(self.liveness[0] - args) > 0 and idx == 0 and len(self.visited) == len(graph):
            print('error: reference to unassigned variable: ', self.liveness[0] - args, ' in ', funcName)
            exit(1)
# # test
# if __name__ == '__main__':
#     lines = [
#         ['movl', 4, 'z'],
#         ['movl', 0, 'w'],
#         ['movl', 1, 'z'],
#         ['movl', 'w', 'x'],
#         ['addl', 'z', 'x'],
#         ['movl', 'w', 'y'],
#         ['addl', 'x', 'y'],
#         ['movl', 'y', 'w'],
#         ['addl', 'x', 'w']
#     ]
#     liveness = LivenessAnalyzer(lines)
#     liveness.analyze()
#     for i in liveness.liveness:
#         print(i)
