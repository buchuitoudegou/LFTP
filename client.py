import socket
import threading
import time
import Message
import queue
from Message import restore
from threading import Timer
import random

class Client():
  def __init__(self, port, ip_addr, des_ip, des_port, src_path):
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
    self.win_size = 30000
    self.last_packet = []
    self.timer = None
    self.src_path = src_path

  def establish_conn(self):
    """
    description: establish connection with server
    return: None
    """
    # initial seq of client request
    begin_seq = 100
    def send_syn():
      """
      description:send SYN to server
      """
      my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      my_socket.bind((self.ip_addr, self.port))
      CTL = 'SYN'
      ACK = -1
      SEQ = begin_seq
      DATA = 'data.txt'
      msg = Message.Message(CTL, ACK, SEQ, DATA, 1, self.win_size)
      msg = msg.serialize()
      # print(msg)
      # print(restore(msg))
      my_socket.sendto(msg.encode('utf8'), (self.des_ip, self.des_port))
      my_socket.close()

    def wait_for_msg():
      """
        description: receive SYN and ACK from server
      """
      my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      my_socket.bind((self.ip_addr, self.port))
      #print(self.port)
      recv = my_socket.recv(self.port)
      recv = recv.decode('utf8')
      print(recv)
      self.msg_queue.put(recv)
      my_socket.close()

    def send_ack():
      """
        description: send ACK to server
      """
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
    """
      description: send request and gain resource
      return: None
    """
    # analog packet loss
    self.timer = None
    # first request
    msg = Message.Message('ACK', self.ack, self.seq, '', 0, 0)
    self.last_packet.append(msg)
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.bind((self.ip_addr, self.port))
    msg = msg.serialize()
    my_socket.sendto(msg.encode('utf8'), (self.des_ip, self.des_port))
    self.timer = Timer(2, self.resend, args=(my_socket, ))
    self.timer.start()
    fd = open(self.src_path, 'a')
    # recieve packet from server
    while True:
      # ananlize packet
      data = my_socket.recv(self.port).decode('utf8')
      print(data)
      data = restore(data)
      idx = 0
      # if transport complete
      if data['CTL'] == 'FIN':
        self.timer.cancel()
        print('transport complete')
        break
      # analog packet loss
      if random.random() > 0.9:
        print('throw', data)
        continue
      idx = 0
      for packet in self.last_packet:
        if packet.ACK == data['SEQ'] + data['LEN']:
          print('resend', packet)
          my_socket.sendto(packet.serialize().encode('utf8'), (self.des_ip, self.des_port))
      # whether correct
      if data['ACK'] == self.seq and data['SEQ'] == self.ack:
        print(data)
        # save to the file
        fd.write(data['DATA'])
        self.timer.cancel()
        self.ack = self.ack + data['LEN']
        msg = Message.Message('ACK', self.ack, self.seq, '', data['LEN'], 0)
        self.last_packet.append(msg)
        msg = msg.serialize()
        my_socket.sendto(msg.encode('utf8'), (self.des_ip, self.des_port))
        #self.timer = Timer(2, self.resend, args=(my_socket, ))
        #self.timer.start()
      else:
        pass
    fd.close()
    my_socket.close()
      
  def resend(self, my_socket):
    for i in range(len(self.last_packet) - 1, -1, -1):
      packet = self.last_packet[i]
      print('resend', packet.serialize())
      try:
        my_socket.sendto(packet.serialize().encode('utf8'), (self.des_ip, self.des_port))
      except:
        pass
    # self.last_packet = []
    self.timer = Timer(2, self.resend, args=(my_socket, ))
    self.timer.start()

def multi_thread(port):
  client = Client(port, '127.0.0.1', '127.0.0.1', 8081, 'rev.txt')
  client.establish_conn()
  client.send_request()  

if __name__ == '__main__':
  t1 = threading.Thread(target=multi_thread, args=(7777, ))
  #t2 = threading.Thread(target=multi_thread, args=(7700, ))
  t1.start()
  #time.sleep(2)
  #t2.start()
