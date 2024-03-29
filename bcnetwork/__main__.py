import argparse
import sys

from bcnetwork import (
    analyze,
    cplex,
    draw,
    logger,
    persistance,
    solve,
    transform,
)
from bcnetwork.run import supported_solvers

PROG_NAME = 'bcnetwork'


class CmdAction:
    def __init__(self, method, use_graph=True):
        self.method = method
        self.use_graph = use_graph

    def __call__(self, args):
        if self.use_graph:
            self.method(self.load_graph(args), args)
        else:
            self.method(args)

    def load_graph(self, args):
        if args.graph_yaml:
            graph = persistance.read_graph_from_yaml(
                args.graph_yaml, normalize=True)
        elif args.arcs_csv and args.nodes_csv:
            graph = persistance.read_graph_from_csvs(
                args.nodes_csv, args.arcs_csv)
        else:
            sys.stderr.write(
                "Need to specify either a graph YAML file or pair of CSVs for nodes and arcs\n")
            sys.exit(1)
        return graph


actions = {
    'analyze': CmdAction(analyze.main),
    'cplex-sol': CmdAction(cplex.main, use_graph=False),
    'draw': CmdAction(draw.main, use_graph=False),
    'solve': CmdAction(solve.main, use_graph=False),
    'transform': CmdAction(transform.main, use_graph=False),
}

graph_input_args = (
    (['-n', '--nodes-csv'], dict(required=False)),
    (['-a', '--arcs-csv'], dict(required=False)),
    (['-g', '--graph-yaml'], dict(required=False)),
)

action_arguments = {
    'transform': (
        (['model'], {}),
    ),
    'analyze': (
        *graph_input_args,
        (['-w', '--weight-attribute'], dict(required=True, default='weight')),
    ),
    'cplex-sol': (
        (['input_file'], dict(help='Cplex solution path')),
        (['-m', '--model'], dict(required=True)),
    ),
    'draw': (
        (['-o', '--output'], dict(required=True)),
        (['--model'], dict(required=True)),
        (['--solution'], {}),
        (['--odpairs'], dict(action='store_true')),
        (['--infrastructures'], dict(action='store_true')),
        (['--flows'], dict(action='store_true')),
    ),
    'solve': (
        *graph_input_args,
        (['--breakpoints'], dict(type=int, default=4)),
        (['--budget-factor'], dict(type=float, default=0.2)),
        (['--demands-csv'], dict(required=False)),
        (['--infrastructures'], dict(type=int, default=2)),
        (['--model'], dict(required=False)),
        (['--output-dir'], dict(default='.')),
        (['--parallelism'], dict(type=int, default=10)),
        (['--project-root'], dict()),
        (['--solver'], dict(choices=supported_solvers, default=supported_solvers[0])),
        (['--timeout'], dict(type=int)),
        (['--validate'], dict(action='store_true')),
        (['--version'], dict(help='Model version to use, default single_level')),
        (['--solution-path'], dict(help='Path where to save the solution'))
    )
}


def parse_arguments():
    """
    Parses action and per action arguments
    """
    main_parser = argparse.ArgumentParser(prog=PROG_NAME)
    main_parser.add_argument(
        '-l', '--log-level',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        default='info',
    )

    subparsers = main_parser.add_subparsers(
        dest='action', required=True, help='Action to perform')

    for action_name, action_args in action_arguments.items():
        action_parser = subparsers.add_parser(action_name)
        for args, kwargs in action_args:
            action_parser.add_argument(*args, **kwargs)

    return main_parser.parse_args(sys.argv[1:])


def main():
    args = parse_arguments()

    logger.setLevel(args.log_level.upper())

    actions[args.action](args)


main()
