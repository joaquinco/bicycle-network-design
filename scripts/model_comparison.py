from functools import partial
import traceback
import sys
import os
import pickle
import random
from multiprocessing import Pool, Manager, Process
import datetime

import bcnetwork as bc


project_root = '.'
data_dir = os.path.join(project_root, 'instances/sioux-falls/')
nodes_file = os.path.join(data_dir, 'nodes.csv')
arcs_file = os.path.join(data_dir, 'arcs.csv')

finish_token = 'finished'

build_random_model = partial(
    bc.model.RandomModel,
    name='Sioux-Falls',
    nodes_file=nodes_file,
    arcs_file=arcs_file,
    project_root=project_root,
)


od_uniform_range = [1, 14]
breakpoint_uniform_range = [2, 10]
model_names = [
    '',
    'single_level_v2',
    'single_level_v3',
    'single_level_v4',
    'single_level_v5',
    'single_level_v6',
]


class ModelError(Exception):
    def __init__(self, model, solution, exception):
        self.model = model
        self.solution = solution
        self.exception = exception


def runner(index, model, model_name, solver):
    solution = model.solve(model_name=model_name, solver=solver)
    print('.', end='')

    try:
        errors = model.validate_solution(solution)
    except Exception as e:
        e.tb = traceback.format_exc()
        raise ModelError(model, solution, e)

    return dict(
        solution=solution,
        model=model,
        errors=errors,
        solver=solver,
        index=index,
    )


def pool_runner(args):
    queue, *run_args = args
    run_data = runner(*run_args)
    queue.put(run_data)


def extract_data(run):
    s = run['solution']
    m = run['model']

    return {
        'demand_transfered': s.total_demand_transfered,
        'budget_used': s.budget_used,
        'model_name': s.model_name,
        'od_count': m.odpair_count,
        'breakpoint_count': m.breakpoint_count,
        'model': run['index'],
        'has_errors': bool(run['errors']),
        'run_time_seconds': s.run_time_seconds,
    }


def write_to_file(csv_path, value, append=False):
    flags = 'a' if append else 'w'

    with open(csv_path, flags) as f:
        f.write(value)
        f.write('\n')


def run_processor(queue, target_dir):
    headers = None
    separator = ','
    run_count = 0

    now_iso = datetime.datetime.now().isoformat()
    runs_csv_path = os.path.join(target_dir, f'runs_{now_iso}.csv')

    while True:
        try:
            run = queue.get()

            if run == finish_token:
                break

            run_count += 1
            index = run['index']
            model_path = os.path.join(target_dir, f'test_model_{index}.pkl')
            if not os.path.exists(model_path):
                run['model'].save(model_path)
            data = extract_data(run)

            print('Processed index {model} model {model_name}'.format(**data))

            if headers is None:
                headers = list(data.keys())
                write_to_file(runs_csv_path, separator.join(headers))

            write_to_file(
                runs_csv_path,
                separator.join(map(str, [data[key] for key in headers])),
                append=True,
            )
            solution_filename = 'solution_{model}_{model_name}.pkl'.format(
                **data)
            with open(os.path.join(target_dir, solution_filename), 'wb') as f:
                pickle.dump(run['solution'], f)
        except ValueError:
            # Queue closed
            break

    print(f'Queue closed, received {run_count} runs')


def run_model_examples(number_of_examples, worker_count, target_dir, solver):
    run_opts = []

    for i in range(number_of_examples):
        odpair_count = int(random.uniform(*od_uniform_range))
        breakpoint_count = int(random.uniform(*breakpoint_uniform_range))

        print(
            f'Model #{i} - od_count: {odpair_count}, breakpoint_count: {breakpoint_count}')
        model = build_random_model(
            odpair_count=odpair_count, breakpoint_count=breakpoint_count
        )
        # Generate random data so that it's the same
        # when loaded on workers
        model._generate_random_data()
        for model_name in model_names:
            run_opts.append((i, model, model_name, solver))

    manager = Manager()
    queue = manager.Queue()
    run_process = Process(target=run_processor, args=(queue, target_dir))
    run_process.start()
    with Pool(worker_count) as pool:
        pool.map(pool_runner, map(lambda run_opt: [queue, *run_opt], run_opts))
    queue.put(finish_token)

    run_process.join()


def main():
    number_of_examples = int(os.environ.get('BCNETWORK_NUM_EXAMPLES', 10))
    target_dir = os.environ['BCNETWORK_TARGET_DIR']
    number_of_workers = int(os.environ.get('BCNETWORK_NUM_WORKERS', 4))
    solver = os.environ.get('BCNETWORK_SOLVER', 'cbc')

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    run_model_examples(
        number_of_examples,
        number_of_workers,
        target_dir,
        solver,
    )


if __name__ == '__main__':
    main()
