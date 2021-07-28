from functools import partial
import traceback
import sys
import os
import random
from multiprocessing import Pool

import pandas as pd

import bcnetwork as bc


project_root = '.'
data_dir = os.path.join(project_root, 'instances/sioux-falls/')
nodes_file = os.path.join(data_dir, 'nodes.csv')
arcs_file = os.path.join(data_dir, 'arcs.csv')

build_random_model = partial(
    bc.model.RandomModel,
    name='Sioux-Falls',
    nodes_file=nodes_file,
    arcs_file=arcs_file,
    project_root=project_root,
)


uniform_range = [1, 20]
model_names = ['', 'single_level_v2', 'single_level_v3', 'single_level_v4']
use_glpsol_opts = [True]


class ModelError(Exception):
    def __init__(self, model, solution, exception):
        self.model = model
        self.solution = solution
        self.exception = exception


def runner(index, model, model_name, use_glpsol):
    solution = model.solve(model_name=model_name, use_glpsol=use_glpsol)
    print('.', end='')

    try:
        errors = model.validate_solution(solution)
    except Exception as e:
        e.tb = traceback.format_exc()
        raise ModelError(model, solution, e)

    return dict(
        solution=solution,
        model=model,
        model_name=solution.model_name,
        errors=errors,
        use_glpsol=use_glpsol,
        index=index,
    )


def pool_runner(args):
    return runner(*args)


def run_model_examples(number_of_examples, worker_count):
    run_opts = []

    for i in range(number_of_examples):
        odpair_count = int(random.uniform(*uniform_range))
        model = build_random_model(odpair_count=odpair_count)
        # Generate random data so that it's the same
        # when loaded on workers
        model._generate_random_data()
        for model_name in model_names:
            for use_glpsol in use_glpsol_opts:
                run_opts.append((i, model, model_name, use_glpsol))

    with Pool(worker_count) as pool:
        ret = pool.map(pool_runner, run_opts)

    print()
    return ret


def save_error_models(runs, target_dir):
    """
    Loop over runs and save models whose
    solution was not valid.
    """
    err_indexes = set()

    for run in runs:
        index = run['index']
        if not run['errors']:
            continue
        print("Run ", index)
        if run['errors'] and index not in err_indexes:
            err_indexes.add(index)
            run['model'].save(os.path.join(
                target_dir, f'/test_model_{index}.yaml'))


def extract_data(run):
    s = run['solution']

    return {
        'demand_transfered': s.total_demand_transfered,
        'budget_used': s.budget_used,
        'model_name': s.model_name,
        'od_count': len(s.data.shortest_paths),
        'model': run['index'],
    }


def save_dataframes(runs, target_dir):
    data = list(map(extract_data, runs))

    df = pd.DataFrame(data)

    def get_different_runs(df):
        def model_name(rows):
            return ' '.join(rows.tolist())

        difdf = df \
            .groupby(['model', 'demand_transfered'], as_index=False)['model_name'] \
            .agg([model_name, 'size']) \
            .rename(columns={'size': 'mcount'}) \
            .reset_index()

        difdf = difdf[difdf.mcount != len(model_names)]

        return difdf

    difdf = get_different_runs(df)

    df.to_csv(os.path.join(target_dir, 'rundata.csv'))
    difdf.to_csv(os.path.join(target_dir, 'rundifs.csv'))


def main():
    number_of_examples = int(os.environ.get('BCNETWORK_NUM_EXAMPLES', 10))
    target_dir = os.environ['BCNETWORK_TARGET_DIR']
    number_of_workers = int(os.environ.get('BCNETWORK_NUM_WORKERS', 4))

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    runs = run_model_examples(number_of_examples, number_of_workers)
    save_error_models(runs, target_dir)
    save_dataframes(runs, target_dir)


if __name__ == '__main__':
    main()
