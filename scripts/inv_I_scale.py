# Диаг. (19.10) I: оценка масштаба layout-литералов по всем приложениям (насыщенность, топы).
import os
"""Оценка масштаба: захардкоженные CJK-литералы в layout-атрибутах всех 106 аппов."""
import glob, os, re, collections

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "decompiled")
CJK = re.compile(r'[\u4e00-\u9fff]')
# атрибуты, которые реально видны пользователю
ATTR_RE = re.compile(r'(?:android:[a-z]+:?)=')

total_by_app = collections.Counter()
total_files = 0
samples = collections.defaultdict(list)

for appdir in sorted(glob.glob(P + "/*/res")):
    app = os.path.basename(os.path.dirname(appdir.rstrip("/")))
    cnt = 0
    for root, dirs, files in os.walk(appdir):
        b = os.path.basename(root)
        if b.startswith("values") or not b.endswith("layout"):
            continue
        for fn in files:
            if not fn.endswith(".xml"):
                continue
            fp = os.path.join(root, fn)
            try:
                txt = open(fp, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            if not CJK.search(txt):
                continue
            # ищем quote-атрибуты = "....CJK...."
            for m in re.finditer(r'([\w:]+)="([^"]*[\u4e00-\u9fff][^"]*)"', txt):
                attr, val = m.group(1), m.group(2)
                if attr in ("android:text", "android:hint", "android:contentDescription",
                            "android:title", "android:subtitle", "android:label",
                            "contentDescription", "title"):
                    cnt += 1
                    if len(samples[app]) < 8:
                        samples[app].append(f"{os.path.relpath(fp, appdir)}: {attr}={val[:40]!r}")
    if cnt:
        total_by_app[app] = cnt
        total_files += 1

print("всего layout-файлов с CJK-литералами:", total_files)
print("всего видимых CJK-аудибельных атрибутов:", sum(total_by_app.values()))
print()
print("Топ приложений (апп: кол-во литералов):")
for a, c in total_by_app.most_common(15):
    print(f"  {a:28} {c}")
print()
print("Примеры (первые 30):")
shown = 0
for a in sorted(samples):
    for s in samples[a][:3]:
        print(f"  [{a}] {s}")
        shown += 1
        if shown >= 30:
            break
    if shown >= 30:
        break
