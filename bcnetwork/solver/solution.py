

class Solution(object):
  def __init__(self, value, modifications, paths):
    self.value = value
    self.modifications = modifications
    self.paths = paths

  def __repr__(self):
    return f'<Solution value={self.value}>'
