import Message
class Server():
  def __init__(self, ip, port):
    self.ip = ip
    self.port = port
    self.conn_table = set()
    self.connecting = set()
  
  def establish_conn_1(self, client_ip, client_port, data, my_socket):
    begin_seq = 200
    # print(data)
    def send_syn():
      if data['CTL'] == 'SYN':
        CTL = 'SYN+ACK'
        SEQ = begin_seq
        ACK = data['SEQ'] + 1
        DATA = ''
        msg = Message.Message(CTL, ACK, SEQ, DATA)
        msg = msg.serialize()
        my_socket.sendto(msg.encode('utf8'), (client_ip, client_port))
        self.connecting.add((client_ip, client_port))
    send_syn()
    print(self.connecting)
    print(self.conn_table)

  def establish_conn_2(self, client_ip, client_port, data):
    check_seq = 201
    # print(data)
    if data['CTL'] == 'ACK' and data['ACK'] == check_seq:
      self.connecting.remove((client_ip, client_port))
      self.conn_table.add((client_ip, client_port, check_seq))
    print(self.connecting)
    print(self.conn_table)