# Intensive slicing test case

nested_list = [
    [0, 1, 2, 3, 4],
    [5, 6, 7, 8, 9],
    [10, 11, 12, 13, 14],
    [15, 16, 17, 18, 19],
    [20, 21, 22, 23, 24]
]

# Perform slicing operations
result1 = nested_list[::2]
result2 = nested_list[::-1]
result3 = nested_list[1:4:2]
result5 = nested_list[1:4][::-1]

# Print results and expected outcomes
print(result1)
print(result2)
print(result3)
print(result5)
