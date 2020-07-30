from os import path
from bcnetwork.misc import Bunch

class _Settings(Bunch):
  pass


settings = _Settings(**{
  'dataset_path': path.join(path.dirname(__file__), 'resources')
})
