# Диаг. (19.10) A: субстроковый поиск zh-фраз скриншотов по translations/*.json (app, name, ru).
import os
"""Исследование: китайские фразы с ГУ — где они в пайплайне?
Этап A: поиск zh-фраз в translations/*.json (app, name, ru).
"""
import json, glob, re, unicodedata

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

phrases = [
    # Скрин 1: умные сценарии (детали сценария)
    "详情", "低电量充电提醒", "自动", "就依次执行", "语音播报", "电池包瘪了",
    "驾驶-车辆档位", "P挡", "驾驶-电池电量",
    # Скрин 2: сети/WiFi
    "未连接", "剩余", "赠送流量包", "数据来源",
    # Скрин 3: кастомный HUD
    "自定义", "歌词",
    # Скрин 4: дисплей, центр экран
    "左", "右",
    # Скрин 5: звук
    "换挡音", "车外音", "缓速序列", "闭锁音", "经典",
    # Скрин 6: энергия
    "更多",
    # Скрин 7: освещение
    "大灯高度",
    # Скрин 8: кузов
    "左后锁", "右后锁",
    # Скрин 9: сиденье
    "零重力模式", "进入",
]

# считаем JSON один раз
data = {}
for f in sorted(glob.glob(P + "/translations/*.json")):
    app = f.split("/")[-1][:-5]
    try:
        lst = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    if isinstance(lst, list):
        data[app] = lst

for ph in phrases:
    print("=" * 78)
    print(f"ФРАЗА: {ph}")
    hits = 0
    for app, lst in data.items():
        for e in lst:
            zh = e.get("zh") or ""
            if ph in zh:
                hits += 1
                ru = e.get("ru") or ""
                flag = "" if ru else "  *** ПУСТОЙ RU ***"
                print(f"  [{app}/{e.get('name')}] zh={zh[:60]!r}")
                print(f"      ru={ru[:90]!r}{flag}")
    if hits == 0:
        print("  --- НЕТ в translations/*.json ---")
