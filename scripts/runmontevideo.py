import argparse
import functools
import os
import sys

import pandas as pd

import bcnetwork as bc

import functions


data_dir = functools.partial(os.path.join, 'instances/montevideo/')

model_params = dict(
    nodes_file=data_dir('nodes.csv'),
    arcs_file=data_dir('arcs.csv'),
    infrastructure_count=4,
)

solve_params = dict()


def run_instance(model_output, demands_file):
    model = bc.model.Model(
        **model_params,
        odpairs_file=demands_file,
    )
    model.save(model_output)
    solution = model.solve(**solve_params)
    output_dir, model_filename = os.path.split(model_output)
    solution.save(os.path.join(output_dir, f'solution_{model_filename}'))


def run_montevideo_max_distance(demands_df, max_distance, model_output):
    """
    Creates montevideo instance whose demand pairs are no further than
    :max_distance: distance.
    """
    nodes = pd.read_csv(data_dir('nodes.csv'))
    nodes_by_id = {int(row.id): (row.x, row.y) for _, row in nodes.iterrows()}

    def compute_distance(row):
        return bc.geo.plane_distance(
            nodes_by_id[int(row.origin)],
            nodes_by_id[int(row.destination)],
        )

    df = demands_df.copy()
    df['distance'] = df.apply(compute_distance, axis=1)
    df = df[df.distance <= max_distance]
    demands_file = data_dir(f'demands_d{max_distance}.csv')

    df.to_csv(demands_file)

    run_instance(
        model_output,
        demands_file,
    )


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('output_dir')
    parser.add_argument('--name-suffix', default='')
    parser.add_argument('--max-distance', type=float)
    parser.add_argument('--breakpoint-count',
                        choices=[5, 10, 20], default=10, type=int)
    parser.add_argument(
        '--solver', choices=bc.run.supported_solvers, default='ampl')
    parser.add_argument('--timeout-hours', type=int)
    parser.add_argument('--function', required=True)
    parser.add_argument('--budget-factor', type=float, default=0.8)

    return parser.parse_args(sys.argv[1:])


def main():
    args = parse_arguments()
    demands_df = pd.read_csv('instances/montevideo/demands.csv')

    if args.timeout_hours:
        solve_params['timeout'] = args.timeout_hours * 3600
    solve_params['solver'] = args.solver
    solve_params['output_dir'] = args.output_dir

    model_params['breakpoints'] = bc.model_utils.build_breakpoints(
        getattr(functions, args.function),
        args.breakpoint_count,
        infrastructure_count=model_params['infrastructure_count'],
    )
    model_params['budget_factor'] = args.budget_factor

    name_suffix = ''
    if args.name_suffix:
        name_suffix = '_' + args.name_suffix

    demands_925_df = demands_df.sort_values(by=['demand'], ascending=False)
    demands_file = data_dir('demands_925.csv')
    demands_925_df.to_csv(demands_file)

    run_instance(
        os.path.join(args.output_dir, f'montevideo_925{name_suffix}.pkl'),
        demands_file,
    )
    run_montevideo_max_distance(
        demands_925_df,
        args.max_distance,
        os.path.join(args.output_dir,
                     f'montevideo_d{args.max_distance}{name_suffix}.pkl'),
    )


main()
