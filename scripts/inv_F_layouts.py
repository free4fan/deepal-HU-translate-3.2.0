# Диаг. (19.10) F: CJK-литералы, захардкоженные в layout-XML (android:text/hint/contentDescription).
import os
"""Этап F: поиск ПОИСКА фраз, захардкоженных прямо в layout XML
(android:text="..." / android:hint=... и т.п.), а также в других типах res (menu, drawable, xml).
Эти строки RRO НЕ трогает — они зашиты в layout."""
import glob, os, re
from xml.etree import ElementTree as ET

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "decompiled")

phrases = [
    # (фраза, скрин)
    ("详情", "1"), ("低电量充电提醒", "1"), ("自动", "1"), ("就依次执行", "1"),
    ("语音播报", "1"), ("电池包瘪了", "1"), ("驾驶-车辆档位", "1"), ("P挡", "1"),
    ("驾驶-电池电量", "1"), ("≤20%", "1"),
    ("未连接", "2"), ("赠送流量包", "2"), ("数据来源", "2"),
    ("自定义", "3"), ("歌词", "3"), ("零重力模式", "9"), ("进入", "9"),
    ("左", "4"), ("右", "4"),
    ("换挡音", "5"), ("车外音", "5"), ("闭锁音", "5"),
    ("更多", "6"),
    ("大灯高度", "7"),
    ("左后锁", "8"), ("右后锁", "8"),
]

# собираем все XML в res/ ИСКЛЮЧАЯ values (values уже проверены)
hits = {p: [] for p, _ in phrases}

for d in sorted(glob.glob(P + "/*/res")):
    app = d.split("/")[3]
    for root, dirs, files in os.walk(d):
        # пропустим values*
        if os.path.basename(root).startswith("values"):
            continue
        for fn in files:
            if not fn.endswith(".xml"):
                continue
            fp = os.path.join(root, fn)
            try:
                txt = open(fp, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            if not any(p in txt for p, _ in phrases):
                continue
            rel = os.path.relpath(fp, f"{P}/{app}")
            for p, scr in phrases:
                # в attribute: ="...фраза..."  или >фраза<  как текст
                for m in re.finditer(re.escape(p), txt):
                    s, e = m.start(), m.end()
                    # контекст: ближайший атрибут
                    frag = txt[max(0, s - 90): e + 40]
                    # наймем key=
                    keym = re.findall(r'([a-zA-Z_:][\w:]*)="[^"]*$', txt[max(0, s - 200):s])
                    hits[p].append((app, rel, (keym[-1] if keym else "?"), frag.replace("\n", " ")[:150]))
                    break  # 1 hit per file per phrase enough -> no, continue collect but limit
            if all(len(hits[p]) >= 3 for p, _ in phrases):
                pass

for p, scr in phrases:
    print("=" * 76)
    print(f"ФРАЗА '{p}' (скрин {scr}):  layout-res hits={len(hits[p])}")
    for h in hits[p][:6]:
        print(f"   [{h[0]}] {h[1]}  attr={h[2]}")
        print(f"      …{h[3]}")
