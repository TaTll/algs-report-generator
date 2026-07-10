#!/usr/bin/env python3
"""
ALGS 一键更新
用法:
  python update_all.py --group ad --url "https://..."
  python update_all.py --group ad --skip-fetch
  python update_all.py --website-only
"""
import os, sys, subprocess, argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = BASE_DIR

def run(cmd, cwd=None):
    print(f"  > {cmd}")
    r = subprocess.run(cmd, shell=True, cwd=cwd or BASE_DIR)
    return r.returncode == 0

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
            run(f'python generate_report.py "{args.url}" --group {args.group}', SCRIPTS_DIR)

    # Build website
    print("\n[1/2] Building website...")
    run("python build_app.py")

    # Push
    if not args.skip_push:
        print("\n[2/2] Pushing to GitHub...")
        run("git add public/ build_app.py")
        run(f'git commit -m "Update {args.group or \"website\"}"')
        run("git push")

    print("\nDone!")
    print("Site: https://TaTll.github.io/algs-report-generator/")
    print("⚠️  Ensure GitHub Pages source is set to /public folder")

if __name__ == "__main__":
    main()
