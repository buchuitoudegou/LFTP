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
    string = str(self.CTL) + '@@@@' \
      + str(self.ACK) + '@@@@' \
      + str(self.SEQ) + '@@@@' \
      + str(self.DATA) + '@@@@' \
      + str(self.LEN) + '@@@@' \
      + str(self.WIN) + '@@@@'\
      + str(self.marked)
    return string

def restore(string):
  arr = string.split('@@@@')
  return { \
    'CTL': str(arr[0]), \
    'ACK': int(arr[1]), \
    'SEQ': int(arr[2]),\
    'DATA': str(arr[3]),\
    'LEN': int(arr[4]),\
    'WIN': int(arr[5]),\
    'marked': False if arr[6] == 'False' else True
  }