import argparse
import getpass
import os
from pathlib import Path
import sys

from nix_lock.update import update


def parse_args():
    def credential(value):
        if value:
            password = os.environ.get("NIX_LOCK_PASSWORD")
            password = password or getpass.getpass(f"Password [{value}]")
        return (value, password)

    def path_exists(value):
        if not os.path.exists(value):
            raise argparse.ArgumentTypeError(f"{value} does not exists")
        return Path(value)

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(help="command to run")
    update_parser = subparsers.add_parser("update")
    update_parser.add_argument(
        "derivations_file", nargs="?", default="derivations.json", type=path_exists
    )
    update_parser.add_argument("--force", default=False, action="store_true")
    update_parser.add_argument("--user", dest="auth", default=None, type=credential)

    update_parser.set_defaults(
        func=lambda args: update(args.derivations_file, args.auth, args.force)
    )
    return parser.parse_args()


def main():
    args = parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
