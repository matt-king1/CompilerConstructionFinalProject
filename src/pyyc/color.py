class GraphColorer():
    def __init__(self, graph, stack):
        self.graph = graph
        self.registers = {}
        self.priority = {}
        self.notallowed = {}
        self.priority['%eax'] = 0
        self.priority['%ecx'] = 1
        self.priority['%edx'] = 2
        self.priority['%ebx'] = 3
        self.priority['%esi'] = 4
        self.priority['%edi'] = 5
        self.priority['stack'] = 6
        self.registers['%eax'] = '%eax'
        self.registers['%ebx'] = '%ebx'
        self.registers['%ecx'] = '%ecx'
        self.registers['%edx'] = '%edx'
        self.registers['%esi'] = '%esi'
        self.registers['%edi'] = '%edi'
        for var in self.graph.keys():
            self.notallowed[var] = []
            if '%eax' in self.graph.get(var):
                self.notallowed[var].append('%eax')
                self.notallowed[var].append('%ecx')
                self.notallowed[var].append('%edx')
            if var in stack:
                self.notallowed[var].append('stack')

    def color(self):
        while len(self.graph.keys()) + 3 != len(self.registers.keys()): #we have three extra registers
            #find the key with the most notallowed
            max = -1
            maxkey = ''
            for key in self.graph.keys():
                if len(self.notallowed[key]) > max and key not in self.registers.keys():
                    max = len(self.notallowed[key])
                    maxkey = key
            #find the register with the highest priority that is not in notallowed
            min = float('inf')
            minreg = 'stack'
            for reg in self.priority.keys():
                if self.priority[reg] < min and reg not in self.notallowed[maxkey]:
                    min = self.priority[reg]
                    minreg = reg
            
            #add the register to the registers dictionary
            self.registers[maxkey] = minreg
            #add the register to the notallowed list of neighbors
            if minreg == 'stack':
                self.usedstack = True
            else:
                for neighbor in self.graph[maxkey]:
                    self.notallowed[neighbor].append(minreg)
