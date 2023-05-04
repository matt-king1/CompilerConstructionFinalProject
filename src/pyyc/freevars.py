import ast
from ast import *

from functools import reduce

def free_vars(n):
    if isinstance(n, ast.Const):
        return set([])
    elif isinstance(n, ast.Name):
        if n.name == 'True' or n.name == 'False':
            return set([])
        else:
            return set([n.name])
    elif isinstance(n, ast.Add):
        return free_vars(n.left) | free_vars(n.right)
    elif isinstance(n, ast.Call): #CallFunc?
        fv_args = [free_vars(e) for e in n.args]
        free_in_args = reduce(lambda x, y: x | y, fv_args, set([]))
        return free_vars(n.func) | free_in_args
    elif isinstance(n, ast.Lambda):
        return free_vars(n.body) - set([arg.id for arg in n.args])