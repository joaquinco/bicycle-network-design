from .base import Vicinity

class DefragVicinity(Vicinity):
  def get_default_config(self):
    return dict(
      minimun_length=2,
      maximim_jumps=100
    )

  def get_neighbors(self):
    return []
