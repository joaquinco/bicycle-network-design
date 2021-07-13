import os
import subprocess


def run_cbc(project_root, data_file, solution_file, timeout=None, model_name=''):
    """
    Run cbc solver.

    data_file must be relative to project root.
    """
    project_abs_dir = project_root
    if not project_root.startswith('/'):
        project_abs_dir = os.path.join(os.getcwd(), project_root)

    return subprocess.run(
        ['./bin/cbc', data_file, solution_file],
        cwd=project_abs_dir,
        timeout=timeout,
        capture_output=True,
        text=True,
        check=False,
        env={
            **os.environ,
            'BCNETWORK_MODEL_NAME': model_name,
        },
    )
