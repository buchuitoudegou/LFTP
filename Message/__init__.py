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
    string = self.CTL + '|' \
      + str(self.ACK) + '|' \
      + str(self.SEQ) + '|' \
      + str(self.DATA) + '|' \
      + str(self.LEN) + '|' \
      + str(self.WIN)
    return string

def restore(string):
  arr = string.split('|')
  return { \
    'CTL': str(arr[0])[2:], 'ACK': int(arr[1]), \
    'SEQ': int(arr[2]),\
    'DATA': str(arr[3]),\
    'LEN': int(arr[4]),\
    'WIN': int(arr[5][:len(arr[5])-1])
  }