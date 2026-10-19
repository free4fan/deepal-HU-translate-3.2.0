# Диаг. (19.10) J: точная статистика layout-литералов: файлы x атрибуты x приложения.
import os
"""Точная пересказочность: по файлам и по атрибутам."""
import glob, os, re, collections

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "decompiled")
ATTRS = ("android:text", "android:hint", "android:contentDescription",
         "android:title", "android:subtitle", "android:label")
files_hit = 0
by_file = collections.Counter()
by_attr = collections.Counter()
by_app_files = collections.Counter()
by_app_attrs = collections.Counter()
shared_lib_files = collections.Counter()

for appdir in sorted(glob.glob(P + "/*/res")):
    app = os.path.basename(os.path.dirname(appdir.rstrip("/")))
    for root, dirs, files in os.walk(appdir):
        b = os.path.basename(root)
        if not b.endswith("layout"):
            continue
        for fn in files:
            if not fn.endswith(".xml"):
                continue
            fp = os.path.join(root, fn)
            try:
                txt = open(fp, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            n = 0
            for a in ATTRS:
                n += len(re.findall(re.escape(a) + r'="([^"]*[\u4e00-\u9fff][^"]*)"', txt))
            if n:
                files_hit += 1
                rel = os.path.relpath(fp, appdir)
                by_file[(app, rel)] = n
                by_app_files[app] += 1
                by_app_attrs[app] += n

print("layout-файлов с CJK-видимыми атрибутами:", files_hit)
print("сумма атрибутов:", sum(by_app_attrs.values()))
print()
print("по приложениям (файлов / атрибутов):")
for a in sorted(by_app_files, key=lambda x: -by_app_attrs[x]):
    print(f"  {a:26} {by_app_files[a]:4} файлы / {by_app_attrs[a]:5} атр.")
print()
print("самые плотные файлы (топ-15):")
for (app, rel), n in by_file.most_common(15):
    print(f"  {n:4}  {app}/{rel}")
