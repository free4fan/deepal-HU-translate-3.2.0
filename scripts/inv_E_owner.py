# Диаг. (19.10) E: по ПЕРЕВЕДЁННЫМ (ru) строкам экрана находим owner-app (чьи это res).
import os
"""Этап E: по ПЕРЕВЕДЁННЫМ (ru) строкам с экранов находим, ЧЬЕ это res (owner app).
Для каждой видимой RU-фразы: точный поиск в r u поля всех JSON -> (app, name, zh).
Это фиксирует приложение, рисующее экран."""
import json, glob

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

data = {}
for f in sorted(glob.glob(P + "/translations/*.json")):
    app = f.split("/")[-1][:-5]
    try:
        lst = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    if isinstance(lst, list):
        data[app] = lst

ru_phrases = [
    # скрин2: сети/трафик
    "Доступные сети", "Остаток общего трафика", "Купить трафик", "Детали пакета",
    "Связь WeChat", "Подкл. устр-ва",
    # скрин3: HUD кастом
    "Помощь водителю", "AR-навигация", "Упрощённая навигация", "Мини-карта",
    "Уровень заряда", "Bluetooth-телефон", "Текст песни", "Сохранить",
    # скрин4: дисплей
    "Центр. экран", "Калибровка", "По центру", "Умный поворот",
    # скрин5/6: звук
    "Звук при касании", "Выкл.", "Низкий", "Средний", "Высокий", "Озвучка зарядки",
    # скрин6: энергия
    "Отложенная зарядка", "Внешняя разрядка", "Авто-разблокировка АС",
    "Укажите время брони", "WLTC", "Поездка",
    # скрин1: сцена
    "Если", "И выполнены заранее", "Редактиров", "Выполнить",
    # общие
    "Автомобиль", "Вожжение", "Казов", "Освещение", "Энергия", "Звук", "Дисплей",
    "Управление",
]

idx = {}  # ru_text -> [(app, name, zh)]
for app, lst in data.items():
    for e in lst:
        ru = (e.get("ru") or "").strip()
        if ru:
            idx.setdefault(ru, []).append((app, e.get("name"), (e.get("zh") or "").strip()))

for ph in ru_phrases:
    hits = idx.get(ph, [])
    # подстроковый fallback
    if not hits:
        for t, locs in idx.items():
            if ph in t:
                for a, n, z in locs:
                    hits.append((a, n, z, f"подстрок: {t[:40]!r}"))
                break
    print("=" * 72)
    print(f"RU '{ph}':")
    if not hits:
        print("   --- не найдено (возможно, это RU из системного или runtime) ---")
    else:
        for h in hits[:8]:
            if len(h) == 4:
                print(f"   {h[0]}/{h[1]}  zh={h[2]!r}  {h[3]}")
            else:
                print(f"   {h[0]}/{h[1]}  zh={h[2]!r}")
