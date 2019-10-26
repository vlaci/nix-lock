import argparse
import datetime
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import crayons
import httpx


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
    update_parser.add_argument("derivations_file",  nargs="?", default="derivations.json", type=path_exists)
    update_parser.add_argument("--force", default=False, action="store_true")
    update_parser.add_argument("--user", dest="auth", default=None, type=credential)
    update_parser.set_defaults(func=update)
    return parser.parse_args()


def main():
    args = parse_args()
    return args.func(args)


def update(args):
    return _update(args.derivations_file, args.auth, args.force)


def _update(package_file, auth, force):
    """Update dependencies in the lock file to latest versions"""
    print(f"Updating sources in {package_file.name}")
    dirty = False
    with package_file.open() as f:
        versions = json.load(f)

    lock_file = package_file.with_suffix(".lock")

    try:
        with lock_file.open() as f:
            lock = json.load(f)
    except FileNotFoundError:
        lock = {}

    client = httpx.Client()
    for i, p in enumerate(versions):
        n = versions[p]
        print(f"{i+1}/{len(versions)} [{p}]: Looking for updates... ")
        while True:
            try:
                resp = client.get(
                    f"https://api.github.com/repos/{n['owner']}/{n['repo']}/commits?sha={n.get('rev', 'master')}",
                    headers={"Accept": "application/vnd.github.v3+json"},
                    auth=auth
                )
                resp.raise_for_status()
                rev = resp.json()[0]["sha"]
                limit = int(resp.headers['X-RateLimit-Remaining'])
                break
            except httpx.HTTPError as err:
                if resp.status_code == 403 and resp.headers["X-RateLimit-Remaining"] == "0":
                    reset_at = datetime.datetime.fromtimestamp(int(resp.headers["X-RateLimit-Reset"]))
                    while True:
                        delta = int((reset_at - datetime.datetime.now()).total_seconds())
                        if delta < 0:
                            time.sleep(5)
                            break
                        print(crayons.red(f"Ratelimit reached. Waiting for {delta}s..."))
                        time.sleep(10)
                raise

        if force or rev != lock.get(p, {}).get("meta", {}).get("rev"):
            print(crayons.yellow(f"downloading new version... (limit: {limit})"))
            url = f"https://github.com/{n['owner']}/{n['repo']}/archive/{rev}.tar.gz"
            res = subprocess.run(
                ["nix-prefetch-url", "--unpack", url], stdout=subprocess.PIPE, text=True
            )

            lock[p] = {
                "fetcher": "fetchFromGitHub",
                "args": {
                    "owner": n["owner"],
                    "repo": n["repo"],
                    "rev": rev,
                    "sha256": res.stdout.strip(),
                },
                "meta": {
                    "updated": datetime.datetime.utcnow()
                    .replace(microsecond=0, tzinfo=datetime.timezone.utc)
                    .isoformat(),
                    "rev": rev,
                    },
            }
            dirty = True
        else:
            print(crayons.green(f"️up-to-date (limit: {limit})"))

    if not dirty:
        return

    with tempfile.NamedTemporaryFile(
        "w",
        prefix=package_file.name,
        dir=package_file.parent,
        delete=False,
    ) as f:
        json.dump(lock, f, indent=4)
        f.write("\n")
    os.rename(f.name, lock_file)


if __name__ == "__main__":
    sys.exit(main())
