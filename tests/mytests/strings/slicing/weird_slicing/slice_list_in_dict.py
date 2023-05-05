# mypy: ignore-errors
d = {'a': [["abc"], 2, 3, 4, 5, 6, 7, 8, 9, 10]}
print(d['a'][0][::])