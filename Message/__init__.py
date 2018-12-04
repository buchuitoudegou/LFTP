class Message():
  def __init__(self, CTL, ACK, SEQ, DATA, LEN, WIN):
    self.CTL = CTL
    self.ACK = ACK
    self.SEQ = SEQ
    self.DATA = DATA
    self.LEN = LEN
    self.WIN = WIN
    self.marked = False

  def serialize(self):
    string = string = str(self.CTL) + '@@@@' \
        + str(self.ACK) + '@@@@' \
        + str(self.SEQ) + '@@@@' \
        + str(self.LEN) + '@@@@' \
        + str(self.WIN) + '@@@@' \
        + str(self.marked) + '@@@@'
    string = string.encode('utf8')
    string += self.DATA
    return string

def restore(string):
  arr = string.split(b'@@@@')
  return { \
    'CTL': arr[0].decode('utf8'), \
    'ACK': int(arr[1].decode('utf8')), \
    'SEQ': int(arr[2].decode('utf8')),\
    'LEN': int(arr[3].decode('utf8')),\
    'WIN': int(arr[4].decode('utf8')),\
    'marked': False if arr[5].decode('utf8') == 'False' else True,\
    'DATA': arr[6]
  }