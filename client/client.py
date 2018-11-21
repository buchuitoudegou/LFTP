import socket
import threading
import time
'''
def wait_for_msg(my_socket):
  recv_msg = my_socket.recv(7707)
  print(recv_msg)

def send_msg(my_socket):
  send_addr = ('127.0.0.1', 8081)
  msg = 'Hello!'
  my_socket.sendto(msg.encode('gbk'), send_addr)
  t = threading.Thread(target=wait_for_msg, args=(my_socket, ), daemon=True)
  t.start()
  t.join(timeout=1000)
'''
class Client():
  def __init__(self, port, ip_addr):
  """
  init a client socket params
  :params port: port of the socket
  :type port: Integer
  :params ip_addr: ip address of socket
  :type ip_addr: string
  """
    self.port = port
    self.ip_addr = ip_addr

  def establish_conn(self,des_ip, des_port):
    def send_syn():
      socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      soket.bind((self.ip_addr, self.port))
      syn = 
  



if __name__ == '__main__':
  my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  my_socket.bind(('127.0.0.1', 7707))
  send_msg(my_socket)
  my_socket.close()