import argparse
import re
from collections import OrderedDict
import functools
import os
import sys

from matplotlib import pyplot as plt
import numpy as np
import networkx as nx
import pandas as pd

import bcnetwork as bc

from misc import format_run_time_seconds


sort_by_columns = ['budget_factor', 'transfer_function', 'breakpoint_count']
colors = list(bc.colors.values())


def get_solution_path(model_path):
    dirname, basename = os.path.split(model_path)
    name, _ = os.path.splitext(basename)

    return os.path.join(dirname, f'solution_{name}.pkl')


def get_function_readable_name(function_name):
    return {
        'lineal': 'lineal',
        'concave up': 'concavidad positiva',
        'concave down': 'concavidad negativa',
        'logit': 'logística',
    }.get(function_name, 'Unknown')


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


def get_row_from_model(model_path, model, solution, total_demand):
    """
    Return param information and run information.
    """
    model_name = get_model_name_from_path(model_path)

    did_timeout = hasattr(solution, 'did_timeout') and solution.did_timeout
    gap = solution.gap if hasattr(solution, 'gap') else None
    if gap:
        gap *= 100

    function_name = get_function_name(model_name)
    function_readable_name = get_function_readable_name(function_name)

    affected_odpair_count = len(list(
        filter(lambda dt: dt.demand_transfered > 0, solution.data.demand_transfered)))

    return {
        'name': model_name,
        'total_demand_transfered': solution.total_demand_transfered,
        'total_demand_transfered_percentage': 100 * solution.total_demand_transfered / total_demand,
        'm': bc.costs.calculate_user_cost(1, model.infrastructure_count - 1),
        'infrastructure_count': model.infrastructure_count,
        'affected_odpair_count': affected_odpair_count,
        'budget': model.budget,
        'budget_factor': model._budget_factor,
        'budget_used': solution.budget_used,
        'breakpoint_count': len(model.breakpoints),
        'transfer_function': function_name,
        'transfer_function_name': function_readable_name,
        'run_time_seconds': int(solution.run_time_seconds),
        'run_time_seconds_str': format_run_time_seconds(solution.run_time_seconds),
        'did_timeout': did_timeout,
        'gap': gap,
        'uid': model.uid if hasattr(model, 'uid') else None,
    }


def generate_runs_dataframe(working_dir):
    """
    Return a pd.DataFrame out of a directory of
    models and solutions.
    """
    rows = []
    instances = []
    total_demand = None

    for entry in os.scandir(working_dir):
        if entry.is_dir() or not entry.name.endswith('.pkl') or 'solution' in entry.name:
            continue

        model_path = os.path.join(working_dir, entry.name)
        model, solution = get_model_and_solution(model_path)
        if not solution:
            continue

        max_demand_transfer_factor = model.breakpoints[-1][0]

        _, _, demands = zip(*model.odpairs)
        total_demand = sum([int(d * max_demand_transfer_factor)
                           for d in demands])

        data = get_row_from_model(model_path, model, solution, total_demand)
        rows.append(data)
        instances.append((data['name'], model, solution))

    return instances, pd.DataFrame(rows).sort_values(by=sort_by_columns)


def draw_instances(
    data_dir,
    instances,
    width=2,
    flow_scale_factor=5,
    odpairs=True,
    flows=True,
    dpi=300,
    fig_height=7,
    fig_width=15,
    with_labels=True,
    node_size=None,
):
    """
    Draw instances and solutions
    """
    for model_name, model, solution in instances:
        fig_filename = os.path.join(data_dir, f'{model_name}.png')

        if os.path.exists(fig_filename):
            continue

        if flows:
            fig, (ax1, ax2) = plt.subplots(1, 2)
        else:
            fig, ax1 = plt.subplots()

        draw_params = dict(
            solution=solution,
            width=width,
            legend_location='lower right',
            # margins=[0.02],
            with_labels=with_labels,
        )

        if node_size:
            draw_params['node_size'] = node_size

        draw_model = functools.partial(
            bc.draw.draw,
            model,
            **draw_params,
        )

        draw_model(
            odpairs=False,
            infrastructures=True,
            ax=ax1,
        )

        if flows:
            draw_model(
                odpairs=odpairs,
                flows=True,
                flow_scale_factor=flow_scale_factor,
                infrastructures=False,
                ax=ax2,
            )

        fig.subplots_adjust(wspace=0.0)
        fig.set_size_inches(fig_width, fig_height)
        fig.savefig(fig_filename, dpi=dpi, bbox_inches='tight')
        plt.close(fig)


def summarize_solutions_to_csv(output_file, instances):
    """
    Write csv with solutions information
    - budget spent per infrastructure
    - infra length
    """

    distance_key = 'distance'

    def generate_row(model_name, model, solution):
        """
        Compute stuff for single instance
        """
        infra_costs = bc.misc.group_by(
            solution.data.infrastructures, 'infrastructure')
        budget_used = solution.budget_used

        cost_by_infra = [
            (f'infra_{key}', sum(
                map(lambda d: d.construction_cost, value)) / budget_used * 100)
            for key, value in infra_costs.items()
        ]

        total_arc_distance = sum(nx.get_edge_attributes(
            model.graph, distance_key).values())
        arcs_by_id = bc.misc.get_arcs_by_key(model.graph)
        length_covered_by_infra = [
            (f'infra_{key}_length_percentage', sum(
                map(lambda d: model.graph.edges[arcs_by_id[d.arc]]
                    [distance_key], value)
            ) / total_arc_distance * 100)
            for key, value in infra_costs.items()
        ]
        infra_total_length = sum(list(zip(*length_covered_by_infra))[1])

        demand_transfered_by_od = [
            (f'od_{entry.origin}_{entry.destination}', entry.demand_transfered)
            for entry in solution.data.demand_transfered
        ]

        function_name = get_function_name(model_name)
        function_readable_name = get_function_readable_name(function_name)

        return OrderedDict(
            cost_by_infra +
            length_covered_by_infra +
            demand_transfered_by_od +
            [
                ('infra_total_length', infra_total_length),
                ('budget_factor', model._budget_factor),
                ('budget', model.budget),
                ('budget_used', solution.budget_used),
                ('budget_used_percentage', solution.budget_used / model.budget),
                ('breakpoint_count', len(model.breakpoints)),
                ('total_demand_transfered', solution.total_demand_transfered),
                ('name', model_name),
                ('transfer_function', function_name),
                ('transfer_function_name', function_readable_name),
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

    return df


def draw_budget_used_by_infrastructure(budget_use_df, output_path):
    """
    For each instance, draw the budget used as a stacked histogram
    where worse infrastructures and on lower positions. Percentages
    are normalized by budget used percentage so they always sum 100%.
    """
    fig, ax = plt.subplots(figsize=(8, 4))
    budget_use_df = budget_use_df.fillna(0.0)

    def get_infra_i_data(infra_num):
        return np.array([
            row.get(f'infra_{infra_num}', 0.0)
            for _index, row in budget_use_df.iterrows()
        ])

    labels = list(range(1, len(budget_use_df) + 1))
    bottom = [0] * len(labels)

    for infra_num in range(1, 6):
        current = get_infra_i_data(infra_num)
        if not any(current):
            continue

        ax.bar(
            labels,
            current,
            width=0.75,
            bottom=bottom,
            color=bc.draw.default_infra_colors[infra_num - 1],
            label=f'Tecn. {infra_num}',
        )
        bottom += current

    ax.set_ylabel('Distribución del presupuesto utilizado')
    yticks = list(range(10, 101, 10))
    ax.set_yticks(yticks)
    ax.set_yticklabels(list(map(lambda v: f'{v} %', yticks)))
    ax.set_xlabel('Instancia')
    ax.set_xticks(labels)
    ax.tick_params(axis='x', labelsize='x-small')
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=300)


def draw_demand_transfered_by_budget(
    executions_df, output_path, functions=['lineal', 'logit'],
):
    """
    Plot demand transfer percentage by budget
    for lineal function.
    """
    fig, ax = plt.subplots(figsize=(6, 4.5))

    for index, function_name in enumerate(functions):
        df = executions_df[executions_df.transfer_function == function_name]
        ax.plot(
            df.budget,
            df.total_demand_transfered_percentage,
            color=colors[index],
            label=get_function_readable_name(function_name),
        )

    ax.set_xlabel('Presupuesto')
    ax.set_ylabel('Demanda transferida (%)')
    ax.legend()
    fig.tight_layout()

    fig.savefig(output_path, dpi=300)


def save_document_csvs(data_dir, executions_df, budget_use_df):
    """
    Generate csvs out of full dataframes to be used in the documentation.
    """

    def preprocess_short_df(df):
        return df.assign(instance=range(1, len(df) + 1)).round(2)

    preprocess_short_df(executions_df)[
        [
            'instance',
            'budget_factor',
            'transfer_function_name',
            'affected_odpair_count',
            'total_demand_transfered_percentage',
            'run_time_seconds_str',
        ]
    ].to_csv(os.path.join(data_dir, 'aexecution_summary_short.csv'), index=False)

    infra_keys = list(sorted(filter(lambda col: re.match(
        r'^infra_\d+$', col), budget_use_df.columns)))

    preprocess_short_df(budget_use_df)[
        ['instance', 'budget', 'budget_used'] + sorted(infra_keys)
    ].to_csv(os.path.join(data_dir, 'abudget_use_summary_short.csv'), index=False)

    infra_length_cols = list(sorted(filter(lambda col: re.match(
        r'^infra_\d+_length', col), budget_use_df.columns)))

    preprocess_short_df(budget_use_df)[
        ['instance'] + infra_length_cols + ['infra_total_length']
    ].to_csv(os.path.join(data_dir, 'ainfra_length_proportions.csv'), index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('data_dir')
    parser.add_argument('--skip-instance-drawing', action='store_true')
    parser.add_argument(
        '--demand-by-budget-breakpoint-count', type=int, default=20)
    parser.add_argument(
        '--draw-width', type=float, default=2.0)
    parser.add_argument(
        '--draw-flow-scale-factor', type=int, default=5)
    parser.add_argument(
        '--draw-skip-odpairs', action='store_true')
    parser.add_argument(
        '--draw-dpi', type=int, default=300)
    parser.add_argument(
        '--draw-fig-height', type=int, default=7)
    parser.add_argument(
        '--draw-fig-width', type=int, default=13)
    parser.add_argument(
        '--draw-skip-flows', action='store_true')
    parser.add_argument(
        '--draw-node-size', type=float, default=None)
    parser.add_argument(
        '--draw-skip-labels', action='store_true')

    args = parser.parse_args(sys.argv[1:])

    instances, executions_df = generate_runs_dataframe(args.data_dir)

    executions_df.to_csv(os.path.join(
        args.data_dir, 'aexecution_summary.csv'), index=False)

    if not args.skip_instance_drawing:
        draw_instances(
            args.data_dir,
            instances,
            width=args.draw_width,
            flow_scale_factor=args.draw_flow_scale_factor,
            odpairs=not args.draw_skip_odpairs,
            flows=not args.draw_skip_flows,
            dpi=args.draw_dpi,
            fig_width=args.draw_fig_width,
            fig_height=args.draw_fig_height,
            node_size=args.draw_node_size,
            with_labels=not args.draw_skip_labels,
        )

    budget_use_df = summarize_solutions_to_csv(
        os.path.join(args.data_dir, 'abudget_use_summary.csv'),
        instances,
    )

    save_document_csvs(args.data_dir, executions_df, budget_use_df)

    draw_budget_used_by_infrastructure(
        budget_use_df,
        os.path.join(args.data_dir, 'abudget_use_by_infra.png'),
    )

    draw_demand_transfered_by_budget(
        executions_df[executions_df.breakpoint_count ==
                      args.demand_by_budget_breakpoint_count],
        os.path.join(args.data_dir, 'ademand_by_budget.png'),
    )


if __name__ == '__main__':
    main()
