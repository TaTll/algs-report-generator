#!/usr/bin/env python3
"""
ALGS 数据 → 剪映工程文件
导入雷达图 + 选手照片 + 战队Logo → 三轨道时间轴，配选手名字幕

用法:
  python build_jy_video.py --group ac
  python build_jy_video.py --group bd --name "ALGS_BD_Group"
"""
import os, sys, csv, re, argparse

# ====== 环境初始化 ======
current_dir = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = r"C:\Users\嘟嘟\AppData\Roaming\reasonix\skills\jianying-editor"
if not os.path.exists(os.path.join(SKILL_ROOT, "scripts", "jy_wrapper.py")):
    raise ImportError(f"JianYing skill not found at: {SKILL_ROOT}")

sys.path.insert(0, os.path.join(SKILL_ROOT, "scripts"))
from jy_wrapper import JyProject

BASE_DIR = os.path.dirname(current_dir)
DATA_DIR = os.path.join(BASE_DIR, "data")
PHOTO_DIR = os.path.join(DATA_DIR, "picture-ab")
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
from team_utils import find_player_photo, get_team_abbr

DURATION = "3s"


def build_video(group, draft_name=None):
    """主流程：读取 CSV → 匹配素材 → 创建剪映工程"""
    group_dir = os.path.join(DATA_DIR, group)
    csv_path = os.path.join(group_dir, "algs_players_data.csv")
    radar_dir = os.path.join(group_dir, "radar_charts")

    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}")
        return

    if draft_name is None:
        draft_name = f"ALGS_{group.upper()}_Group"

    # 读取选手
    players = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            players.append(row)
    players.sort(key=lambda p: (p.get('Team', ''), p.get('Player', '')))
    print(f"Players: {len(players)}")

    # 匹配素材
    player_assets = []
    for p in players:
        name = p['Player']
        team = p['Team']
        name_slug = re.sub(r'[\\/:*?"<>| ]', '_', name)
        name_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', name_slug)
        radar_path = os.path.join(radar_dir, f"{name_slug}.png")
        photo_path, abbr = find_player_photo(name, team_name=team)

        player_assets.append({
            'name': name, 'team': team,
            'radar': radar_path if os.path.exists(radar_path) else None,
            'photo': photo_path, 'abbr': abbr,
        })

    has_radar = sum(1 for a in player_assets if a['radar'])
    has_photo = sum(1 for a in player_assets if a['photo'])
    print(f"Radar: {has_radar}/{len(players)}, Photos: {has_photo}/{len(players)}")

    # 收集战队Logo
    team_logos = {}
    for a in player_assets:
        if a['abbr'] and a['abbr'] not in team_logos:
            lp = os.path.join(PHOTO_DIR, f"{a['abbr']}.png")
            if os.path.exists(lp):
                team_logos[a['abbr']] = lp
    print(f"Logos: {len(team_logos)}")

    # 创建剪映工程
    project = JyProject(draft_name, overwrite=True)
    time_offset = 0

    for i, a in enumerate(player_assets):
        t_str = f"{time_offset}s"

        if a['radar']:
            project.add_media_safe(a['radar'], t_str, duration=DURATION, track_name="Radar")
            project.add_text_simple(
                f"{a['name']} ({a['team']})",
                start_time=t_str, duration=DURATION, anim_in="渐显"
            )

        if a['photo']:
            project.add_media_safe(a['photo'], t_str, duration=DURATION, track_name="Photo")

        if a['abbr'] and a['abbr'] in team_logos:
            project.add_media_safe(team_logos[a['abbr']], t_str, duration=DURATION, track_name="Logo")

        time_offset += 3

        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(players)}")

    project.save()
    total_min = time_offset / 60
    print(f"\nDone! Duration: {time_offset}s ({total_min:.1f} min)")
    print(f"Draft: {draft_name}")
    print(f"Open JianYing and refresh draft list to see it.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ALGS 数据 → 剪映工程")
    parser.add_argument("--group", "-g", required=True, help="组别 (如 ac, bd, ab, cd)")
    parser.add_argument("--name", "-n", default=None, help="草稿名称 (默认 ALGS_{GROUP}_Group)")
    parser.add_argument("--duration", "-d", default="3s", help="每张图时长 (默认 3s)")
    args = parser.parse_args()
    DURATION = args.duration
    build_video(args.group, args.name)
