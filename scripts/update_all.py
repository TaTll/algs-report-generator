#!/usr/bin/env python3
"""
ALGS 一键更新
用法:
  python update_all.py --group ad --url "https://..."
  python update_all.py --group ad --skip-fetch
  python update_all.py --website-only
"""
import argparse
import os
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)
SITE_DIR = "docs"


def run(cmd, cwd=None, check=True):
    """Run one command and return whether it succeeded."""
    print(f"  > {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=cwd or PROJECT_DIR)
    if check and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result.returncode == 0


def has_staged_changes():
    """Return True when git has something staged for commit."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=PROJECT_DIR,
    )
    return result.returncode != 0

def main():
    p = argparse.ArgumentParser(description="ALGS 一键更新")
    p.add_argument("--group", "-g", help="组别")
    p.add_argument("--url", "-u", help="比赛 URL")
    p.add_argument("--skip-fetch", action="store_true")
    p.add_argument("--skip-push", action="store_true")
    p.add_argument("--website-only", action="store_true")
    args = p.parse_args()

    if not args.website_only:
        if not args.group:
            p.print_help()
            return
        if not args.skip_fetch and args.url:
            run(
                [sys.executable, "generate_report.py", args.url, "--group", args.group],
                cwd=SCRIPTS_DIR,
            )

    # Build website
    print("\n[1/2] Building website...", flush=True)
    run([sys.executable, "build_app.py"], cwd=PROJECT_DIR)

    # Push
    if not args.skip_push:
        print("\n[2/2] Pushing to GitHub...", flush=True)
        run(["git", "add", SITE_DIR, "build_app.py"])
        if has_staged_changes():
            run(["git", "commit", "-m", f"Update {args.group or 'website'}"])
            run(["git", "push"])
        else:
            print("  > No website changes to commit.", flush=True)

    print("\nDone!")
    print("Site: https://TaTll.github.io/algs-report-generator/")
    print("⚠️  Ensure GitHub Pages source is set to /docs folder")

if __name__ == "__main__":
    main()
