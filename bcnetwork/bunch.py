
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
        return self[name]
