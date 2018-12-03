import socket
import threading
import time
import Message
import queue
from Message import restore

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
    self.seq = -1
    self.ack = -1
    self.begin = True
    self.win = 10

  def establish_conn(self):
    begin_seq = 100

    def send_syn():
      my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      my_socket.bind((self.ip_addr, self.port))
      CTL = 'SYN'
      ACK = -1
      SEQ = begin_seq
      DATA = 'filename'
      msg = Message.Message(CTL, ACK, SEQ, DATA, 1, self.win)
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
        ack = Message.Message('ACK', msg['SEQ'] + 1, begin_seq + 1, ' ', 1, 0)
        ack = ack.serialize()
        self.seq = begin_seq + 1
        self.ack = msg['SEQ'] + 1
        my_socket.sendto(ack.encode('utf8'), (self.des_ip, self.des_port))
        my_socket.close()
        print('finish connecting')

    send_syn()
    wait_for_msg()
    send_ack()
    
  def send_request(self):
    # data_len = 6
    # # if self.begin:
    # msg = Message.Message('ACK', self.seq, self.ack, 'client', data_len, 0)
    # my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # my_socket.bind((self.ip_addr, self.port))
    # msg = msg.serialize()
    # my_socket.sendto(msg.encode('utf8'), (self.des_ip, self.des_port))
    # my_socket.close()
    # self.ack += data_len
    # for i in range(3):
    #   my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #   my_socket.bind((self.ip_addr, self.port))
    #   data = str(my_socket.recv(self.port))
    #   data = restore(data)
    #   print('client recieve: %s' % data)
    #   if data['ACK'] == self.ack and data['SEQ'] == self.seq:
    #     self.seq += data['LEN']
    #     msg = Message.Message('ACK', self.seq, self.ack, '', 0, 0)
    #     msg = msg.serialize()
    #     my_socket.sendto(msg.encode('utf8'), (self.des_ip, self.des_port))
    #     my_socket.close()
    throw = 0
    msg = Message.Message('ACK', self.ack, self.seq, '', 0, 0)
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.bind((self.ip_addr, self.port))
    msg = msg.serialize()
    my_socket.sendto(msg.encode('utf8'), (self.des_ip, self.des_port))
    # my_socket.close()
    while True:
      data = str(my_socket.recv(self.port))
      data = restore(data)
      if data['CTL'] == 'FIN':
        print('transport complete')
        break
      time.sleep(1)
      if data['SEQ'] == 209 and throw == 0:
        throw += 1
        print('throw', data)
        continue
      if data['ACK'] == self.seq and data['SEQ'] == self.ack:
        print(data)
        self.ack = self.ack + data['LEN']
        msg = Message.Message('ACK', self.ack, self.seq, '', 0, 0)
        msg = msg.serialize()
        my_socket.sendto(msg.encode('utf8'), (self.des_ip, self.des_port))
        # my_socket.close()
      else:
        # my_socket.close()
        pass
    my_socket.close()
      
def multi_thread(port):
  client = Client(port, '127.0.0.1', '127.0.0.1', 8081)
  client.establish_conn()
  client.send_request()  

if __name__ == '__main__':
  t1 = threading.Thread(target=multi_thread, args=(7777, ))
  #t2 = threading.Thread(target=multi_thread, args=(7700, ))
  t1.start()
  #time.sleep(2)
  #t2.start()
