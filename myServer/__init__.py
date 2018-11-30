import Message

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
  
  def establish_conn_1(self, client_ip, client_port, data, my_socket):
    # print(data)
    def send_syn():
      if data['CTL'] == 'SYN':
        CTL = 'SYN+ACK'
        SEQ = self.begin_seq
        ACK = data['SEQ'] + 1
        DATA = ''
        msg = Message.Message(CTL, ACK, SEQ, DATA, 1)
        msg = msg.serialize()
        my_socket.sendto(msg.encode('utf8'), (client_ip, client_port))
        self.connecting.add({(client_ip, client_port): data['WIN']})
    send_syn()
    print(self.connecting)
    print(self.conn_table)

  def establish_conn_2(self, client_ip, client_port, data):
    check_seq = self.begin_seq + 1
    # print(data)
    if data['CTL'] == 'ACK' and data['ACK'] == check_seq:
      
      # self.conn_table.add((client_ip, client_port), check_seq)
      self.conn_table[(client_ip, client_port)] = {'SEQ': data['ACK'], \
      'ACK': data['SEQ'],\
       'WIN_SIZE': self.connecting[(client_ip, client_port)], \
       'IDX': 0,\
       'WIN': []} 
      self.connecting.pop((client_ip, client_port))
    print(self.connecting)
    print(self.conn_table)

  # def send_response(self, client_address, data, my_socket):
  #   if client_address not in self.conn_table:
  #     return
  #   last_status = self.conn_table[client_address]
  #   print('server recieve: %s' % (data))
  #   new_message_len = 5
  #   if last_status['SEQ'] == data['SEQ'] and last_status['ACK'] == data['ACK']:
  #     self.conn_table[client_address]['SEQ'] += data['LEN']
  #     msg = Message.Message('ACK', self.conn_table[client_address]['SEQ'], last_status['ACK'], 'Hello', new_message_len)
  #     msg = msg.serialize()
  #     self.conn_table[client_address]['ACK'] += new_message_len
  #     my_socket.sendto(msg.encode('utf8'), client_address)
   
  
  # def close_conn(self):
  def handler(self, client_address, data, my_socket):
    if not client_address in self.conn_table:
      return
    if len(self.conn_table[client_address]['WIN']) != 0:
      idx = 0
      # acked not pop
      for packet in self.conn_table[client_address]['WIN']:
        if packet['SEQ'] + packet['LEN'] == data['ACK']:
          self.conn_table[client_address]['WIN'].pop(idx)
        idx += 1
    while not self.win_empty(client_address):
      if self.conn_table[client_address]['IDX'] == len(self.send_data):
        break
      begin = self.conn_table[client_address]['IDX']
      newSeq = self.conn_table[client_address]['SEQ']
      newAck = self.conn_table[client_address]['ACK']
      msg = Message.Message('ACK', newAck, newSeq, \
      self.send_data[begin:begin+self.size], self.size, 0)
      self.conn_table[client_address]['WIN'].append(msg)
      msg = msg.serialize()
      self.conn_table[client_address]['IDX'] += self.size
      self.conn_table[client_address]['SEQ'] += self.size
      my_socket.sendto(msg.encode('utf8'), client_address)

    if self.conn_table[client_address]['IDX'] == len(self.send_data):
      self.close_conn(client_address)
    

  def win_empty(self, client_address):
    win = self.conn_table[client_address]['WIN']
    total = 0
    for packet in win:
      total += packet['LEN']
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