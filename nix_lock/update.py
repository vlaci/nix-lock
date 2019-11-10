import datetime
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from urllib.parse import urlparse

import crayons
import httpx

from . import derivations


def update(package_file, auth, force):
    """Update dependencies in the lock file to latest versions"""
    client = httpx.Client()
    updaters = [GitHubUpdater(client, auth)]
    print(f"Updating sources in {package_file.name}")
    dirty = False
    with package_file.open() as f:
        srcs = derivations.loads(f.read())["srcs"]

    lock_file = package_file.with_suffix(".lock")

    try:
        with lock_file.open() as f:
            lock = json.load(f)
    except FileNotFoundError:
        lock = {}

    for i, p in enumerate(srcs):
        n = srcs[p]
        print(f"{i+1}/{len(srcs)} [{p}]: Looking for updates... ")
        for u in updaters:
            pkg = u.get_package(n["url"], n["rev"])
            if pkg:
                break
        else:
            raise RuntimeError("Unsupported package source " + n["url"])

        rev = pkg.get_latest_hash()
        if force or rev != lock.get(p, {}).get("meta", {}).get("rev"):
            print(crayons.yellow(f"downloading new version..."))
            lock_entry = pkg.update_lock(rev)
            lock_entry["meta"] = {
                "updated": datetime.datetime.utcnow()
                .replace(microsecond=0, tzinfo=datetime.timezone.utc)
                .isoformat(),
                "rev": rev,
            }

            lock[p] = lock_entry
            dirty = True
        else:
            print(crayons.green(f"️up-to-date"))

    if not dirty:
        return

    with tempfile.NamedTemporaryFile(
        "w", prefix=lock_file.name, dir=package_file.parent, delete=False
    ) as f:
        json.dump(lock, f, indent=4)
        f.write("\n")
    os.rename(f.name, lock_file)


class GitHubArchive:
    def __init__(self, client, auth, url, rev):
        self.client = client
        self.auth = auth
        self.path = urlparse(url).path
        self.rev = rev or "master"

    def get_latest_hash(self):
        api_url = f"https://api.github.com/repos{self.path}/commits?sha={self.rev}"
        while True:
            try:
                resp = self.client.get(
                    api_url,
                    headers={"Accept": "application/vnd.github.v3+json"},
                    auth=self.auth,
                )
                resp.raise_for_status()
                return resp.json()[0]["sha"]
            except httpx.HTTPError as err:
                if (
                    err.response.status_code == 403
                    and err.response.headers["X-RateLimit-Remaining"] == "0"
                ):
                    reset_at = (
                        datetime.datetime.fromtimestamp(
                            int(err.response.headers["X-RateLimit-Reset"])
                        )
                        + 10
                    )
                    while True:
                        delta = int(
                            (reset_at - datetime.datetime.now()).total_seconds()
                        )
                        if delta < 0:
                            break
                        print(
                            crayons.red(f"Ratelimit reached. Waiting for {delta}s...")
                        )
                        time.sleep(10)
                raise

    def update_lock(self, rev):
        url = f"https://github.com{self.path}/archive/{rev}.tar.gz"
        res = subprocess.run(
            ["nix-prefetch-url", "--unpack", url], stdout=subprocess.PIPE, text=True
        )
        checksum = res.stdout.strip()
        owner, repo = Path(self.path).relative_to("/").parts

        return {
            "fetcher": "fetchFromGitHub",
            "args": {"owner": owner, "repo": repo, "rev": rev, "sha256": checksum},
        }


class GitHubUpdater:
    def __init__(self, client, auth):
        self.client = client
        self.auth = auth

    def get_package(self, url, rev):
        if "github.com" in url:
            return GitHubArchive(self.client, self.auth, url, rev)
