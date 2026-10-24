# deepal-HU-translate v3.2.0

Перевод ГУ **Deepal / Changan S05** (прошивка 3.2.0) с китайского на русский:
RRO-оверлеи ресурсов + Go-инструменты.

## Состав

| Файл | Что |
|---|---|
| `apks_rro_min/` — 100 APK (+ `.idsig`) | **Динамические** RRO (пакеты `com.android.vendor.translate.rro.*`): ставятся в `/data/app`, включаются/отключаются через `cmd overlay` — без root-раздела |
| `apks_rro_static/` — 100 APK (+ `.idsig`) | **Статические** RRO (пакеты `com.deepal.translate.rro.*`): ложатся в `/vendor/overlay/`, активны с загрузки, сменных |
| `deepl` / `deepl.exe` | Go: **единый менеджер RRO** (заменяет manage.bat): установка/включение/выключение/снятие/статус/отчёт для **обоих** схем — `dyn` и `stat` (root+remount, `/vendor/overlay`). См. §Go-тулзы |
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

# все разом:
for f in apks_rro_min/*_RRO.apk; do
  app=$(basename "$f" _RRO.apk | tr '[:upper:]' '[:lower:]' | tr '_' '.')
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
  (или `./deepl dyn uninstall all`). Список установленных:
  `adb shell pm list packages | grep translate.rro`.

## Способ 2 — статические RRO (`apks_rro_static/`)

Активны с загрузки, отключаться не деградируют.

Требуется запись в `/vendor` (обычно доступно после `adb root && adb remount`;
на части прошивок remount не разрешён — тогда есть только способ 1):

```bash
adb root && adb remount
for f in apks_rro_static/*_RRO.apk; do
  pkg="com.deepal.translate.rro.$(basename "$f" _RRO.apk | tr '[:upper:]' '[:lower:]' | tr '_' '.')"
  adb shell mkdir -p "/vendor/overlay/$pkg"
  adb push "$f" "/vendor/overlay/$pkg/"
done
adb reboot
```

> Через менеджер: `./deepl stat install all` (делает root+remount,
> mkdir и push сам).

Особенности:
- после установки нужен **reboot** (оверлеи `/vendor/overlay` читаются при boot);
- снятие: `adb shell rm -rf /vendor/overlay/<pkg>` (или
  `./deepl stat uninstall all`) + reboot;
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
Интерактивное меню — просто `./deepl` (динамические) или `./deepl stat`.

```bash
./deepl                      # меню — динамические (группы 1–4; install+enable)
./deepl stat                 # меню — статические (группы 1–5; install/uninstall по /vendor/overlay)
./deepl dyn install auto     # динам.: установка+enable всей схемы (CLI, без меню)
./deepl dyn status           # состояние (какие включены/выключены)
./deepl dyn report           # zip-отчёт: pm list, overlay states, locale, logcat
./deepl stat install all     # статические: root+remount → /vendor/overlay (все группы)
./deepl stat uninstall all   # статические: удалить все из /vendor/overlay
./deepl report dyn           # zip-отчёт по схеме dyn
```

Группы (presets): `1|2|3|4` (dyn) / `1..5` (stat), `8` = TOP-8,
`A`/`C`/`auto` = наборы, либо имена пакетов через пробел.

Бинарники static (без зависимостей): Linux x86-64 — `deepl`, Windows x86-64 — `deepl.exe`.

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
