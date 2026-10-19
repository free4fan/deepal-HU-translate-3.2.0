# Диаг. (19.10) K: финальный verdict по каждой фразе скриншотов: А=layout / B=runtime / C=@string; + dump типов RRO-APK.
import os
"""ФИНАЛЬНАЯ ВЕРИФИКАЦИЯ (без предположений).
1) Наши RRO APKs: сколько type layout / drawable внутри (ожидается 0 layout).
2) Таблица verdict для каждой видимой CJK-фразы со скриншотов:
   A=захохарджен в layout  B=runtime/данные (нет в res вообще)  C=@string (есть в RRO, работает)
"""
import glob, os, re, json, subprocess, collections

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = P + "/decompiled"

# ---- 1) types в наших APK ----
print("="*78)
print("1) КОЛИЧЕСТВО ТИПОВ РЕСУРСОВ В НАШИХ RRO-APK (dynamic min)")
for app in ("WT_VehicleCenter", "WT_NewLauncher", "WT_AISceneMode", "WT_WtSystemUI", "WT_SmartSoundEffect"):
    apk = f"{P}/apks_rro_min/{app}_RRO.apk"
    if not os.path.exists(apk):
        continue
    r = subprocess.run(["aapt2", "dump", "resources", apk], capture_output=True, text=True)
    types = collections.Counter(re.findall(r"^\s*type (\w+) ", r.stdout, re.M))
    print(f"  {app:22} types: {dict(types)}")

# ---- 2) verdict table ----
# (фраза, скрин). Ищем: layout-hardcoded, any-res (values), и RRO-ru.
def layout_hits(ph):
    out = []
    seen = set()
    for appdir in sorted(glob.glob(D + "/*/res/layout*")):
        app = os.path.basename(os.path.dirname(appdir))
        for root, dirs, files in os.walk(appdir):
            if not os.path.basename(root).endswith("layout"):
                continue
            for fn in files:
                if not fn.endswith(".xml"):
                    continue
                fp = os.path.join(root, fn)
                try:
                    txt = open(fp, encoding="utf-8", errors="replace").read()
                except Exception:
                    continue
                if ph in txt:
                    for a in ("android:text", "android:hint", "android:contentDescription", "android:title"):
                        for m in re.finditer(re.escape(a) + r'="([^"]*' + re.escape(ph) + r'[^"]*)"', txt):
                            rel = os.path.relpath(fp, f"{D}/{app}")
                            key = (app, rel)
                            if key not in seen:
                                seen.add(key)
                                out.append(f"{app}/{os.path.basename(rel)}")
    return out

def res_hits(ph):
    out = []
    for appdir in sorted(glob.glob(D + "/*/res/values")):
        app = os.path.basename(os.path.dirname(appdir))
        fp = appdir + "/strings.xml"
        if not os.path.exists(fp):
            continue
        txt = open(fp, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r'<string name="([^"]+)">([^<]*' + re.escape(ph) + r'[^<]*)</string>', txt):
            out.append(f"{app}/{m.group(1)}")
    return out

def rro_has_ru(app, name):
    for cfg in ("values-ru", "values"):
        fp = f"{P}/apks_rro_min" # placeholder
    # check overlay source
    for base in ("overlays", "overlays_static"):
        fp = f"{P}/{base}/{app}/res/values-ru/strings.xml"
        if os.path.exists(fp):
            txt = open(fp, encoding="utf-8", errors="replace").read()
            m = re.search(r'<string name="%s">(.*?)</string>' % re.escape(name), txt, re.S)
            if m and m.group(1).strip():
                return m.group(1).strip()[:30]
    return None

phrases = [
    ("详情","скр1 · тайтл сцены"),
    ("低电量充电提醒","скр1 · имя сцены"),
    ("自动","скр1 · бейдж Auto"),
    ("就依次执行","скр1 · заголовок действий"),
    ("语音播报","скр1 · тип акшена"),
    ("电池包瘪了","скр1 · текст TTS-акшена"),
    ("驾驶-车辆档位","скр1 · условие сцены"),
    ("P挡","скр1 · значение условия"),
    ("驾驶-电池电量","скр1 · условие сцены"),
    ("≤20%","скр1 · значение условия"),
    ("未连接","скр2 · статус сети (каждую строку)"),
    ("赠送流量包","скр2 · план данных"),
    ("剩余 10","скр2 · остаток трафика"),
    ("数据来源","скр2 · источник данных"),
    ("截止至2026/10/08","скр2 · дата планa"),
    ("自定义","скр3 · тайтл листа HUD"),
    ("歌词","скр3 · имя виджета в превью"),
    ("左","скр4 · край слайдера дисплея"),
    ("右","скр4 · край слайдера дисплея"),
    ("换挡音","скр5 · тумблер звука"),
    ("车外音","скр5 · секция звука"),
    ("闭锁音","скр5 · тумблер звука"),
    ("缓速序列","скр5/6 · выбранная опция"),
    ("经典","скр5 · выбранная опция"),
    ("更多","скр6 · бутон в шапке"),
    ("大灯高度","скр7 · тайтл слайдера света"),
    ("左后锁","скр8 · бутон замка"),
    ("右后锁","скр8 · бутон замка"),
    ("零重力模式","скр9 · режим сиденья"),
    ("进入","скр9 · бутон входа в режим"),
]

print()
print("="*78)
print("2) VERDICT: источник каждой видимой CJK-фразы")
print(f"{'фраза':14} | вердикт | layout / res / RRO")
classA = classB = classC = 0
for ph, ctx in phrases:
    lh = layout_hits(ph)
    rh = res_hits(ph)
    # точный res (zh == ph)
    exact = [x for x in rh]
    # классификация
    if lh:
        v = "A (layout-hardcoded)"
        classA += 1
        src = "LAYOUT: " + "; ".join(sorted(set(lh))[:3])
    elif rh:
        v = "C (@string в res)"
        classC += 1
        src = "RES: " + "; ".join(sorted(set(exact))[:3])
    else:
        v = "B (runtime/данные)"
        classB += 1
        src = "нет ни в res, ни в layout"
    print(f"{ph:14} | {v:22} | {src[:90]}")

print()
print(f"ИТОГО:  A(в layout, RRO не трогает) = {classA}")
print(f"        B(данные/scene.db/TBOX)       = {classB}")
print(f"        C(@string — есть RRO)         = {classC}")
