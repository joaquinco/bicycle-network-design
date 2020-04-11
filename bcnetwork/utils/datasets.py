import shapefile
import networkx as nx
import bcnetwork.graph as gu


def get_montevideo():
  path = '../dataset/montevideo/data.shp'

  reader = shapefile.Reader(path)
  
  records = reader.shapeRecords()

  street_by_id = {}
  for record in records:
    # TODO: finish this
    pass


_dataset_getters = {
  'montevideo': get_montevideo,
}

def dataset(key):
  global _dataset_getters

  getter = _dataset_getters.get(key, None)
  if not getattr:
    raise Exception('Dataset not found')

  return getattr()
