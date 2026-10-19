# Диаг. (19.10) H: presence public.xml по ключевым приложениям (private layout = только static RRO).
import os
"""Этап H: финальные проверки.
1) public.xml: layouts — public или private (для RRO-override layouts).
2) root_default_lyric в JSON.
3) AndroidManifest static RRO (isStatic, targetPackage).
"""
import glob, os, re, json

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

layouts_interest = {
    "WT_VehicleCenter": [
        "fragment_sound_new", "fragment_ligth_setting_outside_c857",
        "view_function_title_with_select", "item_device_recycleview",
        "item_bluetooth_recycleview", "dialog_passenger_seat_adjust_zero_gravity",
        "fragment_idd_setting_energy", "fragment_network", "customization_hud",
        "dialog_energy_more_setting",
    ],
    "WT_AISceneMode": ["activity_scene_preview", "item_exec_conflict_content", "item_condition_conflict_dialog_content"],
    "WT_NewLauncher": ["fragment_driving_car_last", "fragment_driving_car_last_hor",
                       "c857_media_card", "c857_media_card_mini", "network_card_layout", "network_card_land_layout"],
}

for app, layouts in layouts_interest.items():
    pubf = f"{P}/decompiled/{app}/public.xml"
    pub = set()
    if os.path.exists(pubf):
        txt = open(pubf, encoding="utf-8", errors="replace").read()
        pub = set(re.findall(r'name="([^"]+)"\s+type="layout"', txt))
    print("=" * 74)
    print(f"{app}:  public layouts total={len(pub)}")
    for L in layouts:
        print(f"   {L:45} {'PUBLIC' if L in pub else 'PRIVATE (только static RRO может)'}")

# root_default_lyric в JSON
print("=" * 74)
print("root_default_lyric / локальные lyrics-строки:")
for app in ("WT_MultiMediaCenter", "WT_NewLauncher", "WT_VehicleCenter"):
    fp = f"{P}/translations/{app}.json"
    lst = json.load(open(fp, encoding="utf-8"))
    for e in lst:
        if e.get("name") in ("root_default_lyric", "lyrics", "local_no_lrcy", "not_parking_not_open_lyric"):
            print(f"  {app}/{e['name']}  zh={e['zh']!r}  ru={e['ru']!r}")

# manifest static RRO (пример)
print("=" * 74)
m = f"{P}/overlays_static/WT_VehicleCenter/AndroidManifest.xml"
print(open(m, encoding="utf-8").read()[:900])
