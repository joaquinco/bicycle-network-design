import argparse
import re
import sys
import os

from functools import partial
from itertools import product

import bcnetwork as bc


def get_odpairs_by_id(model):
    data = bc.transform.get_origin_destinations_by_id(model)

    return {x[0]: x[1:] for x in data}


def solver_int(string_value):
    """
    Handles some cases where integer variables are floats near integers
    """
    fvalue = float(string_value)
    ivalue = int(fvalue)

    if ivalue == 0:
        module = fvalue
    else:
        module = fvalue % ivalue

    if module > 0.5:
        return ivalue + 1

    return ivalue


class Index:
    def __init__(self, name):
        self.name = name
        self.values = set()

    def add(self, value):
        self.values.add(value)

    def __iter__(self):
        return iter(self.values)


class Variable:
    def __init__(self, builder, indexes):
        self.indexes = indexes
        self.builder = builder
        self.values = dict() if indexes else None

    def __setitem__(self, key, item):
        if not isinstance(key, tuple):
            key = (key,)

        if not self.indexes:
            self.values = item
        else:
            for entry, index in zip(key, self.indexes):
                index.add(entry)

            self.values[key] = self.builder(item)

    def __getitem__(self, key):
        if not self.indexes:
            return self.values
        else:
            return self.values.get(key, 0)

    def parse_indexes(self, key_indexes):
        return key_indexes.split(',')


def populate_variables(solution_path, variables):
    """
    Read cplex solution file and populate variables
    accordingly
    """
    with open(solution_path, 'r') as solution_file:
        for line in solution_file:
            if 'variable' not in line:
                continue

            match = re.match(
                '\s*<variable name="(.*)" index=".*?" value="(.*)"/>', line)
            if not match:
                continue

            variable_parts = match[1].split('(')
            variable_name = variable_parts[0]
            if len(variable_parts) == 1:
                variable_index = ''
            else:
                variable_index = variable_parts[1].rstrip(')').split(',')
                if len(variable_index) == 1:
                    variable_index = variable_index[0]
                else:
                    variable_index = tuple(variable_index)
            variable_value = match[2]

            variable = variables.get(variable_name)
            if not variable:
                continue

            variable[variable_index] = variable_value


def process_solution_file(solution_path, model):
    """
    Given a solution path, prints stuff in
    a way that is understandable by the solution parsing
    of the ampl and gplpk outputs.
    """

    od = Index('OD')
    a = Index('A')
    i = Index('I')
    j = Index('J')
    w = Variable(float, (od,))
    y = Variable(solver_int, (a, i))
    x = Variable(float, (a, od))
    z = Variable(solver_int, (od, j))
    h = Variable(float, (a, od, i))
    demand_transfered = Variable(float, ())

    variables = dict(
        w=w,
        y=y,
        x=x,
        z=z,
        h=h,
        demand_transfered=demand_transfered,
    )

    populate_variables(solution_path, variables)

    csvprint = partial(print, sep=',')

    odpair_data = get_odpairs_by_id(model)
    arcs_by_id = bc.misc.get_arcs_by_key(model.graph)

    def get_m(arc, infra):
        return bc.costs.get_construction_cost(
            model.graph.edges[arcs_by_id[arc]],
            int(infra),
        )

    def get_p(odpair, jota):
        odpair_index = int(odpair.split('_')[1])
        ijota = int(jota)

        # demand * transfer proportion
        return odpair_data[odpair][2] * model.breakpoints[ijota][0]

    # Reproduce print logic of Mathprog models
    prefix = '---'
    print(f'{prefix}shortest_paths')
    print('origin,destination,shortest_path_cost')
    for k in od:
        csvprint(k, odpair_data[k][0], odpair_data[k][1], w[k])

    print(f'{prefix}flows')
    print('origin,destination,arc,infrastructure,flow')
    for k in od:
        for arc in a:
            for infra in i:
                h_value = h[(arc, k, infra)]
                if h_value > 0:
                    csvprint(odpair_data[k][0], odpair_data[k]
                             [1], arc, infra, h_value)

    print(f'{prefix}infrastructures')
    print('arc,infrastructure,construction_cost')
    for arc in a:
        for infra in i:
            if y[(arc, infra)] > 0 and infra != '0':
                csvprint(
                    arc,
                    infra,
                    get_m(arc, infra),
                )

    print(f'{prefix}demand_transfered')
    print('origin,destination,demand_transfered,z,j_value')
    for k in od:
        for jota in j:
            z_value = z[(k, jota)]
            if z_value > 0:
                csvprint(
                    odpair_data[k][0],
                    odpair_data[k][1],
                    get_p(k, jota),
                    z_value,
                    jota,
                )

    print(f'{prefix}total_demand_transfered')
    print('total_demand_transfered')
    csvprint(demand_transfered[''])

    print(f'{prefix}budget_used')
    print('budget_used')
    csvprint(sum(
        get_m(arc, infra) * y[(arc, infra)] for arc, infra in product(a, i))
    )

    print(prefix)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help='Cplex solution path')
    parser.add_argument('-m', '--model', required=True,
                        help='Saved Model path')

    args = parser.parse_args(sys.argv[1:])

    model = bc.model.Model.load(args.model)
    process_solution_file(args.input_file, model)


main()
