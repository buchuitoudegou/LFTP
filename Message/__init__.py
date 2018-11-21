class Message():
  def __init__(self, CTL, ACK, SEQ, DATA):
    self.CTL = CTL
    self.ACK = ACK
    self.SEQ = SEQ
    self.DATA = DATA
  def serialize(self):
    string = self.CTL + '|' + str(self.ACK) + '|' + str(self.SEQ) + '|' + self.DATA
    return string

def restore(string):
  arr = string.split('|')
  return { 'CTL': str(arr[0])[2:], 'ACK': int(arr[1]), 'SEQ': int(arr[2]), 'DATA': str(arr[3]) }