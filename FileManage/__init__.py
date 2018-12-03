
class FileManage():
  def __init__(self):
    self.source_table = {}
    self.path = './FileManage/'

  def load_resource(self, client_address, filename, size):
    if client_address in self.source_table:
      self.source_table[client_address]['IDX'] += size
    else:
      data = None
      if filename.split('.')[1] == 'txt':
        data = open(self.path + filename, 'r')
      else:
        data = open(self.path + filename, 'rb')
      self.source_table[client_address] = {\
        'IDX': 0,\
        'fd': data\
      }
    return self.source_table[client_address]['fd'].read(size)
    