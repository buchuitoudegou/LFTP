import threading
import socketserver

class udpRequestHandler(socketserver.BaseRequestHandler):
  def __init__(self, request, client_address, server):
    super().__init__(request, client_address, server)
  
  def handle(self):
    data = self.request[0].strip()
    socket = self.request[1]
    print('[Recieve from %s:%s] %s' % (self.client_address[0], self.client_address[1], data))
    socket.sendto('next seq'.encode('gbk'), self.client_address)

def listen():
  host, port = '127.0.0.1', 8081
  server = socketserver.UDPServer((host, port), udpRequestHandler)
  print('server is listening at port 8081')
  server.serve_forever()
  
if __name__ == '__main__':
  listen()