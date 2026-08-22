"""Repair the parts of a PythonAnywhere deploy that django-simple-deploy leaves broken.

Two known failure modes:

1. `manage.py deploy` (dsd-pythonanywhere) always appends `django-simple-deploy`
   and `dsd-pythonanywhere` to requirements.txt, even though they're only needed
   to run the deploy command, not at runtime. Installing dsd-pythonanywhere's
   git+https dependency often fails on PythonAnywhere's Beginner-tier outbound
   allowlist, which can break the rest of an --automate-all run.
2. PythonAnywhere's `/var/www/<domain>_wsgi.py` doesn't reliably get updated by
   dsd-pythonanywhere's own `cp` (run through a bash console with no exit-status
   check) or by writing it through the Files API's `path_post` -- that call
   reports success and a follow-up GET even echoes back the new content, but
   the real on-disk file (the one PythonAnywhere actually serves, and the one
   a console `cat` shows) can be left untouched. A `cp` run directly in a PA
   console is the only method confirmed to actually persist here, so that's
   what this script uses, with a same-console read-back to verify it landed.

Run standalone (`just deploy-pythonanywhere-plan`) to just clean
requirements.txt locally, matching what django-simple-deploy's non-automated
"plan" mode already expects you to review and commit yourself.

Run with --remote (`just deploy-pythonanywhere`, after --automate-all has
already committed/pushed/deployed) to also commit and push the requirements.txt
fix, then, unconditionally (first deploy or the hundredth), pull, reinstall
requirements, re-copy the WSGI file, verify it, and reload the webapp -- so the
site is left working with no manual PA console or Web-tab steps.
"""

import argparse
import os
import subprocess
from pathlib import Path

from dsd_pythonanywhere.client import PythonAnywhereClient

DEPLOY_ONLY_PACKAGES = ("django-simple-deploy", "dsd-pythonanywhere")
REQUIREMENTS_PATH = Path(__file__).resolve().parent.parent / "requirements.txt"


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


def sync_wsgi_file(client: PythonAnywhereClient, repo_name: str) -> None:
    # PythonAnywhere's WSGI filename is always the lowercased domain, regardless
    # of the account's actual username casing (e.g. /home/CodenameTim/ but
    # /var/www/codenametim_..._wsgi.py) -- client.domain_name carries API_USER's
    # casing verbatim, so it must be lowered here rather than trusted as-is.
    wsgi_src = f"~/{repo_name}/config/wsgi.py"
    wsgi_dest = f"/var/www/{client.domain_name.lower().replace('.', '_')}_wsgi.py"

    client.run_command(f"cp {wsgi_src} {wsgi_dest}")

    result = client.run_command(f"cmp -s {wsgi_src} {wsgi_dest} && echo COPY_OK || echo COPY_FAILED")
    if "COPY_OK" not in result:
        raise RuntimeError(f"WSGI file copy did not verify (console said: {result!r})")


def repair_pythonanywhere() -> None:
    client = PythonAnywhereClient(username=os.environ["API_USER"])
    repo_name = get_repo_name()
    reinstall_requirements(client, repo_name)
    sync_wsgi_file(client, repo_name)
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
    print("Reinstalled requirements, verified the WSGI file, and reloaded the PythonAnywhere webapp.")


if __name__ == "__main__":
    main()
