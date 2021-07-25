import re

from .bunch import Bunch
from .cache import cached_property

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
    },
    'infrastructures': {
        'infrastructure': str,
        'construction_cost': float,
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


class Solution:
    def __init__(self, stdout_file=None, stdout_stream=None, model_name=None):
        self.stdout_file = stdout_file
        self.stdout_stream = stdout_file
        self.model_name = model_name

    def _parse_data(self):
        if self.stdout_file:
            with open(self.stdout_file, 'r') as f:
                return parse_solution_file(f)
        else:
            csvs = parse_solution_file(self.stdout_stream)
            self.stdout_stream.close()
            return csvs

    @cached_property
    def data(self):
        return Bunch(**self._parse_data())

    @cached_property
    def budget_used(self):
        return self.data['budget_used'][0]['budget_used']

    @cached_property
    def total_demand_transfered(self):
        return self.data['total_demand_transfered'][0]['total_demand_transfered']
