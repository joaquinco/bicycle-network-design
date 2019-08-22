import sys
from argparse import ArgumentParser

from .persist import load_and_export


_commands_args = {
    'export': [
        (['-i', '--input'], {}),
        (['-o', '--output'], {}),
    ]
}

def parse_args(args):
    parser = ArgumentParser()
    parser.add_argument('action', choices=_commands_args.keys())

    return parser.parse_known_args(args)


def _parse_command_args(cmd_name, cmd_args):
    parser_entries = _commands_args.get(cmd_name)

    if not parser_entries:
        return {}

    parser = ArgumentParser()

    for args, kwargs in parser_entries:
        parser.add_argument(*args, **kwargs)

    return vars(parser.parse_args(cmd_args))


_actions = {
  'export': load_and_export
}

def main():
    args, extra = parse_args(sys.argv[1:])

    _actions.get(args.action, lambda **kwargs: ())(**_parse_command_args(args.action, extra))


if __name__ == '__main__':
    main()
