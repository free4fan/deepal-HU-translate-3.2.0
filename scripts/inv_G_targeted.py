# Диаг. (19.10) G: точечный поиск конкретных фраз в res (values* + layout) отдельных приложений.
import os
"""Этап G: точечный поиск в res конкретных приложений."""
import glob, os, re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "decompiled")

searches = [
    # (app_dir, needle, comment)
    ("WT_VehicleCenter", "换挡", "toggle 'шifter sound'"),
    ("WT_VehicleCenter", "车外音", "section 'ext. sound'"),
    ("WT_VehicleCenter", "大灯高度", "label 'headlight height'"),
    ("WT_VehicleCenter", "后锁", "buttons left/right rear lock"),
    ("WT_VehicleCenter", "缓速", "chip slow-sequence"),
    ("WT_VehicleCenter", "经典", "chip classic"),
    ("WT_VehicleCenter", "闭锁", "label lock sound"),
    ("WT_VehicleCenter", "更多", "energy-page button 'more'"),
    ("WT_VehicleCenter", "零重力", "zero gravity label"),
    ("WT_VehicleCenter", "进入", "enter button"),
    ("WT_VehicleCenter", "歌词", "lyrics label"),
    ("WT_VehicleCenter", "数据来源", "network data source"),
    ("WT_VehicleCenter", "电池电量", "condition battery level"),
    ("WT_VehicleCenter", "车辆档位", "condition gear"),
    ("WT_AISceneMode", "低电量", "scene: low-battery charging"),
    ("WT_AISceneMode", "充电提醒", "scene: charging remind"),
    ("WT_AISceneMode", "语音播报", "scene action voice-broadcast"),
    ("WT_AISceneMode", "自定义", "scene custom"),
    ("WT_NewLauncher", "歌词", "launcher media card"),
    ("WT_NewLauncher", "自定义", "launcher hud custom title"),
    ("WT_NewLauncher", "赠送流量", "data package"),
    ("WT_SmartSoundEffect", "换挡", "shift change sound"),
    ("WT_SmartSoundEffect", "车外", "outside car sound"),
]

for app, needle, comment in searches:
    base = f"{P}/{app}/res"
    print("=" * 74)
    print(f"{app}  needle='{needle}'  ({comment})")
    hits = 0
    for root, dirs, files in os.walk(base):
        if os.path.basename(root).startswith("values"):
            continue
        for fn in files:
            fp = os.path.join(root, fn)
            try:
                txt = open(fp, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            if needle not in txt:
                continue
            hits += 1
            rel = os.path.relpath(fp, f"{P}/{app}")
            for m in re.finditer(re.escape(needle), txt):
                s, e = m.start(), m.end()
                frag = txt[max(0, s - 120): e + 60].replace("\n", " ")
                keym = re.findall(r'([\w:]+)="[^"]*$', txt[max(0, s - 260):s])
                print(f"  {rel}  attr={(keym[-1] if keym else '?')}")
                print(f"     …{frag[:200]}")
    if hits == 0:
        print("   --- нет вне values ---")

# отдельный проход по values* этих же приложений
print()
print("#" * 74)
print("# values* файлы (strings/arrays/plurals/xml)")
# ------------------------------------------------
for app, needle, comment in searches:
    base = f"{P}/{app}/res"
    out = []
    for fn in sorted(glob.glob(base + "/values*/*.xml")):
        try:
            txt = open(fn, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if needle not in txt:
            continue
        cfg = fn.split("/res/")[1].rsplit("/", 1)[0]
        # все строки с needle
        for m in re.finditer(r'name="([^"]+)"[^>]*(?:/>|>([^<]*<[^/][^<]*)?<)', txt):
            nm = m.group(1)
            if needle in (m.group(2) or ""):
                out.append((cfg, nm, (m.group(2) or "").replace("\n", " ")[:50]))
    print(f"{app} '{needle}' in values*:")
    for o in out[:10]:
        print(f"   [{o[0]}] {o[1]}  {o[2]!r}")
    if not out:
        # вдруг needle в файле как часть array-item без нормального regex
        anyval = [fn for fn in glob.glob(base + "/values*/*.xml") if needle in open(fn, encoding="utf-8", errors="replace").read()]
        if anyval:
            print(f"   (есть упоминания, но не распарсились: {len(anyval)} файлов)")
        else:
            print("   --- нет и в values* ---")
