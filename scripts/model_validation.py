import argparse
import os
import sys
import pickle

import bcnetwork as bc


default_model_names = ['', 'single_level_v2',
                       'single_level_v3', 'single_level_v4']


def perform(models_dir, model_names=None, instance_whitelist=None, save_solutions=False):
    use_glpsol_opts = [True]
    model_names = model_names or default_model_names

    blacklist = ['graph']
    whitelist = ['yaml']
    for path in os.scandir(models_dir):
        if not all(map(lambda x: x in path.name, whitelist)) or any(map(lambda x: x in path.name, blacklist)):
            continue

        if instance_whitelist and not any(map(lambda x: x in path.name, instance_whitelist)):
            continue

        model = bc.model.Model.load(
            os.path.join(models_dir, path.name)
        )
        model.project_root = '.'

        runs = []

        current_instance, _ext = os.path.splitext(path.name)

        def save_solution(s, model_name):
            solution_filename = f'{current_instance}_solution_{model_name}.pkl'
            with open(os.path.join(models_dir, solution_filename), 'wb') as f:
                pickle.dump(s, f)

        for model_name in model_names:
            hr_model_name = model_name or 'default'
            for use_glpsol in use_glpsol_opts:
                s = model.solve(model_name=model_name, use_glpsol=use_glpsol)
                e = model.validate_solution(s)
                print(
                    f'Solved: {path.name}. Model {hr_model_name} demand transfered: {s.total_demand_transfered}'
                )

                if save_solutions:
                    save_solution(s, hr_model_name)
                if e:
                    print(
                        f'error on {path.name}, {hr_model_name} using {s.solver}')
                    print(e)
                    runs.append((s, e))


def parse_arguments(rawargs):
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--model-name', nargs='*')
    parser.add_argument('-w', '--whitelist', nargs='*')
    parser.add_argument('--save-solutions', action='store_true')
    parser.add_argument('path')

    return parser.parse_args(rawargs)


def main():
    args = parse_arguments(sys.argv[1:])

    perform(
        args.path,
        model_names=args.model_name,
        instance_whitelist=args.whitelist,
        save_solutions=args.save_solutions,
    )


if __name__ == '__main__':
    main()
