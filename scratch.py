class A:
    to_python = staticmethod(tuple)

a = A()
print(a.to_python([1, 2, 3]))
