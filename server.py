import threading
import socketserver
import sys
from Message import restore, Message
import queue
from Server import Server

class udpRequestHandler(socketserver.BaseRequestHandler):
  def __init__(self, request, client_address, server):
    self.conn_table = set()
    self.msg_queue = queue.Queue()
    self.connecting = set()
    super().__init__(request, client_address, server)
    
  
  def handle(self):
    # data = self.request[0].strip()
    # socket = self.request[1]
    # print('[Recieve from %s:%s] %s' % (self.client_address[0], self.client_address[1], data))
    # socket.sendto('next seq'.encode('gbk'), self.client_address)
    data = str(self.request[0].strip())
    data = restore(data)
    client_ip = self.client_address[0]
    client_port = self.client_address[1]
    if (client_ip, client_port) not in self.conn_table and (client_ip, client_port) not in self.connecting:
      self.establish_conn_1(client_ip, client_port, data)
    elif (client_ip, client_port) not in self.conn_table:
      self.establish_conn_2(client_ip, client_port, data)

  def establish_conn_1(self, client_ip, client_port, data):
    begin_seq = 200
    #print(data)
    def send_syn():
      if data['CTL'] == 'SYN':
        CTL = 'SYN+ACK'
        SEQ = begin_seq
        ACK = data['SEQ'] + 1
        DATA = ''
        msg = Message(CTL, ACK, SEQ, DATA)
        msg = msg.serialize()
        self.request[1].sendto(msg.encode('utf8'), (client_ip, client_port))
        self.connecting.add((client_ip, client_port))
    send_syn()
    print(self.connecting)
    print(self.conn_table)

  def establish_conn_2(self, client_ip, client_port, data):
    check_seq = 201
    #print(data)
    if data['CTL'] == 'ACK' and data['ACK'] == check_seq:
      #self.connecting.remove((client_ip, client_port))
      self.conn_table.add((client_ip, client_port))
    print(self.connecting)
    print(self.conn_table)

def listen():
  host, port = '127.0.0.1', 8081
  server = socketserver.UDPServer((host, port), udpRequestHandler)
  print('server is listening at port 8081')
  server.serve_forever()
  
if __name__ == '__main__':
  listen()