#!/usr/bin/env python3
"""
ALGS Overview 监控脚本 —— 每天中午12点由 Windows 任务计划触发。
抓取 Overview 页面，发现新完成的比赛自动生成报告并发送飞书。

用法:
  python monitor_overview.py          # 单次检查
  python monitor_overview.py --watch  # 持续监控（每30分钟一次，Ctrl+C 停止）
"""
import sys, os, json, re, subprocess, time
from datetime import datetime

# 路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
STATE_FILE = os.path.join(DATA_DIR, 'processed_matches.json')
GENERATE_SCRIPT = os.path.join(BASE_DIR, 'generate_report.py')

# 基础 URL
BASE_URL = "https://apexlegendsstatus.com"
OVERVIEW_URL = f"{BASE_URL}/algs/Y6-Split1/ALGS-Playoffs/Global/Overview"


def get_scrapling_cmd():
    """Find Scrapling CLI from env, project venv, or PATH."""
    configured = os.environ.get('SCRAPLING_BIN')
    if configured:
        return configured

    exe_name = 'scrapling.exe' if os.name == 'nt' else 'scrapling'
    project_dir = os.path.dirname(BASE_DIR)
    local_bin = os.path.join(project_dir, '.venv', 'Scripts' if os.name == 'nt' else 'bin', exe_name)
    if os.path.exists(local_bin):
        return local_bin

    return 'scrapling'


def load_state():
    """加载已处理比赛记录"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_state(state):
    """保存处理记录"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def fetch_overview():
    """抓取 Overview 页面 HTML"""
    html_path = os.path.join(DATA_DIR, '_overview_temp.html')
    cmd = [
        get_scrapling_cmd(), 'extract', 'fetch', OVERVIEW_URL,
        html_path, '--network-idle', '--timeout', '60000'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', cwd=DATA_DIR)
    if not os.path.exists(html_path):
        print(f"[ERROR] 抓取 Overview 失败")
        return None
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    os.remove(html_path)
    return html


def parse_matches(html):
    """解析所有比赛链接，返回 [(match_id, url, is_finished, scheduled_time), ...]"""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    matches = []

    for a in soup.find_all('a', class_='bracket_match'):
        href = a.get('href', '')
        if not href or '/Day' not in href:
            continue

        # 提取 match_id，如 "Day1/AvB"
        m = re.search(r'/Day(\d+)/(\w+)', href)
        if not m:
            continue
        match_id = f"Day{m.group(1)}/{m.group(2)}"
        url = BASE_URL + href

        # 判断是否已打完：没有 bracket_match_not_played
        not_played = a.find('div', class_='bracket_match_not_played')
        is_finished = not_played is None

        # 获取预定时间
        scheduled = ''
        if not_played:
            time_div = not_played.find('div', class_='bracket_match_scheduled_time')
            if time_div:
                scheduled = time_div.get_text(strip=True)

        matches.append((match_id, url, is_finished, scheduled))

    return matches


def process_match(match_id, url):
    """调用 generate_report.py 处理单场比赛"""
    print(f"\n{'='*50}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 处理: {match_id}")
    print(f"  URL: {url}")

    result = subprocess.run(
        [sys.executable, GENERATE_SCRIPT, url],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        cwd=BASE_DIR, timeout=600
    )

    if result.returncode == 0:
        print(f"  [OK] {match_id} 处理成功")
        return True
    else:
        print(f"  [FAIL] {match_id} 处理失败")
        print(f"  stderr: {(result.stderr or '')[-200:]}")
        return False


def run_once():
    """单次检查并处理新比赛"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 检查 Overview...")

    html = fetch_overview()
    if not html:
        return

    matches = parse_matches(html)
    state = load_state()

    finished = [(mid, url, sched) for mid, url, done, sched in matches if done]
    upcoming = [(mid, url, sched) for mid, url, done, sched in matches if not done]

    print(f"  已打完: {len(finished)} 场  |  未开打: {len(upcoming)} 场")

    new_matches = []
    for mid, url, sched in finished:
        if mid not in state:
            new_matches.append((mid, url))
            print(f"  [NEW] {mid}")
        else:
            print(f"  [SKIP] {mid} (已处理)")

    if not new_matches:
        print("  没有新比赛需要处理。")
        return

    # 逐个处理新比赛
    for mid, url in new_matches:
        success = process_match(mid, url)
        state[mid] = {
            "processed_at": datetime.now().isoformat(),
            "url": url,
            "success": success
        }
        save_state(state)

    print(f"\n处理完成: {len(new_matches)} 场新比赛")


def watch_loop(interval_minutes=30):
    """持续监控循环"""
    print(f"启动监控模式，每 {interval_minutes} 分钟检查一次...")
    print(f"按 Ctrl+C 停止\n")
    try:
        while True:
            run_once()
            print(f"\n下次检查: {interval_minutes} 分钟后...")
            time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        print("\n监控已停止。")


if __name__ == '__main__':
    if '--watch' in sys.argv:
        watch_loop()
    else:
        run_once()
