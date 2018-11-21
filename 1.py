import queue

a = queue.Queue()
a.put(1)
a.put(2)
print(a.get())
print(a.get())