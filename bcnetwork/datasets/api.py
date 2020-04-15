from .datasets import get_montevideo, get_transpurbanpasaj2019

_dataset_getters = {
  'montevideo': get_montevideo,
  'transpurbanpasaj2019': get_transpurbanpasaj2019,
}

def get(key):
  global _dataset_getters

  getter = _dataset_getters.get(key, None)
  if not getter:
    raise Exception('Dataset not found')

  return getter()
