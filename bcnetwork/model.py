import copy
import csv
import functools
import os
import random
import tempfile

import yaml

import networkx as nx

from .persistance import (
    read_graph_from_yaml,
    read_graph_from_csvs,
    write_graph_to_yaml,
    read_graph_from_yaml,
)
from .costs import get_user_cost
from .transform import graph_to_mathprog, origin_destination_pairs_to_mathprog
from .persistance import get_csv_rows, open_path_or_buf
from .solution import Solution
from .run import run_solver
from .validation import validate_solution
from .logging import logger

default_project_root = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..'
)


class Model:
    def __init__(
        self,
        name=None,
        graph=None,
        graph_file=None,
        nodes_file=None,
        arcs_file=None,
        odpairs_file=None,
        budget=None,
        budget_factor=None,
        odpairs=None,
        breakpoints=None,
        user_cost_weight='user_cost',
        infrastructure_count=2,
        project_root=None,
    ):
        self.name = name
        self._graph = graph
        self.graph_file = graph_file
        self.nodes_file = nodes_file
        self.odpairs_file = odpairs_file
        self.arcs_file = arcs_file
        self._budget = budget
        self._budget_factor = budget_factor
        self._odpairs = odpairs
        self.breakpoints = breakpoints
        self.infrastructure_count = infrastructure_count
        self.project_root = project_root or default_project_root
        self.user_cost_weight = user_cost_weight
        self.solution = None

    @functools.cached_property
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

    @functools.cached_property
    def budget(self):
        """
        Return absolute budget value.
        If budget was provided use that, else return
        the budget_factor proportion of constructing all base infrastructures.
        """
        if self._budget is not None:
            return self._budget

        total_cost = sum([self.graph.edges[n1, n2]['construction_cost']
                          for (n1, n2) in self.graph.edges()])

        return total_cost * self._budget_factor

    @functools.cached_property
    def odpairs(self):
        if self._odpairs:
            return self._odpairs

        if self.odpairs_file:
            return [
                (r['origin'], r['destination'], r['demand'])
                for r in get_csv_rows(self.odpairs_file, {'demand': float})
            ]

    def write_data(self, output_path):
        """
        Write model to mathprog to the output path or buffer
        """
        with open_path_or_buf(output_path, 'w') as output:
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

    def solve(self, model_name='', solver='glpsol', **kwargs):
        """
        Run solver, parses output and return Solution object.

        The kwargs are passed throught to run_solver function
        """
        data_fd, data_file = tempfile.mkstemp(
            suffix='.dat', dir=self.project_root)

        logger.debug(f'Writing data to {data_file}')
        with os.fdopen(data_fd, 'w') as f:
            self.write_data(f)

        try:
            process, run_time_seconds = run_solver(
                self.project_root,
                os.path.basename(data_file),
                tempfile.mktemp(),
                model_name=model_name,
                solver=solver,
                **kwargs
            )

            if process.returncode != 0:
                raise RuntimeError(
                    f'Solve returned status {process.returncode}.\n{process.stderr}'
                )

            output_fd, output_file = tempfile.mkstemp(suffix=f'.{solver}.out')
            logger.debug(f'Writing solver output to {output_file}')

            with os.fdopen(output_fd, 'w') as f:
                f.write(process.stdout)
        finally:
            os.remove(data_file)

        return Solution(
            stdout_file=output_file,
            model_name=model_name or 'default',
            solver=solver,
            run_time_seconds=run_time_seconds,
        )

    def validate_solution(self, solution):
        """
        Run solution validator.
        """
        return validate_solution(self, solution)

    def apply_solution_to_graph(
        self,
        solution,
        sol_user_cost_weight='effective_user_cost',
        effective_infrastructure_weight='effective_infrastructure',
    ):
        """
        Return new graph with infraestructures set and user cost
        updated accordingly.

        Solution user cost is saved in <sol_user_cost_weight> edge attribute
        and infrastructure to <effective_infrastructure_weight>
        """

        ret = self.graph.copy()
        arcs_by_id = {ret.edges[o, d]['key']: (o, d) for o, d in ret.edges()}
        edges_infra_data = {(o, d): '0' for (o, d) in ret.edges()}

        for infra_data in solution.data.infrastructures:
            origin, destination = arcs_by_id[infra_data.arc]
            edges_infra_data[(origin, destination)] = infra_data.infrastructure

        for edge, infrastructure in edges_infra_data.items():
            origin, destination = edge
            ret[origin][destination].update({
                sol_user_cost_weight: get_user_cost(
                    ret[origin][destination], infrastructure
                ),
                effective_infrastructure_weight: infrastructure
            })

        return ret


class RandomModel(Model):
    def __init__(
        self,
        *args,
        odpair_count=5,
        breakpoint_count=4,
        budget_factor=0.1,
        min_breakpoint_percent=0.8,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.odpair_count = odpair_count
        self.breakpoint_count = breakpoint_count
        self._budget_factor = budget_factor
        self.min_breakpoint_percent = min_breakpoint_percent

    def _generate_random_data(self):
        """
        Generate random data if needed
        """
        if self.odpairs is None:
            nodes = list(self.graph.nodes())
            nodes_set = set(nodes)
            origins = list(map(str, random.sample(nodes, self.odpair_count)))
            destinations = [
                random.sample(list(nodes_set - {o}), k=1)[0]
                for o in origins
            ]
            demands = [int(random.uniform(100, 1000))
                       for i in range(self.odpair_count)]
            self.odpairs = list(zip(origins, destinations, demands))

        if self.breakpoints is None:
            improvements_breakpoints = [
                1] + list(sorted([random.uniform(self.min_breakpoint_percent, 1) for i in range(self.breakpoint_count)], reverse=True))
            transfer_breakpoints = [
                0] + list(sorted([random.uniform(0, 1) for i in range(self.breakpoint_count)]))
            self.breakpoints = list(
                zip(transfer_breakpoints, improvements_breakpoints))

    def write_data(self, output):
        self._generate_random_data()
        super().write_data(output)
