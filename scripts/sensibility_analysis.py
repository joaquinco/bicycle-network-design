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
    x = np.linspace(m, 1, 10000)
    y = func(x)

    interval = (y.max() - y.min()) / (count - 1)
    breakpoints = []

    # this should be close to 1, if not 1
    curr_threshold = y.max()
    for x_val, y_val in zip(x, y):
        if y_val <= curr_threshold:
            breakpoints.append((y_val, x_val))
            curr_threshold -= interval

    if len(breakpoints) < count:
        breakpoints.append((y[-1], x[-1]))

    breakpoints.reverse()
    return breakpoints


budget_factors = [0.1, 0.4, 0.8, 1.6, 3.2, 6.4, 12.8]
breakpoint_counts = [5, 20, 50]
budget_breakpoint_counts = [5, 20]
budget_functions = [funcs.linear, funcs.inv_logit]

default_breakpoint_count = min(breakpoint_counts)
default_budget_factor = 0.4
default_infra_count = 6
# m is the maximum achievable improvement
# it's fixed to the minimum possible
# so that instances can be compared while keeping the same function.
fixed_m = bc.costs.calculate_user_cost(1, 5)

default_kwargs = dict(
    name='Sioux-Falls',
    nodes_file=nodes_file,
    arcs_file=arcs_file,
    odpairs_file=odpairs_file,
    budget_factor=default_budget_factor,
    infrastructure_count=default_infra_count,
    breakpoints=build_breakpoinst(
        functools.partial(
            funcs.linear, m=fixed_m), default_breakpoint_count, fixed_m,
    ),
)

solve_params = {
    'solver': 'cbc',
    'parallelism': 10,
}

breakpoint_funcs = [
    funcs.linear,
    funcs.inv_logit,
    funcs.sad,
    funcs.happy,
]


def instance_name(budget_factor, function_name, breakpoint_count):
    """
    Return instance name based on those parameters
    """
    return f'{budget_factor}_budget_factor_{function_name}_{breakpoint_count}_breakpoints'


def generate_runs_params():
    """
    Generate all possible model parameter combinations by picking each possible values
    of infrastructure_count, budget_factor and breakpoints within a fixed set.
    """
    assert set(budget_breakpoint_counts) - set(breakpoint_counts) == set()

    for budget_factor in budget_factors:
        for breakpoint_count in budget_breakpoint_counts:
            for func in budget_functions:
                yield (
                    instance_name(budget_factor, func.__name__,
                                  breakpoint_count),
                    {
                        **default_kwargs,
                        'budget_factor': budget_factor,
                        'breakpoints': build_breakpoinst(
                            functools.partial(
                                func, m=fixed_m), breakpoint_count, fixed_m,
                        ),
                    },
                )

    for breakpoint_count in breakpoint_counts:
        for func in breakpoint_funcs:
            breakpoints = build_breakpoinst(
                functools.partial(
                    func, m=fixed_m), breakpoint_count, fixed_m,
            )

            yield (
                instance_name(default_budget_factor,
                              func.__name__, breakpoint_count),
                {
                    **default_kwargs,
                    'breakpoints': breakpoints,
                },
            )


def run_model(directory, force_resolve, model_suffix, model_params):
    """
    Creates and save the model instance.
    Solve and save solution.
    """
    model_name = 'sioux_falls_' + model_suffix
    print(f'Running model {model_name}')

    model = bc.model.Model(**model_params)
    model_filename = os.path.join(directory, f'{model_name}.pkl')
    solution_filename = os.path.join(directory, f'solution_{model_name}.pkl')

    if not force_resolve and os.path.exists(model_filename) and os.path.exists(solution_filename):
        print(f'Skipping {model_name} since file already exists')
        return

    model.save(model_filename)
    solution = model.solve(**solve_params)
    solution.save(solution_filename)


def pool_run_model(args):
    run_model(*args)


def run_parameter_combinations(directory, worker_count, force_resolve):
    """
    Run all parameter combinations
    """
    all_params = list(generate_runs_params())
    print(f'Models to run: {len(all_params)}')

    with Pool(worker_count) as pool:
        pool.map(pool_run_model, [(directory, force_resolve, *params)
                 for params in all_params])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    parser.add_argument('--parallelism', type=int)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--timeout-hours', type=int)
    parser.add_argument('--output-dir')
    parser.add_argument('--force-resolve', action='store_true',
                        help='For rerunning already solved instances')

    args = parser.parse_args(sys.argv[1:])

    os.makedirs(args.directory, exist_ok=True)
    if args.timeout_hours:
        solve_params['timeout'] = args.timeout_hours * 60 * 60

    if args.parallelism:
        solve_params['parallelism'] = args.parallelism

    solve_params['output_dir'] = args.output_dir

    run_parameter_combinations(
        args.directory, args.workers, args.force_resolve)


if __name__ == '__main__':
    main()
