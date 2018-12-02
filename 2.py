import socket

my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.bind(('127.0.0.1', 10100))

my_socket.sendto('1'.encode('utf8'), ('127.0.0.1', 8088))
my_socket.sendto('2'.encode('utf8'), ('127.0.0.1', 8088))
my_socket.close()