import argparse
import sys

from bcnetwork import transform
from bcnetwork import analyze
from bcnetwork import draw

PROG_NAME = 'bcnetwork'

actions = {
  'transform': transform.main_transform,
  'analyze': analyze.main_analyze,
  'draw': draw.main_draw,
}

action_arguments = {
  'transform': (
    (['-n', '--nodes-csv'], dict(required=True)),
    (['-a', '--arcs-csv'], dict(required=True)),
  ),
  'analyze': (
    (['-n', '--nodes-csv'], dict(required=True)),
    (['-a', '--arcs-csv'], dict(required=True)),
    (['-w', '--weight-attribute'], dict(required=True, default='weight')),
  ),
  'draw': (
    (['-n', '--nodes-csv'], dict(required=True)),
    (['-a', '--arcs-csv'], dict(required=True)),
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

  actions[action](args)

main()