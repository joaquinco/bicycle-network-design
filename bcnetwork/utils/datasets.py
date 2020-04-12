from os import path
import shapefile
import networkx as nx
import bcnetwork.graph as gu

DATASETS_PATH = path.join(path.dirname(__file__), '../datasets')

def get_montevideo():
  reader = shapefile.Reader(path.join(DATASETS_PATH, 'montevideo/data.shp'))
  
  records = reader.shapeRecords()

  street_by_id = {}
  for record in records:
    # TODO: finish this
    pass


def get_transpurbanpasaj2019():
  """
  Load graph and demand from files under datasets
  """
  base_path = path.join(DATASETS_PATH, 'transpurbanpasaj2019')
  demand = {}

  with open(path.join(base_path, 'demand.txt')) as f:
    for source, content in enumerate(f, start=1):
      if not f:
        continue

      numbers = map(int, content.split())
      for destination, d in enumerate(numbers, start=1):
        if d <= 0:
          continue

        demand[(str(source), str(destination))] = d


  with open(path.join(base_path, 'graph.json')) as f:
    graph = gu.load(f)

  return graph, demand


_dataset_getters = {
  'montevideo': get_montevideo,
  'transpurbanpasaj2019': get_transpurbanpasaj2019,
}

def dataset(key):
  global _dataset_getters

  getter = _dataset_getters.get(key, None)
  if not getter:
    raise Exception('Dataset not found')

  return getter()
