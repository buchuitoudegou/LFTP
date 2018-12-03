
class FileManage():
  def __init__(self):
    self.source_table = {}
    self.path = './FileManage/'

  def load_resource(self, client_address, filename):
    data = open(self.path + filename)
    self.source_table[client_address] = data.read()
    