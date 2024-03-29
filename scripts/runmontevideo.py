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
)

solve_params = dict()


def save_instance(model_output, demands_file):
    model = bc.model.Model(
        **model_params,
        odpairs_file=demands_file,
    )
    model.save(model_output)

    data_path, _ = os.path.splitext(model_output)
    model.write_data(f'{data_path}.dat')


def add_distance_col(df):
    """
    Add distance column to demands dataframe
    """
    nodes = pd.read_csv(data_dir('nodes.csv'))
    nodes_by_id = {int(row.id): (row.x, row.y) for _, row in nodes.iterrows()}

    def compute_distance(row):
        return bc.geo.plane_distance(
            nodes_by_id[int(row.origin)],
            nodes_by_id[int(row.destination)],
        )

    df['distance'] = df.apply(compute_distance, axis=1)

    return df


def save_montevideo_max_distance(
        demands_df, max_distance, odpair_count, model_output):
    """
    Creates montevideo instance whose demand pairs are no further than
    :max_distance: distance.
    """
    df = add_distance_col(demands_df.copy())
    df = df[df.distance <= max_distance]
    df.to_csv(data_dir(f'demands_d{max_distance}.csv'))

    odpair_count = min(len(df), odpair_count)
    df = df.iloc[:odpair_count]

    demands_file = data_dir(f'demands_d{max_distance}_c{odpair_count}.csv')

    df.to_csv(demands_file, index=False)

    save_instance(
        model_output,
        demands_file,
    )


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('output_dir')
    parser.add_argument('--name-suffix', default='')
    parser.add_argument('--max-distance', type=float, default=5000.0)
    parser.add_argument('--breakpoint-count',
                        choices=[5, 10, 20], default=10, type=int)
    parser.add_argument(
        '--solver', choices=bc.run.supported_solvers, default='ampl')
    parser.add_argument('--timeout-hours', type=int)
    parser.add_argument('--function', required=True)
    parser.add_argument('--budget-factor', type=float, default=0.8)
    parser.add_argument(
        '--infrastructure-count',
        type=int,
        choices=list(range(1, 7)),
        default=4,
    )
    parser.add_argument('--odpair-count', type=int)

    return parser.parse_args(sys.argv[1:])


def main():
    args = parse_arguments()
    demands_df = pd.read_csv('instances/montevideo/demands.csv')

    if args.timeout_hours:
        solve_params['timeout'] = args.timeout_hours * 3600
    solve_params['solver'] = args.solver
    solve_params['output_dir'] = args.output_dir

    model_params['infrastructure_count'] = args.infrastructure_count

    transfer_function = functools.partial(
        getattr(functions, args.function),
        m=bc.costs.calculate_user_cost(
            1, model_params['infrastructure_count'] - 1,
        ),
    )
    model_params['breakpoints'] = bc.model_utils.build_breakpoints(
        transfer_function,
        args.breakpoint_count,
        infrastructure_count=model_params['infrastructure_count'],
    )
    model_params['budget_factor'] = args.budget_factor

    name_suffix = ''
    if args.name_suffix:
        name_suffix = '_' + args.name_suffix

    demands_df.sort_values(
        by=['demand', 'origin'], ascending=False, inplace=True)

    save_montevideo_max_distance(
        demands_df,
        args.max_distance,
        args.odpair_count,
        os.path.join(args.output_dir,
                     f'montevideo_d{args.max_distance}{name_suffix}.pkl'),
    )


if __name__ == '__main__':
    main()
