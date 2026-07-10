#!/usr/bin/env python3
"""
ALGS 一键更新脚本
用法:
  python update_all.py --group ad --url "https://...Day3/AvD"
  python update_all.py --group ad --skip-fetch   # 已有CSV，只重建+推送
  python update_all.py --website-only            # 只重建网站+推送
"""
import os, sys, subprocess, argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = BASE_DIR

def run(cmd, cwd=None):
    print(f"\n  > {cmd}")
    r = subprocess.run(cmd, shell=True, cwd=cwd or BASE_DIR)
    if r.returncode != 0:
        print(f"  [!] Failed (exit {r.returncode})")
    return r.returncode == 0

def main():
    p = argparse.ArgumentParser(description="ALGS 一键更新")
    p.add_argument("--group", "-g", help="组别 (如 ad, bc, bd)")
    p.add_argument("--url", "-u", help="ApexLegendsStatus URL")
    p.add_argument("--skip-fetch", action="store_true", help="跳过数据抓取")
    p.add_argument("--skip-push", action="store_true", help="跳过 Git 推送")
    p.add_argument("--website-only", action="store_true", help="只重建网站+推送")
    args = p.parse_args()

    if args.website_only:
        pass  # just rebuild website
    elif args.group:
        if not args.skip_fetch:
            if not args.url:
                print("需要 --url 参数")
                return
            run(f'python generate_report.py "{args.url}" --group {args.group}', SCRIPTS_DIR)
    else:
        p.print_help()
        return

    # 重建网站
    print("\n[1/3] Building website...")
    run("python build_app.py")

    # 同步文件
    print("\n[2/3] Syncing to root...")
    run("cp -r public/thumbs/* thumbs/ 2>/dev/null; cp -r public/photos/* photos/ 2>/dev/null; cp public/index.html index.html")

    # 推送
    if not args.skip_push:
        print("\n[3/3] Pushing to GitHub...")
        run("git add index.html build_app.py thumbs/ photos/ public/")
        run("git add -f thumbs/*.jpg photos/*.jpg 2>/dev/null; true")
        msg = f"Update: {args.group or 'website'} data refresh"
        run(f'git commit -m "{msg}"')
        run("git push")

    print("\nDone! https://TaTll.github.io/algs-report-generator/")

if __name__ == "__main__":
    main()
