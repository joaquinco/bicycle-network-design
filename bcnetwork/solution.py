import re

from .cache import cached_property

delimeter = ','
file_delimeter = '---'

file_delimeter_regex = r'---([\w_]*)'


def _parse_entry(value):
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


def _parse_single_csv(stream):
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
                header[i]: _parse_entry(row[i]) for i in range(len(header))
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

        csv, delimeter_line = _parse_single_csv(stream)
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


def _get_scalar_from_csv(csv, column_name):
    return csv[0][column_name]


class Solution:
    def __init__(self, stdout_file=None, stdout_stream=None):
        self.stdout_file = stdout_file
        self.stdout_stream = stdout_file

    @cached_property
    def data(self):
        if self.stdout_file:
            with open(self.stdout_file, 'r') as f:
                return parse_solution_file(f)
        else:
            csvs = parse_solution_file(self.stdout_stream)
            self.stdout_stream.close()
            return csvs

    @cached_property
    def budget_used(self):
        return self.data['budget_used'][0]['budget_used']

    @cached_property
    def total_demand_transfered(self):
        return self.data['total_demand_transfered'][0]['total_demand_transfered']