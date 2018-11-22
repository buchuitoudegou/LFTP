def f():
  a = 1
  def b():
    return a
  return b

print(f()())