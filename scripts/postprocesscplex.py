import argparse
import re
import csv
from functools import partial
import sys
import os

from matplotlib import pyplot as plt
import matplotlib

from misc import format_run_time_seconds

import bcnetwork as bc


draw_config = dict(
    figsize=(15, 12),
)


runtime_regex = r"Solution time =\s+((\d+)(\.\d+)?) sec."


def get_runtime_seconds(instance_basepath):
    """
    Reads runtime seconds from output file.
    """
    with open(f'{instance_basepath}.sol.out', 'r') as file:
        reg = re.compile(runtime_regex)
        for line in file:
            match = reg.match(line)
            if match:
                return float(match[1])

    raise Exception('Couldn\'t find runtime for ' + instance_basepath)


def get_instances(data_path):
    """
    Read models and solutions
    """
    instances = []

    for entry in os.scandir(data_path):
        if 'sol' in entry.path or not entry.path.endswith('pkl'):
            continue

        instance_basepath, _ = os.path.splitext(entry.path)
        instance_name = os.path.basename(instance_basepath)

        solution_path = os.path.join(
            data_path, f'solution_{instance_name}.pkl')
        if not os.path.exists(solution_path):
            print(f'Solution for {instance_name} not found, skipping')
            continue

        model = bc.model.Model.load(entry.path)
        solution = bc.solution.Solution.load(solution_path)

        model.name = instance_name
        model.save(entry.path)

        if not solution.run_time_seconds:
            solution.run_time_seconds = get_runtime_seconds(instance_basepath)

        solution.save(solution_path)

        instances.append((model, solution))

    return instances


def draw_to_file(filename, *args, **kwargs):
    fig, ax = plt.subplots()

    bc.draw.draw(
        *args,
        ax=ax,
        **{
            **draw_config,
            **kwargs,
        }
    )

    fig.savefig(filename)


def draw_solution(data_dir, model, solution):
    """
    Draw solution.
    """
    draw_to_file(
        os.path.join(data_dir, f'{model.name}_infras.png'),
        model,
        solution=solution,
        odpairs=False,
        infrastructures=True,
    )
    draw_to_file(
        os.path.join(data_dir, f'{model.name}_flows.png'),
        model,
        solution=solution,
        odpairs=False,
        infrastructures=False,
        flows=True,
    )


def draw_model_data(data_dir, model):
    """
    Draw model data:
    - origin, destination, demand distribution.
    """
    show_top = 200
    fig, axs = plt.subplots(nrows=1, ncols=2)
    ax1, ax2 = axs
    bc.draw.draw(model, odpairs=False, ax=ax1)
    bc.draw.draw_demand_weight(
        ax1, model, destination_color=None, show_top=show_top)

    bc.draw.draw(model, odpairs=False, ax=ax2)
    bc.draw.draw_demand_weight(
        ax2, model, origin_color=None, show_top=show_top)

    fig.set(size_inches=(15, 7))
    fig.suptitle(f'Primeros {show_top} pares origen-destino con mayor demanda')

    ax1.set_title('Orígenes')
    ax2.set_title('Destinos')
    fig.savefig(os.path.join(data_dir, 'montevideo_demands.png'))


def main():
    """
    Generar archivos compatibles con los de sensibility y usar el script
    de processsensibility
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('data_dir')
    args = parser.parse_args(sys.argv[1:])

    matplotlib.rcParams['figure.autolayout'] = True

    instances = get_instances(args.data_dir)
    for model, instance in instances:
        draw_solution(args.data_dir, model, instance)

    model, _ = instances[0]
    draw_model_data(args.data_dir, model)


if __name__ == '__main__':
    main()
