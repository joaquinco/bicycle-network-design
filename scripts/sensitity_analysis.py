import argparse
import functools
import itertools
import os
from multiprocessing import Pool
import sys

import numpy as np

import bcnetwork as bc
import functions as funcs

data_dir = 'instances/sioux-falls/'
nodes_file = os.path.join(data_dir, 'nodes.csv')
arcs_file = os.path.join(data_dir, 'arcs.csv')
odpairs_file = os.path.join(data_dir, 'origin_destination.csv')


def build_breakpoinst(func, count, m):
    """
    Return list of breakpoints by evaluating func
    :count: times between m and 1.

    :count: must be at least 2
    """
    x = np.linspace(m, 1, 1000)
    y = func(x)

    interval = 1 / (count - 1)
    breakpoints = []

    curr_threshold = y.max()
    for idx, y_val in enumerate(y):
        if y_val <= curr_threshold:
            breakpoints.append((y_val, x[idx]))
            curr_threshold -= interval

    if len(breakpoints) < count:
        breakpoints.append((y[-1], x[-1]))

    breakpoints.reverse()
    return breakpoints


default_infra_count = 6
default_m = bc.costs.calculate_user_cost(1, default_infra_count - 1)

default_kwargs = dict(
    name='Sioux-Falls',
    nodes_file=nodes_file,
    arcs_file=arcs_file,
    odpairs_file=odpairs_file,
    budget_factor=0.4,
    infrastructure_count=default_infra_count,
    breakpoints=build_breakpoinst(
        functools.partial(funcs.linear, m=default_m), 5, default_m,
    ),
)

solve_params = {
    'solver': 'cbc',
}

breakpoint_funcs = [
    funcs.linear,
    funcs.inv_logit,
]


def generate_runs_params():
    """
    Generate all possible model parameter combinations by picking each possible values
    of infrastructure_count, budget_factor and breakpoints within a fixed set.
    """
    infrastructure_counts = [3]
    budget_factors = [0.1, 0.6, 0.8]
    breakpoint_counts = [5, 10]

    for infra_count in infrastructure_counts:
        yield (
            f'{infra_count}_infras',
            {**default_kwargs, 'infrastructure_count': infra_count},
        )

    for budget_factor in budget_factors:
        yield (
            f'{budget_factor}_budget_factor',
            {**default_kwargs, 'budget_factor': budget_factor},
        )

    for breakpoint_count in breakpoint_counts:
        for func in breakpoint_funcs:
            current_m = bc.costs.calculate_user_cost(
                1, default_infra_count - 1)
            breakpoints = build_breakpoinst(
                functools.partial(
                    func, m=current_m), breakpoint_count, current_m,
            )

            yield (
                f'{func.__name__}_{breakpoint_count}_breakpoints',
                {**default_kwargs, 'breakpoints': breakpoints},
            )


def run_model(directory, model_suffix, model_params):
    """
    Creates and save the model instance.
    Solve and save solution.
    """
    model_name = 'sioux_falls_' + model_suffix
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
    all_params = list(generate_runs_params())
    print(f'Models to run: {len(all_params)}')

    with Pool(worker_count) as pool:
        pool.map(pool_run_model, [(directory, *params)
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
