import contextlib
import functools
import os
from unittest import TestCase, mock
import tempfile
import shutil

import networkx as nx

from bcnetwork.model import RandomModel
from bcnetwork.persistance import write_graph_to_yaml, read_graph_from_csvs
from bcnetwork.validation import Errors

from .utils import get_resource_path

original_mkstemp = tempfile.mkstemp


def mock_solve_mkstemp(*args, suffix=None, **kwargs):
    _, temp_out = original_mkstemp(suffix=suffix, **kwargs)

    if 'cplex.sol' in suffix:
        shutil.copyfile(get_resource_path('cplex.sol'), temp_out)
    elif 'cplex.out' in suffix:
        shutil.copyfile(get_resource_path('stdout.cplex'), temp_out)
    elif 'out' in suffix:
        shutil.copyfile(get_resource_path('stdout.cbc'), temp_out)

    return (1, temp_out)


@contextlib.contextmanager
def mock_run_solver():
    """
    Mock solver run.

    Returns a mocked subprocess.run mock with stdout and returncode set.
    """
    run_cbc_mock = mock.MagicMock(
        returncode=0,
    )

    with contextlib.ExitStack() as stack:
        stack.enter_context(
            mock.patch(
                'bcnetwork.model.tempfile.mkstemp',
                new=mock_solve_mkstemp,
            )
        )
        stack.enter_context(
            mock.patch(
                'bcnetwork.run.subprocess.run',
                return_value=run_cbc_mock,
            )
        )

        yield run_cbc_mock


class ModelTestCase(TestCase):
    def setUp(self):
        self.temp_file = None
        self.nodes_file = get_resource_path('nodes.csv')
        self.arcs_file = get_resource_path('arcs.csv')
        self.odpairs_file = get_resource_path('demands.csv')

        self.graph = read_graph_from_csvs(
            self.nodes_file, self.arcs_file
        )
        self.graph_file = '/tmp/graph.bcnetwork.test.yaml'

        self.odpairs = [
            ('6', '1', 754),
            ('12', '12', 812),
            ('2', '5', 136),
            ('13', '2', 989),
            ('8', '6', 502),
        ]
        write_graph_to_yaml(self.graph, self.graph_file)

    def test_init_success(self):
        self.assertTrue(bool(RandomModel(graph=self.graph)))

    def test_read_csv_success(self):
        model = RandomModel(nodes_file=self.nodes_file,
                            arcs_file=self.arcs_file)

        self.assertIsInstance(model.graph, nx.DiGraph)

    def test_read_graph_success(self):
        model = RandomModel(graph_file=self.graph_file)

        self.assertIsInstance(model.graph, nx.DiGraph)

    def test_save_success(self):
        self.temp_file = tempfile.mktemp(prefix='bcnetwork.', suffix='.pkl')

        model = RandomModel(graph=self.graph)
        model.save(self.temp_file)

        self.assertGreater(os.path.getsize(self.temp_file), 0)

    def test_load_success(self):
        self.temp_file = tempfile.mktemp(prefix='bcnetwork.', suffix='.pkl')

        model = RandomModel(graph=self.graph)
        model.save(self.temp_file)

        loaded_model = RandomModel.load(self.temp_file)

        self.assertIsInstance(loaded_model, RandomModel)
        self.assertIsInstance(loaded_model.graph, nx.DiGraph)

    def test_save_load_with_solution_success(self):
        self.temp_file = tempfile.mktemp(prefix='bcnetwork.', suffix='.pkl')

        model = RandomModel(graph=self.graph)

        with mock_run_solver():
            solution = model.solve()

        self.assertIsNotNone(solution)
        model.save(self.temp_file)

        self.assertGreater(os.path.getsize(self.temp_file), 0)

        loaded_model = RandomModel.load(self.temp_file)

        self.assertIsInstance(loaded_model, RandomModel)
        self.assertIsInstance(loaded_model.graph, nx.DiGraph)

    def test_write_data_success(self):
        model = RandomModel(graph=self.graph)
        self.temp_file = tempfile.mktemp(prefix='bcnetwork.', suffix='.dat')

        model.write_data(self.temp_file)

        self.assertGreater(os.path.getsize(self.temp_file), 0)

    def test_solve(self):
        model = RandomModel(graph=self.graph)

        model_name = 'test_model'
        with mock_run_solver():
            solution = model.solve(model_name=model_name)

        self.assertIsNotNone(solution)
        self.assertEqual(solution.model_name, model_name)
        self.assertIsNotNone(solution.solver)
        self.assertGreater(solution.run_time_seconds, 0)

    def test_solve_linear(self):
        model = RandomModel(graph=self.graph)

        with mock_run_solver():
            solution = model.solve(model_name='linear')

        self.assertIsNotNone(solution)

    def test_validate_solution(self):
        model = RandomModel(graph=self.graph, odpairs=self.odpairs)

        with mock_run_solver():
            solution = model.solve()

        errors = model.validate_solution(solution)

        self.assertIsInstance(errors, Errors)

    def test_validate_read_odpairs_file(self):
        model = RandomModel(graph=self.graph, odpairs_file=self.odpairs_file)

        self.assertIsInstance(model.odpairs, list)
        self.assertGreater(len(model.odpairs), 1)

    def test_solve_with_output_dir(self):
        model = RandomModel(graph=self.graph, odpairs=self.odpairs)

        output_dir = tempfile.mkdtemp()
        with mock_run_solver():
            solution = model.solve(output_dir=output_dir)

        self.assertEqual(len(list(os.scandir(output_dir))), 2)

    def test_solve_with_cplex(self):
        model = RandomModel(graph=self.graph, odpairs=self.odpairs)

        with mock_run_solver():
            solution = model.solve(solver='cplex')

        self.assertIsNotNone(solution)

    def test_solve_with_cplex_and_output_dir(self):
        model = RandomModel(graph=self.graph, odpairs=self.odpairs)

        output_dir = tempfile.mkdtemp()
        with mock_run_solver():
            solution = model.solve(output_dir=output_dir, solver='cplex')

        self.assertEqual(len(list(os.scandir(output_dir))), 3)

    def test_apply_solution(self):
        model = RandomModel(graph=self.graph, odpairs=self.odpairs)
        model_new = RandomModel(graph=self.graph, odpairs=self.odpairs)

        with mock_run_solver():
            solution = model.solve()

        model_new._generate_random_data()
        new_solution = model_new.apply_to_solution(solution)

        self.assertNotEqual(new_solution.data, solution.data)
        self.assertTrue(new_solution.data.shortest_paths)

    def tearDown(self):
        os.remove(self.graph_file)

        if self.temp_file:
            os.remove(self.temp_file)
