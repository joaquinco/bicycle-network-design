from .base_problem import get_base_model


_model_loaders = {
  'base_model': get_base_model,
}

def load_model(model_name, *args, **kwargs):
  """
  Calls the specified model loader
  """
  global _model_loaders

  if model_name not in _model_loaders:
    raise Exception(f'Model ${model_name} does not exists')

  return _model_loaders.get(model_name)(*args, **kwargs)
