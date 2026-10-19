# Диаг. (19.10) D: проверка цепочки JSON -> overlays (values-ru/values) -> наличие собранного RRO-APK.
import os
"""Этап D: для ключей группы A проверяем цепочку:
   translations JSON (ru) -> overlays/<app>/res/values-ru/strings.xml -> APK (aapt2).
   А также APK's-а: есть ли, когда собран, есть ли имя внутри (через strings/binary grep)."""
import glob, os, re, json, subprocess, sys

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (app, name, screen_context)
targets = [
    ("WT_NewLauncher", "more", "детали сценария"),
    ("WT_WtSystemUI", "wifi_status_disconnected", "networks list WiFi"),
    ("WT_AISceneMode", "custom_scene_execute_selected_normal_text", "execute sequentially"),
    ("WT_VehicleCenter", "lyrics", "lyrics"),
    ("WT_VehicleCenter", "left", "left edge slider"),
    ("WT_VehicleCenter", "right", "right edge slider"),
    ("WT_NewLauncher", "slow_sequence", "slow sequence (launcher widget)"),
    ("WT_SmartSoundEffect", "slow_sequence", "slow sequence (sound)"),
    ("WT_SmartSoundEffect", "root_nav_mute", "lock sound"),
    ("WT_SmartSoundEffect", "classic", "classical"),
    ("WT_SmartSoundEffect", "tips_them_type_default", "classical (tips)"),
    ("WT_VehicleCenter", "inside_light_more_setting", "more (energy screen?)"),
    ("WT_VehicleCenter", "memory_more", "more (energy screen?)"),
    ("WT_VehicleCenter", "outside_light_more_setting", "more (energy screen?)"),
    ("WT_VehicleCenter", "head_lighting_height", "headlight height"),
    ("WT_VisualizationService", "osd_seat_position_zero_gravity", "zero gravity mode"),
    ("WT_VisualizationService", "text_open_zero_gravity", "zero gravity mode"),
]

# 1) translations/ JSON
json_ru = {}
for app, name, _ in targets:
    fp = f"{P}/translations/{app}.json"
    if not os.path.exists(fp):
        continue
    lst = json.load(open(fp, encoding="utf-8"))
    for e in lst:
        if e.get("name") == name:
            json_ru[(app, name)] = e.get("ru") or ""

# 2) overlays
def overlay_val(app, name):
    out = []
    for base in ("overlays", "overlays_static"):
        for cfg in ("values-ru", "values"):
            fp = f"{P}/{base}/{app}/res/{cfg}/strings.xml"
            if os.path.exists(fp):
                txt = open(fp, encoding="utf-8", errors="replace").read()
                m = re.search(r'<string name="%s">(.*?)</string>' % re.escape(name), txt, re.S)
                out.append((base, cfg, (m.group(1)[:60].replace("\n", " ") if m else None)))
    return out

# 3) APK presence and mtime
def apk_info(app):
    res = []
    for base in ("apks_rro_min", "apks_rro_static"):
        fp = f"{P}/{base}/{app}_RRO.apk"
        if os.path.exists(fp):
            st = os.stat(fp)
            import datetime
            res.append((base, datetime.datetime.fromtimestamp(st.st_mtime).strftime("%m-%d %H:%M")))
    return res

print(f"{'app/name':55} | json.ru | overlays values-ru | APK built")
for app, name, ctx in targets:
    j = json_ru.get((app, name))
    ov = overlay_val(app, name)
    apks = apk_info(app)
    ov_ru = next((v for b, c, v in ov if c == "values-ru"), "?")
    ov_def = next((v for b, c, v in ov if c == "values"), "?")
    print(f"{app}/{name}:55"[:55],
          "|", (j or "<нет в json>")[:30],
          "| ru:", (ov_ru or "<НЕТ>")[:30],
          "| def:", (ov_def or "<НЕТ>")[:30],
          "| APK:", apks)
