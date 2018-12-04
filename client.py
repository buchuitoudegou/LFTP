import socket
import threading
import time
import Message
import queue
from Message import restore
from threading import Timer
import random
import Congestion
import os

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
    self.win_size = 204800
    self.last_packet = []
    self.timer = None
    self.size = 2048
    self.src_path = src_path
    self.timeout = 0.1
    self.congestion = Congestion.Congestion()
    self.lock = threading.Lock()

  def establish_conn(self, filename):
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
      DATA = filename.encode('utf8')
      msg = Message.Message(CTL, ACK, SEQ, DATA, 1, self.win_size)
      msg = msg.serialize()
      # print(msg)
      # print(restore(msg))
      my_socket.sendto(msg, (self.des_ip, self.des_port))
      my_socket.close()

    def wait_for_msg():
      """
        description: receive SYN and ACK from server
      """
      my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      my_socket.bind((self.ip_addr, self.port))
      #print(self.port)
      recv = my_socket.recv(self.port)
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
        ack = Message.Message('ACK', msg['SEQ'] + 1, begin_seq + 1, filename.encode('utf8'), 1, 0)
        ack = ack.serialize()
        self.seq = begin_seq + 1
        self.ack = msg['SEQ'] + 1
        my_socket.sendto(ack, (self.des_ip, self.des_port))
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
    msg = Message.Message('ACK', self.ack, self.seq, b'', 0, 0)
    self.last_packet.append(msg)
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.bind((self.ip_addr, self.port))
    msg = msg.serialize()
    my_socket.sendto(msg, (self.des_ip, self.des_port))
    self.timer = Timer(2, self.resend, args=(my_socket, ))
    self.timer.start()
    fd = open(self.src_path, 'ab')
    # recieve packet from server
    while True:
      # ananlize packet
      data = my_socket.recv(self.port)
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
          my_socket.sendto(packet.serialize(), (self.des_ip, self.des_port))
      # whether correct
      if data['ACK'] == self.seq and data['SEQ'] == self.ack:
        print(data)
        # save to the file
        fd.write(data['DATA'])
        self.timer.cancel()
        self.ack = self.ack + data['LEN']
        msg = Message.Message('ACK', self.ack, self.seq, b'', data['LEN'], 0)
        self.last_packet.append(msg)
        msg = msg.serialize()
        my_socket.sendto(msg, (self.des_ip, self.des_port))
        #self.timer = Timer(2, self.resend, args=(my_socket, ))
        #self.timer.start()
      else:
        pass
    fd.close()
    my_socket.close()
      
  def resend(self, my_socket):
    #self.timer.cancel()
    with self.lock:
      self.timeout += 0.2
      self.congestion.update('TIMEOUT')
      for i in range(len(self.last_packet)):
        packet = self.last_packet[i]
        print('resend', packet.serialize())
        try:
          my_socket.sendto(packet.serialize(), (self.des_ip, self.des_port))
        except:
          pass
    # self.last_packet = []
    self.timer = Timer(self.timeout, self.resend, args=(my_socket, ))
    self.timer.start()

  def send_file(self, filename):
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.bind((self.ip_addr, self.port))
    fd = open(filename, 'rb')
    fdata = fd.read(self.size)
    msg = Message.Message('ACK', self.ack, self.seq, fdata, self.size, 0)
    self.seq += self.size
    #print(msg.serialize())
    self.last_packet.append(msg)
    my_socket.sendto(msg.serialize(), (self.des_ip, self.des_port))
    self.timer = Timer(self.timeout, self.resend, args=(my_socket, ))
    self.timer.start()
    count = 1
    while True:
      data = my_socket.recv(self.port)
      data = restore(data)
      with self.lock:
        if len(self.last_packet) != 0:
          idx = 0
          congestion_flag = False
          # marked not pop
          for packet in self.last_packet:
            if packet.SEQ + packet.LEN == data['ACK']:
              self.congestion.update('NEW_ACK')
              self.timeout = 0.1
              congestion_flag = True
              self.last_packet[idx].marked = True
              self.timer.cancel()
              self.timer = Timer(self.timeout, self.resend, args=(my_socket, ))
              self.timer.start()
            idx += 1
          if not congestion_flag:
            self.congestion.update('DUP_ACK')
          delete = -1
          # pop continiously ack
          for packet in self.last_packet:
            if packet.marked == True:
              delete += 1
              self.last_packet.pop(delete)
            else:
              break
        print(data)
        is_finished = False
        c_send = 0
        while self.win_empty() and c_send < self.congestion.cwnd:
          send_data = fd.read(self.size)
          if send_data == b'':
            is_finished = True
            break
          newSeq = self.seq
          newAck = self.ack
          count += 1
          msg = Message.Message('ACK', newAck, newSeq, send_data, self.size, 0)
          self.last_packet.append(msg)
          
          #print(msg.serialize())
          msg = msg.serialize()
          self.seq += self.size
          my_socket.sendto(msg, (self.des_ip, self.des_port))
          c_send += 1

        if is_finished:
          flag = True
          for packet in self.last_packet:
            if packet.marked == False:
              flag = False
              break
          if flag:
            self.close_conn(my_socket)
            print('finished', self.timeout)
            fd.close()
            break         
    my_socket.close()

  def win_empty(self):
    _sum = 0
    for packet in self.last_packet:
      _sum += packet.LEN
    if _sum < self.win_size:
      return True
    else:
      return False


  def close_conn(self, my_socket):
    newSeq = self.seq
    newAck = self.ack
    msg = Message.Message('FIN', newAck, newSeq, b'', 0, 0)
    msg = msg.serialize()
    my_socket.sendto(msg, (self.des_ip, self.des_port))
    my_socket.sendto(msg, (self.des_ip, self.des_port))
    my_socket.sendto(msg, (self.des_ip, self.des_port))
    my_socket.sendto(msg, (self.des_ip, self.des_port))
    my_socket.sendto(msg, (self.des_ip, self.des_port))
    self.timer.cancel()

def multi_thread(port, filename, mode):
  client = Client(port, '127.0.0.1', '127.0.0.1', 8081, filename)
  if mode == 0:
    client.establish_conn(filename + '.UP_LOAD')
    client.send_file(filename)
  else:
    client.establish_conn(filename)
    client.send_request()
  os._exit(0)

if __name__ == '__main__':
  print('LFTP Client is running...')
  mode = int(input('upload(0) or download?(1): '))
  filename = str(input('please input your filename: '))
  t1 = threading.Thread(target=multi_thread, args=(7777, filename, mode))
  t1.start()
