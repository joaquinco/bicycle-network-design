import copy


class Bunch(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getattr__(self, name):
        value = self.get(name)

        if value:
            if isinstance(value, dict):
                self[name] = Bunch(**value)
            if isinstance(value, list):
                self[name] = list(map(
                    lambda x: isinstance(x, dict) and Bunch(**x) or x,
                    value
                ))
        return self.get(name)

    def __getstate__(self):
        return self

    def __setstate__(self, state):
        self.update(state)

    def __deepcopy__(self, memo):
        return Bunch(**{
            key: copy.deepcopy(value, memo) if isinstance(
                value, dict) or isinstance(value, list) else value
            for key, value in self.items()
        })
