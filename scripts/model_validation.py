import argparse
import re
import os
import sys
import pickle

from multiprocessing import Pool

import bcnetwork as bc


default_model_names = [
    '',
    'single_level_v2',
    'single_level_v3',
    'single_level_v4',
    'single_level_v5',
    'single_level_v6',
]

instnace_index_re = re.compile(r'.*?(\d+).*')


def perform_run(
    model_full_path,
    model_name,
    solver,
    ignore_existing,
    solved_only,
    solution_template,
    save_solutions,
    project_root,
):
    """
    Perform a single run/check/verification for a model instance and model_name
    """

    if model_full_path.endswith('yaml'):
        model = bc.model.Model.load_yaml(model_full_path)
    else:
        model = bc.model.Model.load(model_full_path)
    if project_root:
        model.project_root = project_root

    models_dir = os.path.dirname(model_full_path)
    current_instance, _ext = os.path.splitext(
        os.path.basename(model_full_path))

    hr_model_name = model_name or 'default'
    solution_basename = solution_template.format(
        instance=current_instance, model_name=hr_model_name,
    )

    solution_filename = os.path.join(
        models_dir, solution_basename
    )
    print(solution_filename)

    solution_existed = not ignore_existing and os.path.exists(
        solution_filename)
    if solution_existed:
        print(f'Reading existing solution {solution_filename}')
        s = bc.solution.Solution.load(solution_filename)
    elif not solved_only:
        s = model.solve(model_name=model_name, solver=solver)
    else:
        print(
            f'Skipping {hr_model_name} for instance {current_instance}')
        return

    e = model.validate_solution(s)
    print(
        f'Solution for: {current_instance}. Model {hr_model_name} demand transfered: {s.total_demand_transfered}, run time: {s.run_time_seconds}'
    )

    if save_solutions and not solution_existed:
        s.save(solution_filename)
    if e:
        print(
            f'error on {current_instance}, {hr_model_name} using {s.solver}')
        print(e)


def pool_perform_run(args):
    perform_run(*args)


def perform(
    models_dir,
    worker_count=1,
    model_names=None,
    instance_whitelist=None,
    save_solutions=False,
    solver=None,
    ignore_existing=False,
    solved_only=False,
    solution_template=None,
    project_root=None,
):
    model_names = model_names or default_model_names

    blacklist = ['graph', 'solution']
    whitelist = ['pkl', 'yaml']

    def generate_runs():
        for path in os.scandir(models_dir):
            if not any(map(lambda x: x in path.name, whitelist)) or any(map(lambda x: x in path.name, blacklist)):
                continue

            if instance_whitelist and not any(map(lambda x: x in path.name, instance_whitelist)):
                continue

            model_full_path = os.path.join(models_dir, path.name)
            for model_name in model_names:
                yield (model_full_path, model_name)

    params = [
        solver,
        ignore_existing,
        solved_only,
        solution_template,
        save_solutions,
        project_root,
    ]

    with Pool(worker_count) as pool:
        pool.map(pool_perform_run, [(full_path, model_name, *params)
                 for full_path, model_name in generate_runs()])


def parse_arguments(rawargs):
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--model-name', nargs='*')
    parser.add_argument('-w', '--whitelist', nargs='*')
    parser.add_argument('--save-solutions', action='store_true')
    parser.add_argument('--ignore-existing', action='store_true')
    parser.add_argument(
        '--solver', choices=bc.run.supported_solvers, default='cbc')
    parser.add_argument('--solved-only', action='store_true')
    parser.add_argument('--solution-template',
                        default='{instance}_solution_{model_name}.pkl')
    parser.add_argument('--project-root')
    parser.add_argument('--parallelism', type=int, default=1)
    parser.add_argument('path')

    return parser.parse_args(rawargs)


def main():
    args = parse_arguments(sys.argv[1:])

    perform(
        args.path,
        worker_count=args.parallelism,
        model_names=args.model_name,
        instance_whitelist=args.whitelist,
        save_solutions=args.save_solutions,
        solver=args.solver,
        ignore_existing=args.ignore_existing,
        solved_only=args.solved_only,
        solution_template=args.solution_template,
        project_root=args.project_root,
    )


if __name__ == '__main__':
    main()
