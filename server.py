import threading
import socketserver
import sys
import queue
import myServer
from Message import restore
import random

server = myServer.Server('127.0.0.1', 8081)

import copy

class udpRequestHandler(socketserver.BaseRequestHandler):
  def __init__(self, request, client_address, server):
    super().__init__(request, client_address, server)
    
  def handle(self):
    data = self.request[0]
    temp = copy.deepcopy(self.request[0])
    data = restore(data)
    # print(data)
    client_ip = self.client_address[0]
    client_port = self.client_address[1]
    # print()
    if self.client_address not in server.conn_table and self.client_address not in server.connecting:
      t = threading.Thread(target=server.establish_conn_1, args=(client_ip, client_port, data, self.request[1],))
      t.start()
    elif self.client_address not in server.conn_table:
      # server.establish_conn_2(client_ip, client_port, data)
      t = threading.Thread(target=server.establish_conn_2, args=(client_ip, client_port, data, self.request[1], ))
      t.start()
    else:
      # server.handler(self.client_address, data, self.request[1])
      # if random.random() > 0.9:
      #   print('throw', data)
      #   server.throw += 1
      # else:  
      if 'FILE' in server.conn_table[self.client_address]:
        t = threading.Thread(target=server.upload_handler, args=(self.client_address, data, self.request[1], temp))
        t.start()
      else:
        t = threading.Thread(target=server.handler, args=(self.client_address, data, self.request[1]))
        t.start()
    
      
 
def listen():
  host, port = '127.0.0.1', 8081
  server = socketserver.UDPServer((host, port), udpRequestHandler)
  print('server is listening at port 8081')
  server.serve_forever()
  
if __name__ == '__main__':
  listen()