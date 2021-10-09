import argparse
import sys

from bcnetwork import transform
from bcnetwork import analyze
from bcnetwork import draw
from bcnetwork import persistance
from bcnetwork import solve
from bcnetwork import logger

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


actions = {
    'transform': CmdAction(transform.main),
    'analyze': CmdAction(analyze.main),
    'draw': CmdAction(draw.main),
    'solve': CmdAction(solve.main, use_graph=False),
}

graph_input_args = (
    (['-n', '--nodes-csv'], dict(required=False)),
    (['-a', '--arcs-csv'], dict(required=False)),
    (['-g', '--graph-yaml'], dict(required=False)),
)

action_arguments = {
    'transform': (
        *graph_input_args,
    ),
    'analyze': (
        *graph_input_args,
        (['-w', '--weight-attribute'], dict(required=True, default='weight')),
    ),
    'draw': (
        *graph_input_args,
        (['-o', '--output'], dict(required=True)),
    ),
    'solve': (
        *graph_input_args,
        (['--output-dir'], dict(default='.')),
        (['--model'], dict(required=False)),
        (['--demands-csv'], dict(required=False)),
        (['--infrastructures'], dict(type=int, default=2)),
        (['--breakpoints'], dict(type=int, default=4)),
        (['--budget-factor'], dict(type=float, default=0.2)),
    )
}


def parse_arguments():
    """
    Parses action and per action arguments
    """
    main_parser = argparse.ArgumentParser(prog=PROG_NAME)
    main_parser.add_argument(
        'action', choices=actions.keys()
    )
    main_parser.add_argument(
        '-l', '--log-level', choices=['debug', 'info', 'warning', 'error', 'critical'], default='info',
    )

    main_args, rest_args = main_parser.parse_known_args(sys.argv[1:])
    action = main_args.action

    action_args = argparse.ArgumentParser(prog=PROG_NAME)
    for args, kwargs in action_arguments[action]:
        action_args.add_argument(*args, **kwargs)

    return main_args, action_args.parse_args(rest_args)


def main():
    main_args, action_args = parse_arguments()

    logger.setLevel(main_args.log_level)

    actions[action](action_args)


main()
