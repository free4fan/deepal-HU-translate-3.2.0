# Диаг. (18–19.10): какие записи wt_vehiclecenter.json содержат CJK в поле `ru` (wake-words).
import os
import json, re
path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "translations", "WT_VehicleCenter.json")
data = json.load(open(path, encoding="utf-8"))
cjk = re.compile(r'[\u3000-\u303f\u4e00-\u9fff\u3400-\u4dbf\uff00-\uffef]')
hits = []
for e in data:
    ru = e.get("ru","") or ""
    if cjk.search(ru):
        hits.append((e.get("name"), e.get("zh",""), ru))
print("Total entries:", len(data))
print("Entries with CJK in ru:", len(hits))
for name, zh, ru in hits:
    print("=" * 70)
    print("NAME:", name)
    print("ZH  :", zh)
    print("RU  :", ru)
