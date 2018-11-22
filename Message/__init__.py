class Message():
  def __init__(self, CTL, ACK, SEQ, DATA, LEN):
    self.CTL = CTL
    self.ACK = ACK
    self.SEQ = SEQ
    self.DATA = DATA
    self.LEN = LEN
  def serialize(self):
    string = self.CTL + '|' + str(self.ACK) + '|' + str(self.SEQ) + '|' + self.DATA + '|' + str(self.LEN)
    return string

def restore(string):
  arr = string.split('|')
  return { 'CTL': str(arr[0])[2:], 'ACK': int(arr[1]), 'SEQ': int(arr[2]), 'DATA': str(arr[3]), 'LEN': int(arr[4][:len(arr[4])-1])}