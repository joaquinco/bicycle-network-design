import argparse
import sys

from bcnetwork import transform
from bcnetwork import analyze
from bcnetwork import draw
from bcnetwork import persistance

PROG_NAME = 'bcnetwork'

actions = {
  'transform': transform.main,
  'analyze': analyze.main,
  'draw': draw.main,
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
}

def parse_arguments():
  """
  Parses action and per action arguments
  """
  action_parser = argparse.ArgumentParser(prog=PROG_NAME)
  action_parser.add_argument(
    'action', choices=actions.keys()
  )

  action_args, rest_args = action_parser.parse_known_args(sys.argv[1:])
  action = action_args.action

  action_args = argparse.ArgumentParser(prog=PROG_NAME)
  for args, kwargs in action_arguments[action]:
    action_args.add_argument(*args, **kwargs)

  return action, action_args.parse_args(rest_args)


def main():
  action, args = parse_arguments()

  if args.graph_yaml:
    graph = persistance.read_graph_from_yaml(args.graph_yaml, normalize=True)
  elif args.arcs_csv and args.nodes_csv:
    graph = persistance.read_graph_from_csvs(args.nodes_csv, args.arcs_csv)
  else:
    sys.stderr.write("Need to specify either a graph YAML file or pair of CSVs for nodes and arcs\n")
    sys.exit(1)

  actions[action](graph, args)

main()
