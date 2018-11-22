import Message

class Server():
  def __init__(self, ip, port):
    self.ip = ip
    self.port = port
    self.conn_table = dict()
    self.connecting = set()
    self.begin_seq = 200
  
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
        self.connecting.add((client_ip, client_port))
    send_syn()
    print(self.connecting)
    print(self.conn_table)

  def establish_conn_2(self, client_ip, client_port, data):
    check_seq = self.begin_seq + 1
    # print(data)
    if data['CTL'] == 'ACK' and data['ACK'] == check_seq:
      self.connecting.remove((client_ip, client_port))
      # self.conn_table.add((client_ip, client_port), check_seq)
      self.conn_table[(client_ip, client_port)] = {'ACK': check_seq, 'SEQ': data['SEQ']} 
    print(self.connecting)
    print(self.conn_table)

  def send_response(self, client_address, data, my_socket):
    last_status = self.conn_table[client_address]
    print('server recieve: %s' % (data))
    new_message_len = 5
    if last_status['SEQ'] == data['SEQ'] and last_status['ACK'] == data['ACK']:
      self.conn_table[client_address]['SEQ'] += data['LEN']
      msg = Message.Message('ACK', self.conn_table[client_address]['SEQ'], last_status['ACK'], 'Hello', new_message_len)
      msg = msg.serialize()
      self.conn_table[client_address]['ACK'] += new_message_len
      my_socket.sendto(msg.encode('utf8'), client_address)