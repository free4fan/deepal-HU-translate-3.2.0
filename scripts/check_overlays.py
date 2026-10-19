# Диаг. (18.10): видимость новых wake-word-строк в values-ru/values/values-zh-rCN обоих наборов оверлеев.
import os
import re, glob, xml.etree.ElementTree as ET
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

names = ["voice_custom_wake_work_hint", "voice_wakeup_hint"]
for base in ["overlays", "overlays_static"]:
    print("##########", base, "##########")
    for f in sorted(glob.glob(f"{ROOT}/{base}/WT_VehicleCenter/res/values*/strings.xml")):
        cfg = f.split("/res/")[1].split("/strings.xml")[0]
        try:
            root = ET.parse(f).getroot()
        except Exception as ex:
            print(" ", cfg, "PARSE-ERROR:", ex); continue
        for n in names:
            el = [e for e in root if e.tag == "string" and e.get("name") == n]
            if el:
                print(f"  [{cfg}/{n}] {el[0].text!r}"[:200])
            else:
                print(f"  [{cfg}/{n}] <отсутствует>")
