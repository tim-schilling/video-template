"""Repair the parts of a PythonAnywhere deploy that django-simple-deploy leaves broken.

Two known failure modes, both silent:

1. `manage.py deploy` (dsd-pythonanywhere) always appends `django-simple-deploy`
   and `dsd-pythonanywhere` to requirements.txt, even though they're only needed
   to run the deploy command, not at runtime. Installing dsd-pythonanywhere's
   git+https dependency often fails on PythonAnywhere's Beginner-tier outbound
   allowlist.
2. The plugin copies config/wsgi.py to PythonAnywhere's WSGI config file by
   running `cp` in a bash console (dsd_pythonanywhere.platform_deployer
   .PlatformDeployer._copy_wsgi_file). Console commands aren't checked for
   exit status, so if that `cp` fails -- wrong cwd, race with webapp
   creation, whatever -- PythonAnywhere's default "Hello, World!" WSGI file
   is left in place, on the very first deploy, and nothing downstream
   notices.

Run standalone (`just deploy-pythonanywhere-plan`) to just clean
requirements.txt locally, matching what django-simple-deploy's non-automated
"plan" mode already expects you to review and commit yourself.

Run with --remote (`just deploy-pythonanywhere`, after --automate-all has
already committed/pushed/deployed) to also commit and push the requirements.txt
fix, then, unconditionally (first deploy or the hundredth), reinstall
requirements, overwrite PythonAnywhere's WSGI file via the Files API (not the
fragile console `cp`) with this repo's config/wsgi.py, and reload the webapp --
so the site is left working with no manual PA console or Web-tab steps, ever.
"""

import argparse
import os
import subprocess
from pathlib import Path

from dsd_pythonanywhere.client import PythonAnywhereClient

DEPLOY_ONLY_PACKAGES = ("django-simple-deploy", "dsd-pythonanywhere")
REPO_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS_PATH = REPO_ROOT / "requirements.txt"
WSGI_PATH = REPO_ROOT / "config" / "wsgi.py"

# pythonanywhere_core.files.Files computes its API base URL from the username
# at import time (via get_username(), which reads PYTHONANYWHERE_USERNAME),
# so this must be set before that module is first imported below.
if "API_USER" in os.environ:
    os.environ.setdefault("PYTHONANYWHERE_USERNAME", os.environ["API_USER"])

from pythonanywhere_core.files import Files  # noqa: E402


def package_name(requirement_line: str) -> str:
    return requirement_line.split("==")[0].split(" @")[0].split(";")[0].strip()


def strip_deploy_only_packages() -> bool:
    original = REQUIREMENTS_PATH.read_text()
    lines = original.splitlines(keepends=True)
    kept = [line for line in lines if package_name(line) not in DEPLOY_ONLY_PACKAGES]
    contents = "".join(kept).rstrip("\n") + "\n"
    if contents == original:
        return False
    REQUIREMENTS_PATH.write_text(contents)
    return True


def get_repo_name() -> str:
    origin_url = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return Path(origin_url).stem


def commit_and_push() -> None:
    subprocess.run(["git", "add", str(REQUIREMENTS_PATH)], check=True)
    subprocess.run(
        ["git", "commit", "-m", "Remove deploy-only packages from requirements.txt"],
        check=True,
    )
    subprocess.run(["git", "push", "origin", "HEAD"], check=True)


def reinstall_requirements(client: PythonAnywhereClient, repo_name: str) -> None:
    client.run_command(f"cd ~/{repo_name} && git pull && pip install -r requirements.txt")


def sync_wsgi_file(client: PythonAnywhereClient) -> None:
    wsgi_dest = f"/var/www/{client.domain_name.replace('.', '_')}_wsgi.py"
    Files().path_post(wsgi_dest, WSGI_PATH.read_bytes())


def repair_pythonanywhere() -> None:
    client = PythonAnywhereClient(username=os.environ["API_USER"])
    reinstall_requirements(client, get_repo_name())
    sync_wsgi_file(client)
    client.reload_webapp()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--remote",
        action="store_true",
        help="Also commit/push the requirements.txt fix and repair the live PythonAnywhere deploy.",
    )
    args = parser.parse_args()

    changed = strip_deploy_only_packages()
    print(
        "Removed deploy-only packages from requirements.txt."
        if changed
        else "requirements.txt already clean."
    )

    if not args.remote:
        return

    if changed:
        commit_and_push()
    repair_pythonanywhere()
    print("Reinstalled requirements, synced the WSGI file, and reloaded the PythonAnywhere webapp.")


if __name__ == "__main__":
    main()
