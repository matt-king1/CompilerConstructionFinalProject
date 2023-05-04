import re

class GraphBuilder():
    def __init__(self, ir, liveness):
        self.ir = ir
        self.liveness = liveness
        self.graph = dict()
        self.graph['%eax'] = set()
        self.graph['%ecx'] = set()
        self.graph['%edx'] = set()

    def build(self, args):
        for arg in args:
            if arg not in self.graph.keys():
                self.graph[arg] = set()
            self.graph[arg] = self.graph[arg].union(self.liveness[0])
            for var in self.liveness[0]:
                if var not in self.graph:
                    self.graph[var] = set()
                self.graph[var].add(arg)
        for i in range(len(self.ir)):
            match self.ir[i][0]:
                case 'call':
                    self.graph['%eax'] = self.graph['%eax'].union(self.liveness[i+1])
                    self.graph['%ecx'] = self.graph['%ecx'].union(self.liveness[i+1])
                    self.graph['%edx'] = self.graph['%edx'].union(self.liveness[i+1])
                    for var in self.liveness[i+1]:
                        if var not in self.graph:
                            self.graph[var] = set()
                        self.graph[var].add('%eax')
                        self.graph[var].add('%ecx')
                        self.graph[var].add('%edx')
                    if self.ir[i][3] != None:
                        if self.ir[i][3] not in self.graph:
                            self.graph[self.ir[i][3]] = set()
                        self.graph[self.ir[i][3]] = self.graph[self.ir[i][3]].union(self.liveness[i+1])
                        for var in self.liveness[i+1]:
                            if var not in self.graph:
                                self.graph[var] = set()
                            self.graph[var].add(self.ir[i][3])
                case 'addl':
                    if self.ir[i][2] not in self.graph:
                        self.graph[self.ir[i][2]] = set()
                    self.graph[self.ir[i][2]] = self.graph[self.ir[i][2]].union(self.liveness[i+1])
                    for var in self.liveness[i+1]:
                        if var not in self.graph:
                            self.graph[var] = set()
                        self.graph[var].add(self.ir[i][2])
                case 'negl':
                    if self.ir[i][1] not in self.graph:
                        self.graph[self.ir[i][1]] = set()
                    self.graph[self.ir[i][1]] = self.graph[self.ir[i][1]].union(self.liveness[i+1])
                    for var in self.liveness[i+1]:
                        if var not in self.graph:
                            self.graph[var] = set()
                        self.graph[var].add(self.ir[i][1])
                case 'movl':
                    if self.ir[i][2] not in self.graph:
                        self.graph[self.ir[i][2]] = set()
                    self.graph[self.ir[i][2]] = self.graph[self.ir[i][2]].union(self.liveness[i+1])
                    if self.ir[i][1] in self.graph[self.ir[i][2]]:
                        self.graph[self.ir[i][2]].remove(self.ir[i][1])
                    for var in self.liveness[i+1]:
                        if var not in self.graph:
                            self.graph[var] = set()
                        self.graph[var].add(self.ir[i][2])
                case 'setne':
                    if self.ir[i][1] not in self.graph:
                        self.graph[self.ir[i][1]] = set()
                    self.graph[self.ir[i][1]] = self.graph[self.ir[i][1]].union(self.liveness[i+1])
                    for var in self.liveness[i+1]:
                        if var not in self.graph:
                            self.graph[var] = set()
                        self.graph[var].add(self.ir[i][1])
                        if var != self.ir[i][1]:
                            self.graph['%eax'].add(self.ir[i][1])
                            self.graph[var].add('%eax') 
                case 'sete':
                    if self.ir[i][1] not in self.graph:
                        self.graph[self.ir[i][1]] = set()
                    self.graph[self.ir[i][1]] = self.graph[self.ir[i][1]].union(self.liveness[i+1])
                    for var in self.liveness[i+1]:
                        if var not in self.graph:
                            self.graph[var] = set()
                        self.graph[var].add(self.ir[i][1])
                        if var != self.ir[i][1]:
                            self.graph['%eax'].add(self.ir[i][1])
                            self.graph[var].add('%eax')
                case 'not':
                    if self.ir[i][1] not in self.graph:
                        self.graph[self.ir[i][1]] = set()
                    if self.ir[i][2] not in self.graph:
                        self.graph[self.ir[i][2]] = set()
                    self.graph[self.ir[i][2]] = self.graph[self.ir[i][2]].union(self.liveness[i+1])
                    for var in self.liveness[i+1]:
                        if var not in self.graph:
                            self.graph[var] = set()
                        self.graph[var].add(self.ir[i][2])
                        if var != self.ir[i][2]:
                            self.graph['%eax'].add(self.ir[i][1])
                            self.graph[var].add('%eax')
                case 'return':
                    ...
                case 'cmpl':
                    ...
                case 'jne':
                    ...
                case 'je':
                    ...
                case 'jmp':
                    ...
                case _: # default case
                    m = re.search('(ifEnd\d*)|(whileEnd\d*)|(else\d*)|(then\d*)|(whiletag\d*)', self.ir[i][0])
                    if not m:
                        print("invalid instruction during graph building: " + self.ir[i][0])
                        exit(1)
        for key in self.graph.keys():
            for val in self.graph[key]:
                self.graph[val].add(key)
