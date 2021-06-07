import copy
import os
import random

import yaml

from .cache import cached_property
from .persistance import (
    read_graph_from_yaml,
    read_graph_from_csvs,
    write_graph_to_yaml,
    read_graph_from_yaml,
)
from .transform import graph_to_mathprog, origin_destination_pairs_to_mathprog


class Model:
    def __init__(
        self,
        graph=None,
        graph_file=None,
        nodes_file=None,
        arcs_file=None,
        budget=None,
        odpairs=None,
        breakpoints=None,
        user_cost_weight='distance'
    ):
        self._graph = graph
        self.graph_file = graph_file
        self.nodes_file = nodes_file
        self.arcs_file = arcs_file
        self.budget = budget
        self.odpairs = odpairs
        self.breakpoints = breakpoints

    @cached_property
    def graph(self):
        """
        Returns a networkx graph instance
        """
        if self._graph:
            return self._graph

        if self.nodes_file and self.arcs_file:
            return read_graph_from_csvs(self.nodes_file, self.arcs_file)

        if self.graph_file:
            return read_graph_from_yaml(self.graph_file)

        raise ValueError(
            'Missing graph, graph_file or nodes_file and arcs_file')

    def write_data(self, output):
        """
        Write model to mathprog
        """
        output.write("data;\n\n")
        graph_to_mathprog(self.graph, output)
        origin_destination_pairs_to_mathprog(
            self.graph,
            self.odpairs,
            self.breakpoints,
            output,
        )

        output.write(f"param B := {self.budget};\n")
        output.write("end;\n")

    def save(self, path):
        """
        Save this model to a file. 
        The graph is also saved to a new file.
        """
        base_path_name, _ = os.path.splitext(path)
        graph_file = f'{base_path_name}.graph.yaml'

        model_to_save = copy.copy(self)
        model_to_save._graph = None
        model_to_save.arcs_file = None
        model_to_save.nodes_file = None
        model_to_save.graph_file = graph_file

        write_graph_to_yaml(self.graph, graph_file)
        with open(path, 'w') as file:
            file.write(yaml.dump(model_to_save))

    @classmethod
    def load(cls, path):
        with open(path, 'r') as f:
            return yaml.load(f.read(), Loader=yaml.Loader)


class RandomModel(Model):
    def __init__(self, *args, odpair_count=5, breakpoint_count=4, **kwargs):
        super().__init__(*args, **kwargs)

        self.odpair_count = 5
        self.breakpoint_count = 4
        self._generated = False

    def _generate_random_data(self):
        nodes = list(self.graph.nodes())
        origins = random.sample(nodes, self.odpair_count)
        destinations = random.sample(nodes, self.odpair_count)
        demands = [int(random.uniform(100, 1000))
                   for i in range(self.odpair_count)]

        improvements_breakpoints = [
            1] + list(sorted([random.uniform(0.8, 1) for i in range(self.breakpoint_count)], reverse=True))
        transfer_breakpoints = [
            0] + list(sorted([random.uniform(0, 1) for i in range(self.breakpoint_count)]))

        self.odpairs = list(zip(origins, destinations, demands))
        self.breakpoints = list(
            zip(transfer_breakpoints, improvements_breakpoints))

    def write_data(self, output):
        if not self._generated:
            self._generate_random_data()

        super().write_data(output)
