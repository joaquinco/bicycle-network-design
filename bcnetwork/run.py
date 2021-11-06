import os
import subprocess
import datetime


supported_solvers = ['glpsol', 'cbc', 'ampl']


def run_solver(project_root, data_file, solution_file, timeout=None, model_name='', solver='cbc'):
    """
    Run the specified solver.

    data_file must be relative to project root.
    """
    if not solver in supported_solvers:
        raise ValueError(f'Solver must be one of {supported_solvers}')

    project_abs_dir = project_root
    if not project_root.startswith('/'):
        project_abs_dir = os.path.join(os.getcwd(), project_root)

    start_time = datetime.datetime.now()
    process = subprocess.run(
        ['./bin/solve', data_file, solution_file],
        cwd=project_abs_dir,
        capture_output=True,
        text=True,
        check=False,
        env={
            **os.environ,
            'BCNETWORK_MODEL_NAME': model_name,
            'BCNETWORK_SOLVER': solver,
            'BCNETWORK_TIMEOUT': str(timeout),
        },
    )
    run_time = datetime.datetime.now() - start_time

    return process, run_time.total_seconds()
