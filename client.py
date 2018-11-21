import socket
import threading
import time
from Message import Message, restore
import queue

class Client():
  def __init__(self, port, ip_addr, des_ip, des_port):
    """
    init a client socket params
    :params port: port of the socket
    :type port: Integer
    :params ip_addr: ip address of socket
    :type ip_addr: string
    """
    self.port = port
    self.ip_addr = ip_addr
    self.des_ip = des_ip
    self.des_port = des_port
    self.msg_queue = queue.Queue()

  def establish_conn(self):
    begin_seq = 100

    def send_syn():
      my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      my_socket.bind((self.ip_addr, self.port))
      CTL = 'SYN'
      ACK = -1
      SEQ = begin_seq
      DATA = ''
      msg = Message(CTL, ACK, SEQ, DATA)
      msg = msg.serialize()
      my_socket.sendto(msg.encode('utf8'), (self.des_ip, self.des_port))
      my_socket.close()

    def wait_for_msg():
      my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      my_socket.bind((self.ip_addr, self.port))
      print(self.port)
      recv = str(my_socket.recv(self.port))
      print(recv)
      self.msg_queue.put(recv)
      my_socket.close()

    def send_ack():
      my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      my_socket.bind((self.ip_addr, self.port))
      msg = self.msg_queue.get()
      msg = restore(msg)
      if msg['CTL'] == 'SYN+ACK' and msg['ACK'] == begin_seq + 1:
        ack = Message('ACK', msg['SEQ'] + 1, -1, '')
        ack = ack.serialize()
        my_socket.sendto(ack.encode('utf8'), (self.des_ip, self.des_port))
        my_socket.close()

    send_syn()
    wait_for_msg()
    send_ack()
    
  

if __name__ == '__main__':
  client = Client(7777, '127.0.0.1', '127.0.0.1', 8081)
  client.establish_conn()

# if __name__ == '__main__':
#   my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#   my_socket.bind(('127.0.0.1', 7707))
#   send_msg(my_socket)
#   my_socket.close()