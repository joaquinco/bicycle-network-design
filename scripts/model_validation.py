import os

import bcnetwork as bc

models_dir = 'instances/sioux-falls/examples'


model_names = ['', 'single_level_v2', 'single_level_v3', 'single_level_v4']
use_glpsol_opts = [False, True]

for path in os.scandir(models_dir):
    blacklist = ['graph']
    whitelist = ['yaml', '17']
    if not all(map(lambda x: x in path.name, whitelist)) or any(map(lambda x: x in path.name, blacklist)):
        continue

    model = bc.model.Model.load(
        os.path.join(models_dir, path.name)
    )
    model.project_root = '.'

    runs = []

    for model_name in model_names:
        for use_glpsol in use_glpsol_opts:
            s = model.solve(model_name=model_name, use_glpsol=use_glpsol)
            e = model.validate_solution(s)

            if e:
                print(f'error on {path.name}, {model_name} using {s.solver}')
                runs.append((s, e))

    breakpoint()
