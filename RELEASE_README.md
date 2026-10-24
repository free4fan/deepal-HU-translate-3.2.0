# deepal-HU-translate v3.2.0

Перевод ГУ **Deepal / Changan S05** (прошивка 3.2.0) с китайского на русский:
RRO-оверлеи ресурсов + Go-инструменты.

## Состав

| Файл | Что |
|---|---|
| `apks_rro_min/` — 100 APK (+ `.idsig`) | **Динамические** RRO (пакеты `com.android.vendor.translate.rro.*`): ставятся в `/data/app`, включаются/отключаются через `cmd overlay` — без root-раздела |
| `apks_rro_static/` — 100 APK (+ `.idsig`) | **Статические** RRO (пакеты `com.deepal.translate.rro.*`): ложатся в `/vendor/overlay/`, активны с загрузки, сменных |
| `deepl` / `deepl.exe` | Go: **единый менеджер RRO** (заменяет manage.bat). Ставит **обе схемы** — каждое со своим меню: `./deepl` — динамические, `./deepl stat` — статические. Выбор APK внутри обоих меню одинаковый: группы 1–4, TOP-8, все группы, CORE+IMPORTANT, `auto` (все из каталога), `[L]` выбор конкретных пакетов по номерам. См. §Go-тулзы |
| `shot` / `shot.exe` | Go: снимок живого logcat (main/system/crash) + охота за runtime-фразами (не находятся в APK: scene.db, TTS, ASR-правила). `-q` — конкретная фраза, `-cjk` — все CJK-фрагменты, `-offline` — повторный разбор снимка |
| `targets.txt` | Список целевых приложений и групп **для deepl**: без него `deepl` не стартует. Изменяемый — под другую прошивку/набор APK достаточно отредактировать файл (списков в самом бинарнике нет) |

## Предварительно (для обоих методов)

PC с `adb` (Android platform-tools) в PATH; ГУ подключено USB (или adb-over_TCP);
отладка на ГУ включена.

```bash
adb root
# если «Отказано» — в настройках ГУ разрешить «Отладка по USB» в root-режиме
# (Developer options → USB debugging (Security settings))

# ru в НАЧАЛЕ списка системных локалей: OEM-приложения проверяют текущую
# локаль; если начать ставить до этого — часть строк не переключится.
adb shell settings put system system_locales ru-RU,zh-CN,en-US
```

## Способ 1 — динамические RRO (`apks_rro_min/`)

Обратимо: ставить/отключать без входа в /vendor.

```bash
# один пакет:
apk=apks_rro_min/Fota_RRO.apk
adb install "$apk"
adb shell cmd overlay enable --user 0 com.android.vendor.translate.rro.fota

# все разом (package = префикс + нижний регистр имени, underscore оставляется):
for f in apks_rro_min/*_RRO.apk; do
  app=$(basename "$f" _RRO.apk | tr '[:upper:]' '[:lower:]')
  adb install "$f" >/dev/null
  adb shell cmd overlay enable --user 0 com.android.vendor.translate.rro.$app
done
```

> Удобнее через менеджер: `./deepl dyn install auto` (см. ниже,
> один прогон = установка+enable+статус по всем группам).

Особенности:
- `cmd overlay enable` нужен от root (`adb root`); если выдаёт
  «UID2000 is not allowed» — повторить `adb root` и повторить команду.
- Если строка не переключилась сразу, а приложение уже работало —
  убить процесс (`adb shell am force-stop <пакет-таргета>`) или ребут.
- Снятие: `adb shell pm uninstall com.android.vendor.translate.rro.<app>`
  (или `./deepl dyn uninstall auto`). Список установленных:
  `adb shell pm list packages | grep translate.rro`.

## Способ 2 — статические RRO (`apks_rro_static/`)

Активны с загрузки, отключаться не деградируют.

Требуется запись в `/vendor` (обычно доступно после `adb root && adb remount`;
на части прошивок remount не разрешён — тогда есть только способ 1):

```bash
adb root && adb remount
for f in apks_rro_static/*_RRO.apk; do
  app=$(basename "$f" _RRO.apk | tr '[:upper:]' '[:lower:]')
  adb shell mkdir -p "/vendor/overlay/com.deepal.translate.rro.$app"
  adb push "$f" "/vendor/overlay/com.deepal.translate.rro.$app/"
done
adb reboot
```

> Через менеджер удобнее: `./deepl stat` — меню установки статики (те же
> варианты выбора APK, что и в `./deepl`: группы, `[L]` по номерам, `auto`),
> делает root+remount, mkdir и push сам.

Особенности:
- после установки нужен **reboot** (оверлеи `/vendor/overlay` читаются при boot);
- снятие: `adb shell rm -rf /vendor/overlay/<pkg>` (или
  `./deepl stat uninstall auto`) + reboot;
- если `adb remount` не прошёл (verity): динамический способ — единственный.

## Проверка

```bash
adb shell cmd overlay listenabled | grep -c translate   # сколько включено (dyn)
# список /vendor/overlay (static):
adb shell ls /vendor/overlay | grep deepal
# строки оверлея (вытянули из APK — сравните с экраном ГУ):
aapt2 dump resources apks_rro_min/Fota_RRO.apk | grep -m3 '()"'
# на ГУ: открыть экран приложения — строки должны быть по-русски
# (ru-значение видно в settings system_locales: adb shell settings get system system_locales)
```

## Go-тулзы

### deepl — менеджер RRO (динамические + статические)

Единая замена `manage.bat`/`manage_static.bat`/`collect_report.bat`.
**Обе схемы ставятся из этого же приложения — у каждой своё меню**,
которое открывается аргументом запуска. Выбор APK внутри **обоих** меню —
одна и та же цель (группы + `[L]`/`auto`).

- **Динамические** — `./deepl` (или `./deepl dyn`). Берут
  `apks_rro_min/*.apk`, установка = `adb install` + `cmd overlay enable`,
  обратимо (есть enable/disable).
- **Статические** — `./deepl stat`. Берут `apks_rro_static/*.apk`,
  установка = root+remount → `adb push` в `/vendor/overlay`, активны с
  загрузки. enable/disable отсутствуют (оверлей «всегда включён» после
  reboot; выключение = удаление).

```bash
# Интерактивные меню (после выбора действия — цель 1/2/3/4/8/A/C/auto/L):
./deepl                      # МЕНЮ динамических  (установить+включить / enable / disable / удалить / status / diag / report / reboot)
./deepl stat                 # МЕНЮ статических    (установить / удалить / status / diag / report / reboot)

# То же самое без меню (CLI). Пресеты: 1/2/3/4, 8 (TOP-8), A (все группы),
# C (2+3), auto (все *_RRO.apk из каталога схемы), либо имена пакетов:
./deepl dyn install auto     # динам.: установка+enable всего из apks_rro_min
./deepl stat install auto    # статические: root+remount → push всего из apks_rro_static
./deepl dyn status           # состояние
./deepl stat uninstall auto  # статические: удалить всё из /vendor/overlay
./deepl report dyn           # zip-отчёт (dyn)
./deepl report stat          # zip-отчёт (stat)
```

**Выбор APK (общий для dyn и stat, внутри действия):** после выбора
действия меню показывает цель —

```
[1] CRITICAL     [2] CORE UI        [3] IMPORTANT APPS
[4] SECONDARY    [8] TOP-8
[A] Все группы   [C] CORE+IMPORTANT (2+3)
[auto] Все *_RRO.apk из каталога схемы (apks_rro_min / apks_rro_static)
[L] Пакеты — ручной выбор по номерам из списка (5 или 5,12 18)
```

т.е. можно ставить и **всю схему, и отдельные APK — в обе схемы одинаково**.
Конкретные пакеты в CLI — по именам: `./deepl dyn install Fota WT_Link`.

Бинарники static (без зависимостей): Linux x86-64 — `deepl`, Windows x86-64 — `deepl.exe`.
Работает из папки, где лежит `targets.txt` (или задайте `DEEPL_TARGETS=/путь`).

### shot — охота за runtime-фразами

Применяется, когда фраза, которую надо перевести/найти, **не находится в APK**
(исходники проверяем по `res/`/`resources.arsc`/`assets`/`dex`/`.so`): она
приходит runtime — сцены (scene.db), TTS-ответы, ASR-правила, шина (ADAS).

```bash
./shot -cjk -d 180                  # 180 с: показать сценарий на ГУ; снять все CJK-фрагменты
./shot -q "请检查四周情况" -q "即将执行" -d 120   # конкретные фразы + контекст ±3 строки + pid→app
./shot -offline logs/logshot/shot_<ts>.log -cjk    # повторный разбор старого снимка
```

Результат — в `logs/logshot/`: `shot_<ts>.log` (весь снимок),
`shot_<ts>.meta.txt` (окружение: locale, pids камеры/сцен),
`shot_<ts>.hits.txt` (отчёт: совпадения + частотный CJK-фрагмент-отчёт + PID-карты).

## Примечания

- В обоих схемах перевод только ресурсов (values-ru); layout-литералы
  встроенные в XML прошивки оверлеем не покрываются (проектное ограничение).
- 8 длинних строк (условия/соглашения) превышают aapt2-лимит 32 700 байт
  UTF-8 — они НЕ входят в оверлеи (на экране — исходный текст); остальные
  18800 строк — в оверлеях.
- Платформенный ключ подписи — стандартный AOSP public key (никаких секретов).
