import argparse
import itertools
import os
from multiprocessing import Pool
import sys

import numpy as np

import bcnetwork as bc

data_dir = 'instances/sioux-falls/'
nodes_file = os.path.join(data_dir, 'nodes.csv')
arcs_file = os.path.join(data_dir, 'arcs.csv')
odpairs_file = os.path.join(data_dir, 'origin_destination.csv')


default_kwargs = dict(
    name='Sioux-Falls',
    nodes_file=nodes_file,
    arcs_file=arcs_file,
    odpairs_file=odpairs_file,
)

solve_params = {
    'solver': 'cbc',
}


def select_breakpoints(all_breakpoints, count):
    """
    Pick count evenly spaced breakpoints from all_breakpoints.
    """
    sep = len(all_breakpoints) // count

    return [
        all_breakpoints[index * sep]
        for index in range(count)
    ]


def generate_params_combinations():
    """
    Generate all possible model parameter combinations by picking each possible values
    of infrastructure_count, budget_factor and breakpoints within a fixed set.
    """
    infrastructure_counts = list(range(2, 7))
    budget_factors = np.linspace(0.01, 0.6, num=20)

    breakpoint_counts = [2, 3, 4, 5, 6, 7, 8, 9, 10]
    all_breakpoints = list(zip(
        np.linspace(0, 1, num=10),
        np.linspace(1, 0.7, num=10)
    ))

    possible_breakpoints = [select_breakpoints(
        all_breakpoints, count) for count in breakpoint_counts]

    combinations = itertools.product(
        infrastructure_counts, budget_factors, possible_breakpoints)
    for infra_count, budget_factor, breakpoints in combinations:
        yield {
            **default_kwargs,
            'infrastructure_count': infra_count,
            'budget_factor': budget_factor,
            'breakpoints': breakpoints
        }


def get_model_name(model_params):
    infrastructure_count = model_params['infrastructure_count']
    budget_factor = model_params['budget_factor']
    breakpoint_length = len(model_params['breakpoints'])

    return f'sioux_falls_I{infrastructure_count}_B{budget_factor:.2}_PQ{breakpoint_length}'


def run_model(directory, model_params):
    """
    Creates and save the model instance.
    Solve and save solution.
    """
    model_name = get_model_name(model_params)
    print(f'Running model {model_name}')

    model = bc.model.Model(**model_params)
    model.save(os.path.join(directory, f'{model_name}.pkl'))
    solution = model.solve(**solve_params)
    solution.save(os.path.join(directory, f'solution_{model_name}.pkl'))


def pool_run_model(args):
    run_model(*args)


def run_parameter_combinations(directory, worker_count):
    """
    Run all parameter combinations
    """
    all_params = list(generate_params_combinations())
    print(f'Models to run: {len(all_params)}')

    with Pool(worker_count) as pool:
        pool.map(pool_run_model, [(directory, params)
                 for params in all_params])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    parser.add_argument('-p', '--parallelism', type=int, default=4)

    args = parser.parse_args(sys.argv[1:])

    os.makedirs(args.directory, exist_ok=True)

    run_parameter_combinations(args.directory, args.parallelism)


if __name__ == '__main__':
    main()
