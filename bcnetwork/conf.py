from os import path
from bcnetwork.misc import KwargsClass

class _Settings(KwargsClass):
  pass


settings = _Settings(**{
  'dataset_path': path.join(path.dirname(__file__), 'resources')
})
