a = [0] * 5
a[0] = 10
a[4] = a[0] + 7
print(a[4])


a = [0] * 3
i = 1
a[i] = 42
print(a[i])

b = [[0] * 4 for _ in range(3)]
b[2][1] = 55
print(b[2][1])


b = [[0] * 4 for _ in range(3)]
i = 1
j = 2
b[i][j] = 99
print(b[i][j])

a = [0] * 4
i = 0
while i < 4:
    a[i] = i + 10
    i = i + 1

print(a[2])

