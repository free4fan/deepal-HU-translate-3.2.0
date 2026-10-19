# Диаг. (19.10) C: поиск тех же zh-текстов в decompiled/*/res — фиксация владельца ресурса в ROM.
import os
"""Этап C: поиск точных zh-текстов в decompiled/*/res/values*/<strings|arrays>.xml.
Говорит, ЧЬИ (какое приложение) это строки в ROM-пакете 3.2.0."""
import glob, os, re, json, unicodedata
from xml.etree import ElementTree as ET

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

phrases = [
    "详情", "低电量充电提醒", "自动就依次执行", "就依次执行", "语音播报", "电池包瘪了",
    "驾驶-车辆档位", "P挡", "驾驶-电池电量", "≤20%",
    "未连接", "剩余", "赠送流量包", "数据来源", "10G/月",
    "自定义", "歌词",
    "左", "右",
    "换挡音", "车外音", "缓速序列", "闭锁音", "经典",
    "更多",
    "大灯高度",
    "左后锁", "右后锁",
    "零重力模式", "进入",
]

CJK = re.compile(r'[\u4e00-\u9fff].{0,60}')

def normalize(s):
    """Нормализуем: убираем NBSP, все виды кавычек — как в ROM-XML и на экране."""
    if not s:
        return ""
    s = s.replace('\u3000', ' ').replace('\u00a0', ' ')
    return re.sub(r'\s+', ' ', s).strip()

# строим карту: zh_text -> [(app, file, kind, name)]
text2loc = {}
dirs = sorted(glob.glob(P + "/decompiled/*/res/values*"))
for d in dirs:
    app = d.split("/decompiled/")[1].split("/")[0]
    for fn in ("strings.xml", "arrays.xml", "plurals.xml"):
        fp = os.path.join(d, fn)
        if not os.path.exists(fp):
            continue
        try:
            txt = open(fp, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        # strings: <string name="x">TEXT</string>
        for m in re.finditer(r'<(string|array|item|plurals|item)\b[^>]*name="([^"]+)"[^>]*>(.*?)</\1>', txt, re.S):
            tag, name, body = m.group(1), m.group(2), m.group(3)
            text2loc.setdefault(normalize(body), []).append((app, fn, tag, name))
        # arrays: <string-array name="x"><item>T</item>...</string-array>
        for m in re.finditer(r'<string-array name="([^"]+)"[^>]*>(.*?)</string-array>', txt, re.S):
            name, body = m.group(1), m.group(2)
            for it in re.finditer(r'<item>.*?>(.*?)</item>', body, re.S):
                text2loc.setdefault(normalize(it.group(1)), []).append((app, fn, "array-item", name))
        for m in re.finditer(r'<integer-array name="([^"]+)"', txt):
            pass

print("уникальных zh-текстов в res: ", len(text2loc))
print()
for ph in phrases:
    n = normalize(ph)
    hits = text2loc.get(n, [])
    # фолбэк: поиск подстрок
    if not hits:
        for t, locs in text2loc.items():
            if n in t:
                hits = [(a, f, k, nm, t) for a, f, k, nm in locs]
                break
        else:
            hits = None
    print("=" * 74)
    if hits is None:
        print(f"{ph}: --- НЕТ ни точного, ни подстрокового в decompiled/*/res ---")
    else:
        # укоротим: покажем локацию и сам текст
        seen = set()
        for h in hits[:12]:
            if len(h) == 5:
                app, fn, kind, name, orig_txt = h
                print(f"  [подстрока в «{orig_txt[:50]}»]  {app}/{fn}:{kind} name={name}")
            else:
                app, fn, kind, name = h
                print(f"  {app}/{fn}:{kind} name={name}")
