import argparse
import functools
import os
import sys

from matplotlib import pyplot as plt
import pandas as pd

import bcnetwork as bc


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


def get_row_from_model(model_path, model, solution):
    """
    Return param information and run information.
    """
    model_name = get_model_name_from_path(model_path)

    did_timeout = hasattr(solution, 'did_timeout') and solution.did_timeout
    gap = solution.gap if hasattr(solution, 'gap') else None

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
        'run_time_seconds': solution.run_time_seconds,
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

    return instances, pd.DataFrame(rows).sort_values(by=['transfer_function', 'total_demand_transfered'])


def draw_instances(data_dir, instances):
    """
    Draw instances and solutions
    """
    for model_name, model, solution in instances:
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
        fig.savefig(os.path.join(data_dir, f'{model_name}.png'), dpi=300)
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
        cost_by_infra = {
            f'infra_{key}': sum(map(lambda d: d.construction_cost, value))
            for key, value in infra_costs.items()
        }

        demand_transfered_by_od = {
            f'od_{entry.origin}_{entry.destination}': entry.demand_transfered
            for entry in solution.data.demand_transfered
        }

        return {
            **cost_by_infra,
            **demand_transfered_by_od,
            'budget_used': solution.budget_used,
            'total_demand_transfered': solution.total_demand_transfered,
            'name': model_name,
            'transfer_function': get_function_name(model_name),
        }

    def generate_data():
        for entry in instances:
            yield generate_row(*entry)

    df = pd.DataFrame(generate_data()).sort_values(
        by=['transfer_function', 'total_demand_transfered'])
    df.to_csv(output_file, index=False)


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
        os.path.join(args.data_dir, 'solution_summary.csv'),
        instances,
    )


if __name__ == '__main__':
    main()
