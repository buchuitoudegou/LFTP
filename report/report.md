# 实验报告
<a href="https://github.com/buchuitoudegou/LFTP">源码链接</a>
## 结构设计
采用了rdt3.0+GO-BACK-N的模型，即维护一个流量控制窗口，一个拥塞控制窗口，在窗口大小范围内进行传输。收到对应的ACK包，并且满足在自己之前的包都ACK了的情况下可以从窗口移除。只有当窗口有空闲空间的时候可以发送报文。如果超过一定时间没有收到需要的ACK报文，将会启动重传机制，将窗口内的报文发回。

LFTP采用了一个线程响应一个请求的模式，通过多线程来提高应答的效率，但也因此会出现共享资源访问安全的问题，以及链路中分组过多的问题。

## 模块设计
### 客户端建立连接
```python
def send_syn():
  """
  description:send SYN to server
  """
  my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  my_socket.bind((self.ip_addr, self.port))
  CTL = 'SYN'
  ACK = -1
  SEQ = begin_seq
  DATA = filename.encode('utf8')
  msg = Message.Message(CTL, ACK, SEQ, DATA, 1, self.win_size)
  msg = msg.serialize()
  print(msg)
  my_socket.sendto(msg, (self.des_ip, self.des_port))
  my_socket.close()
def wait_for_msg():
  """
    description: receive SYN and ACK from server
  """
  my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  my_socket.bind((self.ip_addr, self.port))
  #print(self.port)
  recv = my_socket.recv(self.port)
  print(recv)
  self.msg_queue.put(recv)
  my_socket.close()
```
第一次握手时，由客户端将报文握手报文发送给服务端，并且在原地等待服务端发来的ACK+SYN报文，拿到ACK+SYN报文之后发一个ACK报文给服务端，表示连接正式建立。

### 服务端建立连接
```python
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
      for i in range(10):
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
```
和客户端的原理相似，拿到第一个SYN+ACK报文之后发回一个SYN+ACK报文，如果并且给它准备好相应的文件资源等，由文件描述符打开一个文件准备读取或者写入。

### 客户端请求资源
```python
while True:
  # ananlize packet
  data = my_socket.recv(self.port)
  print(data)
  data = restore(data)
  idx = 0
  # if transport complete
  if data['CTL'] == 'FIN':
    self.timer.cancel()
    print('transport complete')
    break
  # analog packet loss
  if random.random() > 0.9:
    print('throw', data)
    continue
  idx = 0
  for packet in self.last_packet:
    if packet.ACK == data['SEQ'] + data['LEN']:
      print('resend', packet)
      my_socket.sendto(packet.serialize(), (self.des_ip, self.des_port))
  # whether correct
  if data['ACK'] == self.seq and data['SEQ'] == self.ack:
    print(data)
    # save to the file
    fd.write(data['DATA'])
    self.timer.cancel()
    self.ack = self.ack + data['LEN']
    msg = Message.Message('ACK', self.ack, self.seq, b'', data['LEN'], 0)
    self.last_packet.append(msg)
    msg = msg.serialize()
    my_socket.sendto(msg, (self.des_ip, self.des_port))
    #self.timer = Timer(2, self.resend, args=(my_socket, ))
    #self.timer.start()
  else:
    pass
fd.close()
my_socket.close()
```
这是发送请求中比较重要的一部分逻辑。我们在这里可以看到，当接收到服务端发回的连接断开的FIN包时，则表示传输已经完成，这时退出循环，并将socket关闭，文件关闭；反之，我们先判断这个包是否是我们需要的，如果是，则让它存储的数据写入到文件中，然后给服务端发送一个ACK包。这里需要注意的是，由于服务端采用多线程的应答模式，因此链路中可能会有大量的分组，为了降低链路压力，客户端的重传只选择服务端没收到的ACK分组，即客户端如果收到重复的SEQ而且它的ACK在窗口中，则重传这个ACK分组

### 服务端响应资源请求
```python
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
```
这是LFTP最为重要的部分。首先我们会判断这个ip和端口是否在连接表中，由于UDP是无连接的协议，因此，在服务端模型中加入了连接表的概念，里面按照ip和端口存储了每个客户端在传输过程中要用到的东西，比如线程锁，文件资源，窗口大小，SEQ，ACK等

在接收到一个在连接表中的客户端发送的分组时，先判断这个分组是ACK了哪个发送过的SEQ，并给它打上标记，如果满足在窗口中的某一个分组，它前面的所有分组都已经标记过，则将他们移除窗口。当窗口有空闲位置时，我们会发送一个新的分组，并将他放入窗口中。

要注意的是，在多线程的环境下，对每一个分组进行操作之前，必须获取锁，保证访问的资源的安全性。

当发送完一个分组，或者收到一个新的ACK分组，我们都会重启一次定时器，保证链路中不会重复发送大量没有必要的分组。

### 拥塞控制
```python
class Congestion():
  def __init__(self):
    """
      description: init params of Congestion Control
      cwnd: congestion window
      ssthresh: threshold of congestion window
      dupACKcount: number of duplicate ACK
      status: 0/1/2
    """
    self.cwnd = 1
    self.ssthresh = 64
    self.dupACKcount = 0 
    self.status = 0
  
  def update(self, event):
    """
      description: update congestion control status according to the event
      :param event: event type(DUP_ACK, NEW_ACK, TIMEOUT)
      :type event: str
      :return: None
    """
    if self.status == 0:
      if event == 'DUP_ACK':
        self.dupACKcount += 1
      elif event == 'NEW_ACK':
        self.cwnd += 1
        self.dupACKcount = 0
      elif event == 'TIMEOUT':
        self.ssthresh = self.cwnd / 2
        self.cwnd = 1
        self.dupACKcount = 0

      if self.dupACKcount == 3:
        self.status = 2
        self.ssthresh = self.cwnd / 2
        self.cwnd = self.ssthresh + 3
      elif self.cwnd >= self.ssthresh:
        self.status = 1

    elif self.status == 1:
      if event == 'NEW_ACK':
        self.cwnd += 1 / self.cwnd
        self.dupACKcount = 0
      elif event == 'DUP_ACK':
        self.dupACKcount += 1
      elif event == 'TIMEOUT':
        self.ssthresh = self.cwnd / 2
        self.cwnd = 1
        self.dupACKcount = 0
        self.status = 0

      if self.dupACKcount == 3:
        self.status = 2
        self.ssthresh = self.cwnd / 2
        self.cwnd = self.ssthresh + 3
    
    elif self.status == 2:
      if event == 'DUP_ACK':
        self.cwnd += 1
      elif event == 'NEW_ACK':
        self.status = 1
        self.cwnd = self.ssthresh
        self.dupACKcount = 0
      elif event == 'TIMEOUT':
        self.status = 0
        self.ssthresh = self.cwnd / 2
        self.cwnd = 1
        self.dupACKcount = 0
```
上面实现了一个拥塞控制，大体结构可以参考《计算机网络——自顶向下方法（第6版）》p184，图3-52. 主要功能是，通过判断timeout和冗余的ACK分组更新拥塞控制窗口的最大分段大小。在每一次发送请求之前，都要先判断流量控制窗口以及拥塞控制窗口是否空余。

这里status的值可以取0/1/2，分别代表慢启动，拥塞避免，快速回复三种状态。

### 客户端上传文件
跟服务端发送文件类似，这里不多赘述。

## 实验中遇到的问题
1. python的网络编程。第一次接触到python的网络编程功能，对socket的很多API都不是很熟悉，因此在初期浪费了很多时间。加上第一次大规模使用多线程进行编程，发现线程安全问题非常重要。线程安全不仅体现在I/O模式的保护，还要保护自己维护的共享内存区域，不能让同一个线程同时访问同一个共享区域，否则很容易出现奇怪的玄学问题，用print无法发现错误。另外，在用锁的过程中，尽量使用with结构，这样可以自动释放锁，防止死锁现象的出现。对于一些不可避免的访问冲突越界等，需要用try/except结构来避免程序异常退出（子线程出现异常进程不会退出）
2. bytes类型的传输。在设计之初，传输的数据用的是str类型，这就导致了传输二进制文件的时候会有编码解码的问题（JPEG文件无法进行解码操作），因此后来将分组的基类改成了bytes类型，即对读进来的数据不进行加工，直接拼接到报文上，然后进行传输，这样子就避免了bytes类型和str类型互相转换时产生的问题。另外，在udpserver中，官方文档给出了用strip读取数据的例子，在改了之后记得将它去掉，不然会把报文结尾出现的转义字符去掉。
3. 多线程环境。多线程的问题已经提过，在部署到服务器之后发现，由于Linux和Windows的线程环境的不同而导致线程创建失败。原因好像是python在Linux环境下无法无限创建线程，导致有的分组无法被新的线程处理，导致部署失败。
4. pythonGIL共享锁。python在设计之初，为了内存安全，设置了GIL共享锁，这样的锁会让python的多线程变得名存实亡：在python程序中，只有一个核线程对整个进程进行调度，也就是说，python是用了分片调度的方式处理并发事件，但是并发并不是并行，在实际上并没有提高效率。因此，要做到真正的多客户端处理，应该使用多进程的方式。

## 实验结果分析
为了方便分析，这里不对大文件的传输进行分析（log会将发送的分组全部打印出来）

### 客户端请求资源(一个客户端)
![preview](https://raw.githubusercontent.com/buchuitoudegou/LFTP/master/report/client-1.png)

![preview](https://raw.githubusercontent.com/buchuitoudegou/LFTP/master/report/server-1.png)

![preview](https://raw.githubusercontent.com/buchuitoudegou/LFTP/master/report/result-1.png)

客户端请求了一个small.txt资源，丢包是随机的，丢包会触发重传

### 客户端发送资源
![preview](https://raw.githubusercontent.com/buchuitoudegou/LFTP/master/report/client-2.png)

![preview](https://raw.githubusercontent.com/buchuitoudegou/LFTP/master/report/server-2.png)

![preview](https://raw.githubusercontent.com/buchuitoudegou/LFTP/master/report/result-2.png)

客户端上传一个small.txt资源

### 两个客户端请求资源（一个发送一个上传）
![preview](https://raw.githubusercontent.com/buchuitoudegou/LFTP/master/report/client-3.png)

![preview](https://raw.githubusercontent.com/buchuitoudegou/LFTP/master/report/server-3.png)

其中客户端上传small777.txt，另一个下载small.txt

## 实验感想
在实验之前接触过很久的网络编程，都是利用框架或者http模块进行网络访问，但是如果要让自己实现一个底层的TCP模型，才发现之前使用过的模块是多么的完美。实现的LFTP能够成功实现一个图像文件的传输，但是传输速率还是没有别人的模块好。希望以后在学习的时候能有时间多关注这些底层的模型，这样能对自己的编程水平有不小的提高。