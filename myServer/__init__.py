import Message
from threading import Timer

class Server():
  def __init__(self, ip, port):
    self.ip = ip
    self.port = port
    self.conn_table = dict()
    self.connecting = dict()
    self.closing = dict()
    self.begin_seq = 200
    self.send_data = 'aaaabbbbccccddddeeee'
    self.size = 4
    self.throw = 0
  
  def establish_conn_1(self, client_ip, client_port, data, my_socket):
    # print(data)
    def send_syn():
      if data['CTL'] == 'SYN':
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
    if data['CTL'] == 'ACK' and data['ACK'] == check_seq:
      self.conn_table[(client_ip, client_port)] = {\
        'SEQ': data['ACK'], \
        'ACK': data['SEQ'],\
        'WIN_SIZE': self.connecting[(client_ip, client_port)], \
        'IDX': 0,\
        'WIN': [],\
        'TIMEOUT': timer\
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
      for packet in self.conn_table[client_address]['WIN']:
        if packet.marked == True:
          delete += 1
          self.conn_table[client_address]['WIN'].pop(delete)
        else:
          break
    print(data) 
    while self.win_empty(client_address):
      if self.conn_table[client_address]['IDX'] == len(self.send_data):
        break
      begin = self.conn_table[client_address]['IDX']
      newSeq = self.conn_table[client_address]['SEQ']
      newAck = self.conn_table[client_address]['ACK']
      msg = Message.Message('ACK', newAck, newSeq, \
      self.send_data[begin:begin+self.size], self.size, 0)
      self.conn_table[client_address]['WIN'].append(msg)
      print(msg.serialize())
      msg = msg.serialize()
      print('send-data: %d' % self.conn_table[client_address]['IDX'])
      self.conn_table[client_address]['IDX'] += self.size
      self.conn_table[client_address]['SEQ'] += self.size
      my_socket.sendto(msg.encode('utf8'), client_address)

    if self.conn_table[client_address]['IDX'] == len(self.send_data):
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
    begin = self.conn_table[client_address]['IDX']
    newSeq = self.conn_table[client_address]['SEQ']
    newAck = self.conn_table[client_address]['ACK']
    msg = Message.Message('FIN', newAck, newSeq, '', 0, 0)
    msg = msg.serialize()
    my_socket.sendto(msg.encode('utf8'), client_address)
    self.conn_table[client_address]['TIMEOUT'].cancel()
    self.conn_table.pop(client_address)