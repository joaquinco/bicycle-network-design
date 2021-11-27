import argparse
from collections import OrderedDict
import functools
import os
import sys

from matplotlib import pyplot as plt
import pandas as pd

import bcnetwork as bc


sort_by_columns = ['budget_factor', 'transfer_function', 'breakpoint_count']


def get_solution_path(model_path):
    dirname, basename = os.path.split(model_path)
    name, _ = os.path.splitext(basename)

    return os.path.join(dirname, f'solution_{name}.pkl')


def get_function_name(model_name):
    """
    Return demand transfer function
    name out of model_name
    """
    fallback = 'lineal'

    name_map = dict(
        lineal=fallback,
        sad='concave down',
        happy='concave up',
        logit='logit',
    )

    for match_name, name in name_map.items():
        if match_name in model_name:
            return name

    return fallback


def get_model_and_solution(model_path):
    """
    Return model and solution objects
    """
    solution_path = get_solution_path(model_path)

    if not os.path.exists(solution_path):
        return None, None

    model = bc.model.Model.load(model_path)
    if os.path.exists(solution_path):
        solution = bc.solution.Solution.load(solution_path)
    else:
        solution = None

    return model, solution


def get_model_name_from_path(model_path):
    model_basename = os.path.basename(model_path)
    model_name, _ext = os.path.splitext(model_basename)

    return model_name


def format_run_time_seconds(duration):
    """
    Given a numeric duration returns a string
    HH:MM:SS
    """
    duration = int(duration)
    hours = duration // 3600
    minutes = (duration - hours * 3600) // 60
    seconds = duration - hours * 3600 - minutes * 60

    return f'{hours:02}:{minutes:02}:{seconds:02}'


def get_row_from_model(model_path, model, solution):
    """
    Return param information and run information.
    """
    model_name = get_model_name_from_path(model_path)

    did_timeout = hasattr(solution, 'did_timeout') and solution.did_timeout
    gap = solution.gap if hasattr(solution, 'gap') else None
    if gap:
        gap *= 100

    return {
        'name': model_name,
        'total_demand_transfered': solution.total_demand_transfered,
        'm': bc.costs.calculate_user_cost(1, model.infrastructure_count - 1),
        'infrastructure_count': model.infrastructure_count,
        'budget': model.budget,
        'budget_factor': model._budget_factor,
        'budget_used': solution.budget_used,
        'breakpoint_count': len(model.breakpoints),
        'transfer_function': get_function_name(model_name),
        'run_time_seconds': int(solution.run_time_seconds),
        'run_time_seconds_str': format_run_time_seconds(solution.run_time_seconds),
        'did_timeout': did_timeout,
        'gap': gap,
    }


def generate_runs_dataframe(working_dir):
    """
    Return a pd.DataFrame out of a directory of
    models and solutions.
    """
    rows = []
    instances = []

    for entry in os.scandir(working_dir):
        if entry.is_dir() or not entry.name.endswith('.pkl') or 'solution' in entry.name:
            continue

        model_path = os.path.join(working_dir, entry.name)
        model, solution = get_model_and_solution(model_path)
        if not solution:
            continue

        data = get_row_from_model(model_path, model, solution)
        rows.append(data)
        instances.append((data['name'], model, solution))

    return instances, pd.DataFrame(rows).sort_values(by=sort_by_columns)


def draw_instances(data_dir, instances):
    """
    Draw instances and solutions
    """
    for model_name, model, solution in instances:
        fig_filename = os.path.join(data_dir, f'{model_name}.png')

        if os.path.exists(fig_filename):
            continue

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10),)

        draw_model = functools.partial(
            bc.draw.draw,
            model,
            solution=solution,
            width=2,
        )

        draw_model(
            odpairs=True,
            infrastructures=True,
            ax=ax1,
        )
        ax1.set_title('Infrastructures Built')

        draw_model(
            odpairs=True,
            flows=True,
            flow_scale_factor=5,
            infrastructures=False,
            ax=ax2,
        )
        ax2.set_title('Flows')
        fig.savefig(fig_filename, dpi=300)
        plt.close(fig)


def summarize_solutions_to_csv(output_file, instances):
    """
    Write csv with solutions information
    - budget spent per infrastructure
    - infra length
    """
    def generate_row(model_name, model, solution):
        infra_costs = bc.misc.group_by(
            solution.data.infrastructures, 'infrastructure')
        cost_by_infra = [
            (f'infra_{key}', sum(map(lambda d: d.construction_cost, value)) / model.budget * 100)
            for key, value in infra_costs.items()
        ]

        demand_transfered_by_od = [
            (f'od_{entry.origin}_{entry.destination}', entry.demand_transfered)
            for entry in solution.data.demand_transfered
        ]

        return OrderedDict(
            cost_by_infra +
            demand_transfered_by_od +
            [
                ('budget_factor', model._budget_factor),
                ('budget', model.budget),
                ('budget_used', solution.budget_used),
                ('budget_used_percentage', solution.budget_used / model.budget),
                ('breakpoint_count', len(model.breakpoints)),
                ('total_demand_transfered', solution.total_demand_transfered),
                ('name', model_name),
                ('transfer_function', get_function_name(model_name)),
            ]
        )

    def generate_data():
        for entry in instances:
            yield generate_row(*entry)

    data = list(generate_data())
    header = sorted(functools.reduce(lambda x, y: x | y,
                    map(lambda d: set(d.keys()), data)))

    df = pd.DataFrame(data).sort_values(
        by=sort_by_columns)
    df.to_csv(output_file, index=False, columns=header)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('data_dir')

    args = parser.parse_args(sys.argv[1:])

    instances, df = generate_runs_dataframe(args.data_dir)
    df.to_csv(os.path.join(args.data_dir, 'asummup.csv'), index=False)
    draw_instances(
        args.data_dir,
        instances,
    )
    summarize_solutions_to_csv(
        os.path.join(args.data_dir, 'asolution_summary.csv'),
        instances,
    )


if __name__ == '__main__':
    main()
