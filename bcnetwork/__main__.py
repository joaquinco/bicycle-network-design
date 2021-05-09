import argparse
import sys

from bcnetwork import transform

actions = {
  'transform': transform.main_transform,
}

action_arguments = {
  'transform': (
    (['-n', '--nodes-csv'], dict(required=True)),
    (['-a', '--arcs-csv'], dict(required=True)),
  ),
}

def parse_arguments():
  """
  Parses action and per action arguments
  """
  action_parser = argparse.ArgumentParser(
    prog='bcnetwork'
  )
  action_parser.add_argument(
    'action', choices=actions.keys()
  )

  action_args, rest_args = action_parser.parse_known_args(sys.argv[1:])
  action = action_args.action

  action_args = argparse.ArgumentParser()
  for args, kwargs in action_arguments[action]:
    action_args.add_argument(*args, **kwargs)

  return action, action_args.parse_args(rest_args)


def main():
  action, args = parse_arguments()

  actions[action](args)

main()