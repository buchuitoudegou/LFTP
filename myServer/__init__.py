import Message
from threading import Timer
import FileManage
import threading
import Congestion
import time

class Server():
  def __init__(self, ip, port):
    self.ip = ip
    self.port = port
    self.conn_table = dict()
    self.connecting = dict()
    self.closing = dict()
    self.file_manage = FileManage.FileManage()
    self.begin_seq = 200
    self.size = 2048
    self.throw = 0
    self.timeout = 0.1
    
  def establish_conn_1(self, client_ip, client_port, data, my_socket):
    def send_syn():
      if data['CTL'] == 'SYN':
        data['DATA'] = data['DATA'].decode('utf8')
        if data['DATA'].split('.')[-1] != 'UP_LOAD':
          self.file_manage.load_resource((client_ip, client_port), data['DATA'], 0)
        else:
          self.file_manage.save_resource((client_ip, client_port), \
          data['DATA'].split('.')[0] + '.' + data['DATA'].split('.')[1], '')
        CTL = 'SYN+ACK'
        SEQ = self.begin_seq
        ACK = data['SEQ'] + 1
        DATA = b''
        msg = Message.Message(CTL, ACK, SEQ, DATA, 1, 0)
        msg = msg.serialize()
        my_socket.sendto(msg, (client_ip, client_port))
        self.connecting[(client_ip, client_port)] = data['WIN']
    send_syn()
    print(self.connecting)
    print(self.conn_table)

  def establish_conn_2(self, client_ip, client_port, data, my_socket):
    check_seq = self.begin_seq + 1
    print(data)
    data['DATA'] = data['DATA'].decode('utf8')
    timer = Timer(self.timeout, self.resend, args=((client_ip, client_port), my_socket, ))
    lock = threading.Lock()
    congestion = Congestion.Congestion()
    if data['CTL'] == 'ACK' and data['ACK'] == check_seq:
      self.conn_table[(client_ip, client_port)] = {\
        'SEQ': data['ACK'], \
        'ACK': data['SEQ'],\
        'WIN_SIZE': self.connecting[(client_ip, client_port)], \
        'IDX': 0,\
        'WIN': [],\
        'TIMEOUT': timer,\
        'LOCK': lock,\
        'CGT': congestion
      }
      if data['DATA'].split('.')[-1] == 'UP_LOAD':
        self.conn_table[(client_ip, client_port)]['FILE'] = data['DATA'].split('.')[0] + \
        '.' + data['DATA'].split('.')[1]
        self.conn_table[(client_ip, client_port)]['TIMEOUT'].cancel()
      timer.start()
      self.connecting.pop((client_ip, client_port))
    print(self.connecting)
    print(self.conn_table)

  def resend(self, client_address, my_socket):
    print('resend:')
    self.timeout += 0.2
    if not client_address in self.conn_table:
      return
    self.conn_table[client_address]['CGT'].update('TIMEOUT')
    for packet in self.conn_table[client_address]['WIN']:
      msg = packet.serialize()
      print(msg)
      my_socket.sendto(msg, client_address)
    print('resend complete')
    self.conn_table[client_address]['TIMEOUT'] = Timer(self.timeout, self.resend, args=(client_address, my_socket, ))
    self.conn_table[client_address]['TIMEOUT'].start()

  def handler(self, client_address, data, my_socket):
    lock = None
    try:
      lock = self.conn_table[client_address]['LOCK']
    except:
      return
    lock.acquire()
    print('lock acquire')
    if not client_address in self.conn_table:
      return
    if len(self.conn_table[client_address]['WIN']) != 0:
      idx = 0
      congestion_flag = False
      # marked not pop
      for packet in self.conn_table[client_address]['WIN']:
        if packet.SEQ + packet.LEN == data['ACK']:
          self.conn_table[client_address]['CGT'].update('NEW_ACK')
          self.timeout = 0.1
          congestion_flag = True
          self.conn_table[client_address]['WIN'][idx].marked = True
          self.conn_table[client_address]['TIMEOUT'].cancel()
          self.conn_table[client_address]['TIMEOUT'] = Timer(self.timeout, self.resend, args=(client_address, my_socket, ))
          self.conn_table[client_address]['TIMEOUT'].start()
        idx += 1
      if not congestion_flag:
        self.conn_table[client_address]['CGT'].update('DUP_ACK')
      delete = -1
      # pop continiously ack
      for packet in self.conn_table[client_address]['WIN']:
        if packet.marked == True:
          delete += 1
          self.conn_table[client_address]['WIN'].pop(delete)
        else:
          break
    print(data)
    is_finished = False
    c_send = 0
    while self.win_empty(client_address) and c_send < self.conn_table[client_address]['CGT'].cwnd:
      send_data = self.file_manage.load_resource(client_address, '', self.size)
      if send_data == '' or send_data == b'':
        is_finished = True
        break
      begin = self.conn_table[client_address]['IDX']
      newSeq = self.conn_table[client_address]['SEQ']
      newAck = self.conn_table[client_address]['ACK']
      msg = Message.Message('ACK', newAck, newSeq, send_data, self.size, 0)
      self.conn_table[client_address]['WIN'].append(msg)
      print(msg.serialize())
      msg = msg.serialize()
      self.conn_table[client_address]['IDX'] += self.size
      self.conn_table[client_address]['SEQ'] += self.size
      # congestion control
      # time.sleep(0.01 / self.conn_table[client_address]['CGT'].cwnd)
      my_socket.sendto(msg, client_address)
      c_send += 1

    if is_finished:
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

    lock.release()

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
    if client_address in self.conn_table:
      begin = self.conn_table[client_address]['IDX']
      newSeq = self.conn_table[client_address]['SEQ']
      newAck = self.conn_table[client_address]['ACK']
      msg = Message.Message('FIN', newAck, newSeq, b'', 0, 0)
      msg = msg.serialize()
      my_socket.sendto(msg, client_address)
      self.conn_table[client_address]['TIMEOUT'].cancel()
      try:
        self.conn_table[client_address]['LOCK'].release()
      except:
        pass
      self.conn_table.pop(client_address)
      self.file_manage.source_table[client_address]['fd'].close()
      self.file_manage.source_table.pop(client_address)

  def upload_handler(self, client_address, data, my_socket, temp):
    lock = None
    try:
      lock = self.conn_table[client_address]['LOCK']
    except:
      return
    lock.acquire()
    #print('lock acquire')
    if not client_address in self.conn_table:
      return
    if data['CTL'] == 'FIN':
      self.close_conn(client_address, my_socket)
      return
    for packet in self.conn_table[client_address]['WIN']:
      if packet.ACK == data['SEQ'] + data['LEN']:
        #print('resend', packet.serialize())
        my_socket.sendto(packet.serialize(), client_address)
    if data['ACK'] == self.conn_table[client_address]['SEQ'] and \
    data['SEQ'] == self.conn_table[client_address]['ACK']:
      print(data)
      filename = self.conn_table[client_address]['FILE']
      self.file_manage.save_resource(client_address, filename, data['DATA'])
      self.conn_table[client_address]['ACK'] += data['LEN']
      msg = Message.Message('ACK', \
        self.conn_table[client_address]['ACK'],\
        self.conn_table[client_address]['SEQ'],\
        b'',
        data['LEN'],
        0
      )
      self.conn_table[client_address]['WIN'].append(msg)
      msg = msg.serialize()
      my_socket.sendto(msg, client_address)
    lock.release()
