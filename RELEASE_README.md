# Deepal HU Translate v3.2.0 — установка

Русский перевод ГУ **Deepal / Changan S05** (прошивка 3.2.0): 102 приложения
(экраны, меню, диалоги) — строки GUI. Проводится **RRO-оверлеями** (APK,
которые русские строки накладывают поверх китайских). **Проводку не трогает:**
перевод в любой момент снимается, ГУ возвращается в исходное состояние.

## Состав папки

| Файл | Что |
|---|---|
| `apks_rro_min/` — 100 APK (+ `.idsig`) | **Динамические** RRO (`com.android.vendor.translate.rro.*`): ставятся как обычные приложения, включаются/выключаются через `overlay enable` — без root |
| `apks_rro_static/` — 100 APK (+ `.idsig`) | **Статические** RRO (`com.deepal.translate.rro.*`): кладутся в `/vendor/overlay/`, активны с загрузки |
| `deepl` / `deepl.exe` | Менеджер RRO. Ставит **обе схемы** — у каждой своё меню: `./deepl` — динамические, `./deepl stat` — статические. Выбор APK внутри обоих меню одинаковый |
| `shot` / `shot.exe` | Снимок logcat + охота за runtime-фразами (не те, что в APK): `-q "фраза"`, `-cjk`, `-offline shot_*.log` |
| `targets.txt` | Список приложений-целей для `deepl` (**не удалять** — без него `deepl` не стартует) |

## Установка — 3 шага

1. Подключите ГУ по USB и включите ADB (инженерное меню ГУ).
   Проверьте: `adb devices` → `device`. Если `unauthorized` — добавьте
   ключ этого ПК на ГУ приложением `adbauth` (USB-флешка, «Добавить
   ADB-ключ с USB»). Меню `deepl` не видит ГУ → пункт `[R] Проверить ADB заново`.
2. Запустите `deepl` (Windows — `deepl.exe`) **из этой папки**:
   - Динамические (обычный путь): `[1] Установить + включить` → цель:
     `8` — TOP-8 (быстрый чек), `A` — всё, `[L]` — поштучно по номерам.
   - Статические (нужен root): `./deepl stat` → `[1] Установить` → после
     установки — перезагрузка (`[6]` или `adb reboot`).
3. Готово. RU появляется после перезапуска приложений (закрыть из «недавних»)
   или reboot.

**Чем динамические отличаются от статических:**

| | Динамические (`apks_rro_min`) | Статические (`apks_rro_static`) |
|---|---|---|
| Куда | `/data/app` (обычная установка) | `/vendor/overlay` (root+remount) |
| Вкл/выкл | да (`[2]`/`[3]` в меню) | нет — всегда активны с загрузки |
| Снятие | `[3]`/`[4]` сразу | удаление `[2]` + reboot |
| Сколько ставится | 91 из 100 (9 AOSP-пакетов не ставятся `adb install`) | 100 |
| Переживает сдвиг `/data` | нет | да |

## Как вернуть всё как было

- **Динамические:** `[3] Отключить`, `[4] Удалить` (меню `./deepl`).
- **Статические:** `./deepl stat` → `[2] Удалить` + reboot.
- **Локаль ГУ:** при установке перевод выставлял `system_locales =
  ru-RU,en-US,zh-CN`. Пункт меню **`[9] Восстановить оригинальную локаль`**
  возвращает `zh-CN` (как из коробки). Оверлеи при этом **не** удаляются —
  для них пункты `[3]`/`[4]`/`[2]`.

## Небольшие (краткая справка)

| | Команда |
|---|---|
| Весь dyn (install+enable) | `./deepl dyn install A` |
| Весь stat (→ /vendor/overlay) | `./deepl stat install auto` |
| Снять всё stat | `./deepl stat uninstall auto` |
| Статус | `./deepl dyn status` / `[5]` в меню |
| Локаль в zh-CN | `./deepl dyn locale-restore` / `[9]` |
| Report (zip) | `./deepl report dyn` (или `stat`) / `[7]` в меню |

Цели (presets) в CLI: `1|2|3|4` (группы), `8` (TOP-8), `A` (все группы),
`C` (группы 2+3), `auto` (все APK каталога схемы), либо имена пакетов
через пробел: `./deepl dyn install Camera WT_NewLauncher`.

**Ручная установка (adb, без deepl):**

```bash
# динамические:
adb shell settings put system system_locales ru-RU,en-US,zh-CN
for f in apks_rro_min/*_RRO.apk; do
  app=$(basename "$f" _RRO.apk | tr '[:upper:]' '[:lower:]')
  adb install "$f"
  adb shell cmd overlay enable --user 0 com.android.vendor.translate.rro.$app
done

# статические (нужен root+remount; на части прошивок remount запрещён (verity)):
adb root && adb remount
for f in apks_rro_static/*_RRO.apk; do
  app=$(basename "$f" _RRO.apk | tr '[:upper:]' '[:lower:]')
  adb shell mkdir -p "/vendor/overlay/com.deepal.translate.rro.$app"
  adb push "$f" "/vendor/overlay/com.deepal.translate.rro.$app/"
done
adb reboot
```

## Проверка

- Любое приложение (мультимедиа/центр авто/камера) — по-русски.
- `[5] Статус` в меню: по 100 пакетов «УСТАНОВЛЕН / НЕ» + оверлей `[x]`/`[ ]`.
- `adb shell settings get system system_locales` → `ru-RU,en-US,zh-CN`.
- `[7] Собрать логи` → `logs/deepl_<scheme>_report_<TS>.zip` (внутри
  `summary.txt` — читать первым).

## Если что-то не работает

| Симптом | Что делать |
|---|---|
| ADB «не найдено» / `unauthorized` | `[R]` в меню; кабель/ADB/ключ: `adbauth` на ГУ (adbkey.pub с флешки); `adb.exe` — в PATH, рядом с `deepl` или `DEEPL_ADB=/путь` |
| Пакет установлен, но китайский | `[3]` → снова `[1]` (или reboot); `[5]` — оверлей должен быть `[x]` |
| Оверлей `---` (ошибка) | `[6] Диагностика`, `[7] Report`, `enable` ещё раз |
| Статика: remount не прошёл | только динамический вариант |
| RU не во всём (например, детали «Умного обслуживания») | данные с сервера, не ресурсы — RRO не покрывает |
| Перевести фразу, которой нет в APK (runtime) | `shot -cjk -d 180` (показать сценарий на ГУ), передать фразу переводчику |

## Примечания

- Некоторые процессы увидят RU только после собственного перезапуска
  (закрыть из «недавних») либо reboot.
- Старые `manage.bat`/`manage_static.bat` в релиз больше не входят —
  весь их функционал в `deepl` (включая `[9]`-локаль).
