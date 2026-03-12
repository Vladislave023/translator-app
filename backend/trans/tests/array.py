a = [0] * 5
a[0] = 10
a[4] = a[0] + 7
print(a[4])

ab = [0] * 3
i = 1
ab[i] = 42
print(ab[i])

bc = [[0] * 4 for _ in range(3)]
bc[2][1] = 55
print(bc[2][1])

bf = [[0] * 4 for _ in range(3)]
i = 1
j = 2
bf[i][j] = 99
print(bf[i][j])

arr = [0] * 4
i = 0
while i < 4:
    arr[i] = i + 10
    i = i + 1

print(arr[2])