def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


a = list(range(18))

print(list(chunks(a,3)))