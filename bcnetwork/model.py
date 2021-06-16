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
from .draw import draw_graph
from .solution import Solution


class Model:
    def __init__(
        self,
        graph=None,
        graph_file=None,
        nodes_file=None,
        arcs_file=None,
        budget=None,
        budget_factor=None,
        odpairs=None,
        breakpoints=None,
        user_cost_weight='user_weight',
        infrastructure_count=2,
    ):
        self._graph = graph
        self.graph_file = graph_file
        self.nodes_file = nodes_file
        self.arcs_file = arcs_file
        self._budget = budget
        self._budget_factor = budget_factor
        self.odpairs = odpairs
        self.breakpoints = breakpoints
        self.infrastructure_count = infrastructure_count

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

    @cached_property
    def budget(self):
        """
        Return absolute budget value.
        If budget was provided use that, else return
        the budget_factor proportion of constructing all base infrastructures.
        """
        if self._budget is not None:
            return self._budget

        total_cost = sum([self.graph.edges[n1, n2]['construction_weight']
                          for (n1, n2) in self.graph.edges()])

        return total_cost * self._budget_factor

    def write_data(self, output):
        """
        Write model to mathprog
        """
        output.write("data;\n\n")
        graph_to_mathprog(self.graph, output,
                          infrastructure_count=self.infrastructure_count)
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

    def set_solution(self, stdout_file):
        self.solution = Solution(stdout_file=stdout_file)

class RandomModel(Model):
    def __init__(self, *args, odpair_count=5, breakpoint_count=4, budget_factor=0.1, **kwargs):
        super().__init__(*args, **kwargs)

        self.odpair_count = 5
        self.breakpoint_count = 4
        self._budget_factor = budget_factor

    def _generate_random_data(self):
        """
        Generate random data if needed
        """
        if self.odpairs is None:
            nodes = list(self.graph.nodes())
            origins = random.sample(nodes, self.odpair_count)
            destinations = random.sample(nodes, self.odpair_count)
            demands = [int(random.uniform(100, 1000))
                       for i in range(self.odpair_count)]
            self.odpairs = list(zip(origins, destinations, demands))

        if self.breakpoints is None:
            improvements_breakpoints = [
                1] + list(sorted([random.uniform(0.8, 1) for i in range(self.breakpoint_count)], reverse=True))
            transfer_breakpoints = [
                0] + list(sorted([random.uniform(0, 1) for i in range(self.breakpoint_count)]))
            self.breakpoints = list(
                zip(transfer_breakpoints, improvements_breakpoints))

    def write_data(self, output):
        self._generate_random_data()
        super().write_data(output)
