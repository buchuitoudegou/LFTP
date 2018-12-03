import Message
from threading import Timer
import FileManage
import threading

class Server():
  def __init__(self, ip, port):
    self.ip = ip
    self.port = port
    self.conn_table = dict()
    self.connecting = dict()
    self.closing = dict()
    self.file_manage = FileManage.FileManage()
    self.begin_seq = 200
    self.size = 4
    self.throw = 0
  
  def establish_conn_1(self, client_ip, client_port, data, my_socket):
    def send_syn():
      if data['CTL'] == 'SYN':
        self.file_manage.load_resource((client_ip, client_port), data['DATA'], 0)
        CTL = 'SYN+ACK'
        SEQ = self.begin_seq
        ACK = data['SEQ'] + 1
        DATA = ' '
        msg = Message.Message(CTL, ACK, SEQ, DATA, 1, 0)
        msg = msg.serialize()
        my_socket.sendto(msg.encode('utf8'), (client_ip, client_port))
        self.connecting[(client_ip, client_port)] = data['WIN']
    send_syn()
    print(self.connecting)
    print(self.conn_table)

  def establish_conn_2(self, client_ip, client_port, data, my_socket):
    check_seq = self.begin_seq + 1
    print(data)
    timer = Timer(10, self.resend, args=((client_ip, client_port), my_socket, ))
    lock = threading.Lock()
    if data['CTL'] == 'ACK' and data['ACK'] == check_seq:
      self.conn_table[(client_ip, client_port)] = {\
        'SEQ': data['ACK'], \
        'ACK': data['SEQ'],\
        'WIN_SIZE': self.connecting[(client_ip, client_port)], \
        'IDX': 0,\
        'WIN': [],\
        'TIMEOUT': timer,\
        'LOCK': lock\
      }
      timer.start()
      self.connecting.pop((client_ip, client_port))
    print(self.connecting)
    print(self.conn_table)

  def resend(self, client_address, my_socket):
    print('resend:')
    for packet in self.conn_table[client_address]['WIN']:
      msg = packet.serialize()
      print(msg)
      my_socket.sendto(msg.encode('utf8'), client_address)
    print('resend complete')
    self.conn_table[client_address]['TIMEOUT'] = Timer(10, self.resend, args=(client_address, my_socket, ))
    self.conn_table[client_address]['TIMEOUT'].start()

  def handler(self, client_address, data, my_socket):
    if not client_address in self.conn_table:
      return
    lock = self.conn_table[client_address]['LOCK']
    lock.acquire()
    print('lock acquire')
    if len(self.conn_table[client_address]['WIN']) != 0:
      idx = 0
      # marked not pop
      for packet in self.conn_table[client_address]['WIN']:
        if packet.SEQ + packet.LEN == data['ACK']:
          self.conn_table[client_address]['WIN'][idx].marked = True
          self.conn_table[client_address]['TIMEOUT'].cancel()
          self.conn_table[client_address]['TIMEOUT'] = Timer(10, self.resend, args=(client_address, my_socket, ))
          self.conn_table[client_address]['TIMEOUT'].start()
        idx += 1
      delete = -1
      # pop contuniously ack
      for packet in self.conn_table[client_address]['WIN']:
        if packet.marked == True:
          delete += 1
          self.conn_table[client_address]['WIN'].pop(delete)
        else:
          break
    print(data)
    is_finished = False
    while self.win_empty(client_address):
      send_data = self.file_manage.load_resource(client_address, '', self.size)
      if send_data == '':
        is_finished = True
        break
      begin = self.conn_table[client_address]['IDX']
      newSeq = self.conn_table[client_address]['SEQ']
      newAck = self.conn_table[client_address]['ACK']
      msg = Message.Message('ACK', newAck, newSeq, send_data, self.size, 0)
      self.conn_table[client_address]['WIN'].append(msg)
      print(msg.serialize())
      msg = msg.serialize()
      self.conn_table[client_address]['IDX'] += self.size
      self.conn_table[client_address]['SEQ'] += self.size
      my_socket.sendto(msg.encode('utf8'), client_address)

    if is_finished:
      flag = True
      for packet in self.conn_table[client_address]['WIN']:
        if packet.marked == False:
          flag = False
          break
      if flag:
        self.close_conn(client_address, my_socket)

    if client_address in self.conn_table:
      print(self.conn_table[client_address])
    else:
      print(self.conn_table)

    lock.release()

  def win_empty(self, client_address):
    win = self.conn_table[client_address]['WIN']
    total = 0
    for packet in win:
      total += packet.LEN
    if total < self.conn_table[client_address]['WIN_SIZE']:
      return True
    else:
      return False

  def close_conn(self, client_address, my_socket):
    if client_address in self.conn_table:
      begin = self.conn_table[client_address]['IDX']
      newSeq = self.conn_table[client_address]['SEQ']
      newAck = self.conn_table[client_address]['ACK']
      msg = Message.Message('FIN', newAck, newSeq, '', 0, 0)
      msg = msg.serialize()
      my_socket.sendto(msg.encode('utf8'), client_address)
      self.conn_table[client_address]['TIMEOUT'].cancel()
      self.conn_table.pop(client_address)
      self.file_manage.source_table.pop(client_address)