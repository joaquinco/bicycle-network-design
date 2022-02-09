import copy
import csv
import functools
import os
import random
import secrets
import tempfile
import warnings

import yaml

import networkx as nx

from .persistance import (
    normalize_graph_shape,
    read_graph_from_csvs,
    read_graph_from_yaml,
    read_graph_from_yaml,
    write_graph_to_yaml,
)
from .costs import get_user_cost
from .logging import logger
from .misc import get_arcs_by_key
from .persistance import get_csv_rows, open_path_or_buf, Persistable, save as save_object
from .run import run_solver
from .solution import Solution
from .transform import model_to_mathprog
from .validation import validate_solution

default_project_root = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..'
)


def validate_non_decreasing(value_list):
    """
    Validate that the items of the list are in non decreasing order
    """
    if len(value_list) < 2:
        return True

    for x1, x2 in zip(value_list[:-1], value_list[1:]):
        if x1 > x2:
            return False

    return True


def validate_breakpoints(breakpoints):
    """
    Validate that breakpoints are non decreasing.
    """
    transfers, improvements = zip(*breakpoints)

    if not validate_non_decreasing(transfers):
        raise ValueError('Breakpoint transfer must be strictly incremental')

    improvements = list(improvements)
    improvements.reverse()
    if not validate_non_decreasing(improvements):
        raise ValueError(
            'Breakpoint shortest path improvements are not non decreasing')

    if improvements[-1] < 1 and transfers[0] != 0.0:
        # If thers no breakpoint that handles the no demand transfer case
        # then the problem might be infeasable.
        logger.warning(
            "Missing path cost improvement of at least 1 with corresponding demand transfer of 0,"
            " problem might be infeasable"
        )


class Model(Persistable):
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
        self.user_cost_weight = user_cost_weight
        self.solution = None

    @functools.cached_property
    def graph(self):
        """
        Returns a networkx graph instance
        """
        if self._graph:
            return normalize_graph_shape(self._graph)

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
        validate_breakpoints(self.breakpoints)

        with open_path_or_buf(output_path, 'w') as output:
            model_to_mathprog(
                self,
                output,
            )

    @classmethod
    def load_yaml(cls, path):
        warnings.warn(
            "Consider using load/save to pickle instead",
            DeprecationWarning

        )
        with open(path, 'r') as f:
            return yaml.load(f.read(), Loader=yaml.Loader)

    def save(self, path):
        """
        Create simplified version of model with no external dependencies.
        """
        self.uid
        model_to_save = copy.copy(self)
        model_to_save.graph
        model_to_save.odpairs
        model_to_save.arcs_file = None
        model_to_save.nodes_file = None
        model_to_save.odpairs_file = None

        save_object(model_to_save, path)

    @functools.cached_property
    def uid(self):
        return secrets.token_hex(12)

    def solve(
        self,
        model_name=None,
        solver='glpsol',
        timeout=None,
        output_dir=None,
        **kwargs,
    ):
        """
        Run solver, parses output and return Solution object.

        The kwargs are passed throught to run_solver function
        """
        model_prefix = f'{self.uid}_'
        _, data_file = tempfile.mkstemp(
            prefix=model_prefix,
            suffix='.dat',
            dir=default_project_root
        )
        _, output_file = tempfile.mkstemp(
            prefix=model_prefix,
            suffix=f'.{solver}.out',
            dir=output_dir,
        )

        self.write_data(data_file)

        try:
            data_file_basename = os.path.basename(data_file)
            process, run_time_seconds = run_solver(
                default_project_root,
                data_file_basename,
                output_file,
                model_name=model_name,
                solver=solver,
                timeout=timeout,
                **kwargs
            )

            if process.returncode != 0:
                raise RuntimeError(
                    f'Solve returned status {process.returncode}.\n{process.stderr}'
                )

            logger.debug('Wrote solver output to %s', output_file)
        finally:
            if output_dir:
                new_data_file = os.path.join(output_dir, data_file_basename)

                os.rename(
                    data_file,
                    new_data_file,
                )
                logger.debug('Writing data to %s', new_data_file)
            else:
                os.remove(data_file)

        return Solution(
            stdout_file=output_file,
            model_name=model_name or 'default',
            solver=solver,
            run_time_seconds=run_time_seconds,
            timeout=timeout,
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
        arcs_by_id = get_arcs_by_key(ret)
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

    @functools.cached_property
    def base_shortest_path_costs(self):
        """
        Dictionary with shortest path costs
        on base graph by (o, d).
        """
        return {
            (o, d): nx.astar_path_length(self.graph, o, d, weight=self.user_cost_weight)
            for (o, d, *_rest) in self.odpairs
        }


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
