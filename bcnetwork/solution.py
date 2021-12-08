import functools
import re

from .bunch import Bunch
from .persistance import Persistable

delimeter = ','
file_delimeter = '---'

file_delimeter_regex = r'---([\w_]*)'


schemas = {
    'shortest_paths': {
        'origin': str,
        'destination': str,
    },
    'demand_transfered': {
        'origin': str,
        'destination': str,
        'infrastructure': str,
    },
    'infrastructures': {
        'infrastructure': str,
        'construction_cost': float,
    },
    'flows': {
        'origin': str,
        'destination': str,
    },
}


def _parse_entry(value, schema_type=None):
    if schema_type is not None:
        return schema_type(value)

    if '.' in value:
        try:
            return float(value)
        except:
            pass
    else:
        try:
            return int(value)
        except:
            pass

    return value


def _get_name(line):
    match = re.match(file_delimeter_regex, line)

    if not match:
        raise ValueError('Delimeter line does not match ---<name>')

    return match.group(1)


def _parse_single_csv(stream, schema):
    header = None
    csv = []
    for line in stream:
        if line.startswith(file_delimeter):
            return csv, line

        row = line.strip().split(delimeter)

        if not header:
            header = row
        else:
            csv.append({
                header[i]: _parse_entry(row[i], schema_type=schema.get(header[i])) for i in range(len(header))
            })

    return csv, None


def _parse_csvs(stream, prev_line):
    """
    Parse csvs sections
    """
    delimeter_line = prev_line
    csvs = {}

    while True:
        csv_name = _get_name(delimeter_line)
        if not csv_name:
            break

        csv, delimeter_line = _parse_single_csv(
            stream, schemas.get(csv_name, {})
        )
        csvs[csv_name] = csv

        if not delimeter_line:
            break

    return csvs


def parse_solution_file(stream):
    """
    Parses output of model execution.
    """
    for line in stream:
        if line.startswith(file_delimeter):
            return _parse_csvs(stream, line)


def parse_gap(group, base, match):
    """
    Given a match, returns a gap
    to best solution between 0 and 1
    """
    return float(match[group]) / base


def search_timeout_exceeded(fp, solver):
    """
    Searches indicator of having timeedout.
    """
    if not solver:
        return None, None

    timeout_phrase = dict(
        glpsol='TIME LIMIT EXCEEDED',
        cbc='Stopped on time limit',
        ampl='aborted',
    )[solver]

    gap_regex = dict(
        # Percentage (0-100) is on group 2
        glpsol=r'.*(mip|>>>>>).*\s(\d+(\.\d+)?)%.*',
        cbc=r'^Gap.*\s+(\d+(\.\d+)?)',  # Percentage (0-1) is on group 1
        ampl=r'.*relmipgap\s=\s([\d\.]+)$',
    )

    gap_parser = dict(
        glpsol=functools.partial(parse_gap, 2, 100),
        cbc=functools.partial(parse_gap, 1, 1),
        ampl=functools.partial(parse_gap, 1, 1),
    )

    gap = None
    did_timeout = False
    gap_re = re.compile(gap_regex[solver])

    for line in fp:
        gap_match = gap_re.match(line)
        if gap_match:
            gap = gap_parser[solver](gap_match)

        if not did_timeout:
            did_timeout = timeout_phrase in line

    return gap, did_timeout


class Solution(Persistable):
    def __init__(
        self,
        stdout_file=None,
        stdout_stream=None,
        model_name=None,
        solver=None,
        run_time_seconds=None,
        timeout=None,
    ):
        self.stdout_file = stdout_file
        self.stdout_stream = stdout_stream
        self.model_name = model_name
        self.solver = solver
        self.run_time_seconds = run_time_seconds
        self.timeout = timeout

        self.data = None
        self.did_timeout = None
        self.gap = None
        self.set_data()

    def _parse_data(self):
        if self.stdout_file:
            with open(self.stdout_file, 'r') as f:
                gap, did_timeout = search_timeout_exceeded(f, self.solver)
                f.seek(0)

                return gap, did_timeout, parse_solution_file(f)
        else:
            gap, did_timeout = search_timeout_exceeded(
                self.stdout_stream, self.solver)
            self.stdout_stream.seek(0)

            csvs = parse_solution_file(self.stdout_stream)
            self.stdout_stream.close()
            self.stdout_stream = None

            return gap, did_timeout, csvs

    def set_data(self):
        gap, did_timeout, csv_data = self._parse_data()
        self.data = Bunch(**csv_data)
        self.did_timeout = did_timeout
        self.gap = gap

    @functools.cached_property
    def budget_used(self):
        return self.data['budget_used'][0]['budget_used']

    @functools.cached_property
    def total_demand_transfered(self):
        return self.data['total_demand_transfered'][0]['total_demand_transfered']

    @functools.cached_property
    def shortest_paths(self):
        return {
            (data.origin, data.destination): data.shortest_path_cost
            for data in self.data.shortest_paths
        }
