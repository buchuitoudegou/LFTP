import threading
import socketserver
import sys
import queue
import myServer
from Message import restore

server = myServer.Server('127.0.0.1', 8081)

class udpRequestHandler(socketserver.BaseRequestHandler):
  def __init__(self, request, client_address, server):
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
    if self.client_address not in server.conn_table and self.client_address not in server.connecting:
      server.establish_conn_1(client_ip, client_port, data, self.request[1])
    elif self.client_address not in server.conn_table:
      server.establish_conn_2(client_ip, client_port, data)

 
def listen():
  host, port = '127.0.0.1', 8081
  server = socketserver.UDPServer((host, port), udpRequestHandler)
  print('server is listening at port 8081')
  server.serve_forever()
  
if __name__ == '__main__':
  listen()