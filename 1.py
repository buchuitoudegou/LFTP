import time
import socketserver
import socket
# class udpRequestHandler(socketserver.BaseRequestHandler):
#   def __init__(self, request, client_address, server):
#     super().__init__(request, client_address, server)
  
#   def handle(self):
#     time.sleep(1)
#     data = str(self.request[0].strip())
#     print(data)

# def listen():
#   host, port = '127.0.0.1', 8088
#   server = socketserver.UDPServer((host, port), udpRequestHandler)
#   print('server is listening at port 8088')
#   server.serve_forever()
# listen()

my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.bind(('127.0.0.1', 8088))
my_socket.sendto('h1'.encode('utf8'), ('127.0.0.1', 7777))
my_socket.sendto('h2'.encode('utf8'), ('127.0.0.1', 7777))