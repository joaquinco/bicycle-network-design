import os
from unittest import TestCase
import tempfile

import networkx as nx

from bcnetwork.model import RandomModel
from bcnetwork.persistance import write_graph_to_yaml, read_graph_from_csvs


class ModelTestCase(TestCase):
    def setUp(self):
        self.temp_file = None
        self.nodes_file = 'bcnetwork/tests/resources/nodes.csv'
        self.arcs_file = 'bcnetwork/tests/resources/arcs.csv'
        self.graph = read_graph_from_csvs(
            self.nodes_file, self.arcs_file
        )
        self.graph_file = '/tmp/graph.bcnetwork.test.yaml'
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
        self.temp_file = tempfile.mktemp(prefix='bcnetwork.', suffix='.yaml')

        model = RandomModel(graph=self.graph)
        model.save(self.temp_file)

        self.assertGreater(os.path.getsize(self.temp_file), 0)

    def test_load_success(self):
        self.temp_file = tempfile.mktemp(prefix='bcnetwork.', suffix='.yaml')

        model = RandomModel(graph=self.graph)
        model.save(self.temp_file)

        loaded_model = RandomModel.load(self.temp_file)

        self.assertIsInstance(loaded_model, RandomModel)
        self.assertIsInstance(loaded_model.graph, nx.DiGraph)

    def test_write_data_success(self):
        model = RandomModel(graph=self.graph)
        self.temp_file = tempfile.mktemp(prefix='bcnetwork.', suffix='.dat')

        with open(self.temp_file, 'w') as f:
            model.write_data(f)

        self.assertGreater(os.path.getsize(self.temp_file), 0)

    def test_run(self):
        model = RandomModel(graph=self.graph)

        solution = model.run()

        self.assertIsNotNone(solution)

    def tearDown(self):
        os.remove(self.graph_file)

        if self.temp_file:
            os.remove(self.temp_file)
