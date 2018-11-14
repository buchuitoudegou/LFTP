import socket
import threading
import time

def wait_for_msg(my_socket):
  while True:
    try:
      recv_msg = my_socket.recv(7707)
      print(recv_msg)
      break
    except:
      pass

def send_msg(my_socket):
  send_addr = ('127.0.0.1', 8081)
  msg = 'Hello!'
  my_socket.sendto(msg.encode('gbk'), send_addr)
  t = threading.Thread(target=wait_for_msg, args=(my_socket, ), daemon=True)
  t.start()
  t.join(timeout=1000)

if __name__ == '__main__':
  my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  my_socket.bind(('127.0.0.1', 7707))
  send_msg(my_socket)
  my_socket.close()