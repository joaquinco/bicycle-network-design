from .base import Vicinity


class KMeansVicinity(Vicinity):
  def get_default_config(self):
    return dict(
      k=100,
    )
