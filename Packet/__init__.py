class Packet():
  """
  description: class of packet
  
  - attr seq: the sequence number of the packet

  :types seq: integer
  
  - attr ack: the acknowledge number of the packet
  
  :types ack: integer
  
  - attr rwnd: the window of the reciever
  
  :types rwnd: integer
  
  - attr flag: flag of the TCP packet 
  
  :types flag: dict
  """
  def __init__(self, 
      seq=-1, 
      ack=-1, 
      rwnd=-1, 
      flag={'URG': 0,
      'ACK': 0,
      'PSH': 0,
      'RST': 0,
      'SYN': 0,
      'FIN': 0}
    ):
    # sequence number and acknowledge number
    self.seq = seq
    self.ack = ack
    # length of the reciever's window
    self.rwnd = rwnd
    self.flag = flag
    self.data = b''

  def serialize(self):
    string = str(self.seq) + '@@@@' \
          + str(self.ack) + '@@@@' \
          + str(self.rwnd) + '@@@@'
    for key in self.flag.keys():
      string += str(self.flag[key])
    string += '@@@@'
    string = string.encode('utf8')
    string += self.data
    return string

  @staticmethod
  def restore(string):
    arr = string.split(b'@@@@')
    result = Packet()
    result.seq = int(arr[0].decode('utf8'))
    result.ack = int(arr[1].decode('utf8'))
    result.rwnd = int(arr[2].decode('utf8'))
    flag = arr[3].decode('utf8')
    idx = 0
    for key in result.flag.keys():
      result.flag[key] = int(flag[idx])
      idx += 1
    result.data = arr[4]
    return result
    