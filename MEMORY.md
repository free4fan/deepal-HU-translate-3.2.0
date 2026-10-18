# Deepal HU Translate — рабочий контекст проекта

Оперативный статус. История — в `CHANGELOG.md`,
шаги — в `WORKFLOW.md`.

## ЯКОРЬ (04.10b) — Темки: RRO на `com.autopai.theme.*` = СЛОМАННЫЙ ПЕРЕКЛЮЧАТЕЛЬ ТЕМ — 2 пакета ВЫВЕДЕНЫ из RRO (100+100 APK)

**СИМПТОМ (live, пользователь):** поставили 2 APK (`com.android.vendor.
translate.rro.wt_themeresources{holder,theme}`, target
`com.autopai.theme.resholder|restheme`, подписаны platform-ключом от 04.10
targetName-фикса) → в WT_VehicleCenter «Дисплей» все 3 кнопки тем (светлая/
тёмная/авто) МОЛЧА некликабельны. Удалили 2 APK → кнопки ожили.

**КОРЕНЬ (по smali, не догадка) — темы переключаются OEM-скинами, НЕ RRO:
1. `WT_TinnoveCoreService` `SkinMallImpl` держит OEM-`IOverlayManager`
   (сервит сам). При init `a9()` берёт `getOverlayInfosForTarget
   ("com.autopai.theme.resholder", USER=-2)` = ВСЁ, что оверлеено resholder,
   и: форсит `setEnabled(restheme/rescarmodel)`; **любой ВКЛЮЧЁННЫЙ оверлей
   списка (кроме restheme/carmodel) записывает в `SkinInfo.skinParams
   [overlayAppPackage]` + `Settings.Global.CurrentSkinInfo` (JSON
   skinPackageName) = «текущая тема»** (пути SkinMallImpl.smali:1600–1755).
2. `DialogDisplayMode` (клики всех 3 кнопок lambda$2/3/4) сначала:
   `ThemManager.isDayNightTheme()` = `WTSkinManager.getOverLayAppPkg()
   == "com.autopai.theme.resholder"`. false → log «当前处于AI主题,
   不支持白天黑夜切换» + `return` (молча, без тоста). Наш RRO в пуле →
   overlayAppPackage = наш package → mёртвые кнопки.
3. Рикошет 2: `WTSkinManager.updateResources()` =
   `getResourcesForApplication("com.autopai.theme.resholder")` + catch →
   `SkinCompatResourcesPlatform.reset()` — при подставке RRO скин-слой
   дополнительно сбрасывался (Resources для системных темок под user-0 RRO
   не резолвятся).
4. `switchToSkin` сверху — отказы «same theme / Too frequent / apk uninstall»
   (`V8()` = `getPackageInfo(skinPkg).versionName` пуст).

**ПРИЧИНА ЧТО НЕ EXCLUDE9:** `manage_static.bat:67` =
`GROUP1=!GROUP1! !EXCLUDE9!` — EXCLUDE9 dynamic-исключает, но static-
ВКЛЮЧАЕТ (в `/vendor/overlay`). RRO на temки ломает ОБОИХ схемы одинаково
(скин-сервис смотрит оверлеи по target, не по схеме). → НОВОЕ понятие
**`NO_OVERLAY_APPS`** = «НЕ СОБИРАТЬ ОВЕРЛЕЙ ВООБЩЕ» (в отличии от
exclude.json — «строки-ключи, но оверлей собирать»).

**РЕШЕНИЕ (04.10b, утверждено):**
- `targets.txt` (корень + копия `go/internal/groups/targets.txt`): из GROUP2
  вынесены `WT_ThemeResourcesHolder/Theme` → комментарий (102→100 приложений,
  93→91 adb). **Go-тест `TestRootFileData` вернулся зелёным (expected 91)** —
  был красный с 3.2.0 (тест писался в 3.1.2).
- `generate_overlays.py` + `generate_overlays_static.py`: константа
  `NO_OVERLAY_APPS = {app: причина}` — main() skip + `cleanup_no_overlay()`
  (rmtree stale `overlays*/<app>`: `create_rro_{min,static}.py` собирает ВСЁ,
  что имеет AndroidManifest.xml — БЕЗ сего guard пересборка «возвращала»
  темы). Вывод строки `[NO_OVERLAY]`.
- Удалены: `overlays{,_static}/WT_ThemeResources{Holder,Theme}/`,
  `apks_rro_{min,static}/WT_ThemeResources*_RRO.apk{,.idsig}` (8 файлов) —
  иначе `auto`-режим (glob `*_RRO.apk`) ставил бы их вне групп.
- `translations/WT_ThemeResources{Holder,Theme}.json` **остались** как данные
  (13 строк каждая; у всех хост-приложений те же ID есть локально, уже в
  их RRO — перевод не теряется; пригодятся для будущего смали-репака).

**СБОРКА:** generate ×2 → 100 + 2 no-overlay; **APK 100+100** (было 102+102);
`validate.py` full = 0 ОШИБОК / 9 предупреждений (как были: 8 aapt2-limit +
1 width); CJK-аудит 1d «потерь нет»; `go test ./internal/groups` OK.

**LIVE-ПОДТВЕРЖДЕНИЕ (04.10, logshot):** 4 снимка после установки фикса
`logs/logshot/shot_20261004_{213142,222020,222214,222305}.log` — во всех
`isDayNightTheme=true`, `getOverLayAppPkg pkg=com.autopai.theme.resholder`,
`overlayAppPackage=com.autopai.theme.resholder` (CurrentSkinInfo), ни одного
`translate.rro` в logcat (0), ни одного `switchToSkin`/`updateResource
Exception` → переключатель тем здоров, кнопки кликаются (пользователь:
«после ребута кнопки работают»). Детали — `logs/logshot/ANALYSIS_20261004.md`.
В снимках также: vendor-FATAL `com.tinnove.wecarspeechtools`
(`NumberFormatException : ",03"`, FileSizeUtil.java:3/LogSaveUtils — локаль
чисел, НЕ наш, растёт 2→4/день). Найденный bug logshot (meta): `adb.Shell()`
бил `adb shell sh -lc <cmd>` 4-мя аргументами → adb склизал их без
перекавычивания → device-shell: `sh -lc getprop` (скрипт = одно слово) =
полный дамп пропсов → в `.meta.txt` битые locale/camera_pid/camera_apk/
scenemode_pid + молчала online-атрибуция pids (`hunt.AttrPID`).
**ПОЧИНЕНО (04.10):** `Shell()` = `adb shell <cmd>` (один аргумент),
регрессия-тест `TestShellPassesCommandAsSingleArg`, бинарники пересобраны.

**ПРАВИЛО НА БУДУЩЕЕ:** при появлении НОВОГО приложения, которое является
SKIN TARGET'ом (`com.autopai.theme.*`, или иное, к-е `getOverlayInfosForTarget`
скин-менеджера сканирует) — НЕ ставить RRO без проверки: grep
`getOverlayInfosForTarget` в decompiled/WT_TinnoveCoreService → если target
в списке → app в `NO_OVERLAY_APPS`.

## ЯКОРЬ (04.10) — LIVE-ЛОКАЛЬ: `ru` обяз. в начале system_locales; зеркало RU в `values-zh-rCN` для ВСЕХ; targetName для 2 темок

**Симптом (отчёт 10-03 150230):** (а) 2 пакета НЕ встали
(`wt_themeresourcesholder/theme` — cert-mismatch: targets
`com.autopai.theme.*` = редкий 3-й ключ `CN=wt_xiaoxia` 97716c62, не platform),
(б) главное меню WT_VehicleCenter по-китайски при оверлее `[x]` и строках
в RRO на canonical-ID.

**Причины:**
1. **Cert-mismatch**: AOSP 11 PMS скан non-preloaded RRO: нет
   `android:targetName` + sig(оверлей)≠sig(target) →
   `INSTALL_FAILED_INTERNAL_ERROR`. Фикс: map `CERT_MISMATCH_TARGET_NAME`
   в `generate_overlays.py` добавляет `targetName`; OMS/idmap — legacy-путь
   (enforce=false, таргетом `<overlayable>` не нужен — PMS/OMS/IdmapManager
   из android-11.0.0_r48).
2. **VehicleCenter-меню**: порядок разрешения конфигураций — точные match
   (`values-en/`, `values-zh-rCN/` таргета, там кит.) ВЫШЕ default `values/`.
   `values-ru/` участвует только при `ru` в preferred-локалях.
   Локаль ГУ `en-US,zh-CN` → выигрывал `values-en`(кит.).
   **Live-фикс:** `settings put system system_locales ru-RU,en-US,zh-CN`.

**РЕШЕНО (04.10):**
- `manage.bat` → блок `:EnsureRuLocale` перед install/enable: `settings get` →
  если нет `ru` впереди — `settings put ru-RU,<старое>` (flat temp + for /f
  как в `:DoOpAdb`; `[LOCALE]` в ops-лог).
- `generate_overlays{,_static}.py`: **зеркало RU в `values-zh-rCN/` для ВСЕХ
  приложений** (было ZH_MIRROR_APPS только WT_AirConditioner). Теперь каждый
  оверлей несёт RU в трёх конфиг-папках: values-ru / values / values-zh-rCN.
  zh-CN-пользователь получает RU даже без locale-прачки; `en-US` всё равно
  лечится только через `ru` в начале списка (`values-ru` точное совпадение).
- Пересборка 102+102 (0 FAIL), `validate.py` 0 ошибок.

**Проверка (на следующем отчёте ГУ):** `ОТСУТСТВУЮТ: 0` (было 2),
VehicleCenter-меню RU, строки `[LOCALE]` в ops-логе.

## ЯКОРЬ (01.10) — 3.2.0 финиш: 37 правок + LLM-`--defective` (3), пересборка 102+102, НАЙДЕН/ВОССТАНОВЛЕН `exclude.json`

**Состояние:** 18 808 zh-записей (18 728 CJK) — 100% ru, 102/102 приложений,
RRO 102+102 (3638 KB), `validate.py` 0 ошибок/9 пред., self-test 90/90,
fit/styled-stuck пустые. Бэкап-снимок `translations_bak/` от 12:32 —
до правок. Детали: CHANGELOG [2026-10-01].

**Правки дня (37 строк / 13 приложений):** 34 точечные (12:33–12:34, поиск
+ nano по живым снапшотам ГУ; ядро — 18 строк WT_VehicleCenter: `app_name`
«Автомобиль», `epb` «ручник», `widget_hud_switch` «Экран AR-HUD», voice_*
подсказки; ×3 `srl_component_falsify` — живой `\n`→`\\n`) + 3 LLM
(`improve_translations.py --defective`, log 12:37–12:39 «принято 3»):
`AdayoDvrLocalService/dvr_permission_tip_text` (LONG 6407 симв., первая
попытка 12:37:42 — битый JSON, повтор 243s),
`WT_VehicleCenter/Exterior_voice_interaction_continuous_description`,
`WT_VisualizationService/osd_ringtone_volume` (единственный новый id в
progress: 774→775 — dvr-tip был уже в done). Точечные правки прогресс НЕ
пишут — сверять по diff vs `translations_bak/`, не по progress.

**БАГ ДНЯ (важно): `translations/exclude.json` выпал при переносе
3.1.2→3.2.0** (`load_excludes()` молча `{}`) → 10 строк-ключей
(8× WT_AutoMaintenance `dialog_part_*_title_text` + 2× WT_HDCloudCamera
`setting_guardian_mode`/`cruise_protect_model`) ушли в оверлеи 13:00-сборки
→ возврат «Осталось - - км» в «Умном обслуживании» (см. 25.09).
Найдено: grep ключей в `overlays/*/res/values-ru/strings.xml`. Починка:
`cp` из `deepal-HU-translate/translations/exclude.json` → regen + rebuild
(`[EXCL]` 8+2 в выводе generate_overlays*) → `aapt2 dump resources`:
ключи 0 совпадений. **ПРАВИЛО:** при переносе/бэкапе проекта проверять
`ls translations/`: `exclude.json` + `improve*.json` — критичные данные
(не только `*.json` приложений).

**Не переведено (по решению, НЕ дефект):** non-CJK 5/85 (записи без ru
с латиницей-иероглифами в zh — нет CJK, improve не забирает); 8 строк
> aapt2-лимит (43–70 KB) — в оверлей не влезут (текст источника);
5 строк у fit-cap (24–31w) — переширокие, но у cap (см. 19.09 +
`logs/fit_report_new.txt`).

## ЯКОРЬ (25.09e) — Виджеты шторки: RU-лейблы переносились на 2–3 строки и съезжали влево — РЕШЕНО (пересборка APK, LIVE-чека нет)

**СИМПТОМ (пользователь)**: при свайпе шторки сверху русские подписи
виджетов «не влазят» в иконки, перевод занимает 2–3 строки, «приклеен
к левому краю». Пример: `widget_seat_memory_drive` «Позиция водителя»
[驾驶位置] в `WT_VehicleCenter/res/layout/seat_switch_widget.xml`.

**КАК УСТРОЕНО (важно для будущих правок этого класса)**: шторка/виджеты
= layout-контейнеры `205px`-боксы (FrameLayout/LinearLayout gravity=center
или 183dp-квадраты в 2×2 `*switch_widget.xml`), внутри: иконка (Lottie/
ImageView 100px) + `TextView` `wrap_content` @28px
(`style=@style/WTTextStyleCaption1` = `wt_text_size_caption1=28.0px`,
НЕ 28sp! density экрана ≈4.21 — см. `sp28` dimen = 6.65dp). ЗH-оригинал
(驾驶位置, 4 CJK-знака ≈ 108px) влезал в 1 строку; RU 2×-3× шире
(Позиция водителя = 244px) → жадный wrap на 2–3 строки.
**«Приклеено к левому краю» = артефакт wrap**: wrap_content-TextView
растёт в ШИРИНУ до контейнера (киская граница), строки внутри
выравниваются по левому краю TextView = визуально текст у левго края,
причём 2-я строка сдвинута — «не по центру». gravity="center" контейнера
центрирует только БЛОК текстa целиком. RRO layout не меняет
(доказано, 22.09) → лечится ТОЛЬКО укорочением строк до zh-длины.

**ФИКС (25.09)**: 22 строки WT_VehicleCenter + 6 строк WT_WtSystemUI
(QS-плитки шторки: `qs_widget_*_btn`, `qs_screen_off`,
`btn_text_copilot_qs_*`) укорочены в `translations/*.json` до
<= zh-ширины (всё <= 110px @28px против рамки 183–205px):
Водитель/Резерв/Отдых/Ещё (seat memory), Выключено/Авт. фары/Ближний/
Габариты (light), Удержание, Автояркость, Разрядка, Авар. режим,
Спуск, Настр. AR-HUD, Замок слева/справа, Сигнал низк. скор.,
Зад. ремни, Охрана, Поворот, Зарядка, Подсветка,
stop_up/stop_down = «Остановить» (боковая кнопка 120×40px в
widget_back_door/sun_roof, gravity=center), SystemUI: Крышка бака,
Выкл. экрана, Охлаждение, Зарядка, Не вкл.
Проверка изоляции (ПРАВИЛО для таких правок): `grep -rl '@string/NAME'
decompiled/<app>/res/` — строка должна сидеть ТОЛЬКО в виджетовом
layout (ambient_lighting: фрагмент использует `ambient_lighting_switch_off`
— другая строка); в smali — только `R$string.smali` (нет сравнения
getString-как-ключа — класс бага 25.09 «умное обслуживание»).

**СБОРКА**: `generate_overlays{,_static}.py` (полные, 100 app) →
`create_rro_{min,static}.py --only <App>` ×2 → `validate.py` 0 ОШИБОК →
aapt2 dump: `()` + `(ru)` = новые значения. APK:
`apks_rro_{min,static}/WT_VehicleCenter_RRO.apk` (336KB) +
`WT_WtSystemUI_RRO.apk` (60KB). Установить через `manage.bat install`
(dynamic) или push в `/vendor/overlay/` (static, root+remount) → reboot →
свайпнуть шторку.

**ЗНАНОЕ ОГРАНИЧЕНИЕ аудита** (`audit_fitboxes.py`): dimen'ы вида `px120`
= px, пересчитаны в условные dp (28.5) → виджетовые рамки 183/205 «px»
читаются аудитором как dp и дают ложные WARN/FAIL по @14.0 default
(стиль wtcl.lib не резолвится — ограничение, задокументировано в хедере
скрипта). Для виджетов сверять РУКАМИ в px (см. расклад выше), не
полагаясь на вердикты скрипта по этим файлам.

## ЯКОРЬ (25.09) — RRO для SystemUI: enable требует ROOT (РЕШЕНО + LIVE-проверено)

**СИМПТОМ**: `manage.bat install` — `WT_WtSystemUI_RRO.apk` ставится
(`Success`), но `cmd overlay enable --user 0` падает:
`SecurityException: UID2000 is not allowed to call setEnabled for
com.android.systemui` → STATE_DISABLED, перевод SystemUI не работает.
**КОРЕНЬ (AOSP 11 `OverlayActorEnforcer`, строки стека 1-в-1 совпадают)**:
`setEnabled` разрешён только ROOT_UID/SYSTEM_UID + «акторам» target'а.
Target `com.android.systemui` ОПРЕДЕЛЯЕТ `<overlayable>`:
`decompiled/WT_WtSystemUI/res/values/overlayable.xml` (`car-ui-lib`,
`rotary-ui`) → акторная ветка: shell (uid 2000, без
`CHANGE_OVERLAY_PACKAGES`) не в разрешённых акторах → отказ. Остальные
90 оверлеев включаются: их targets `<overlayable>` НЕ объявляют →
legacy-ветка (`CHANGE_OVERLAY_PACKAGES` — shell на этом ГУ проходит).
«Когда-то работало» = SystemUI шёл по СТАТИКЕ (`/vendor/overlay`,
`isStatic`, авто-enable, без shell enabler); при сводке всего в один
dynamic-поток enable-метка слетела. Префикс пакета
(`com.android.vendor.*` vs `com.deepal.*`) к enable отношения НЕ имеет
(актор — shell, а не пакет оверлея).
**ФИКС (в `manage.bat`, переработка 26.09)**: блок root **ИНЛАЙН в
потоке `:RUN` ДО цикла пакетов** (manage.bat:305-351) — подпрограммы
`:EnsureRoot`/`:Whoami` УДАЛЕНЫ (вложенные `call :x`+`exit /b` хрупки).
Теперь: `call :DoOpAdb root` (один уровень, как рабочая enable-форма) →
`adb wait-for-device` (root рестартит adbd, ждём) → **ВЕСЬ прогон (install
+ enable + disable + uninstall) идёт от root**; флаг `ADB_ROOT_DONE` на
всё окно (перезапуск adbd живёт между прогонами). uid-проверка best-effort
(`adb shell id -u` в temp → `for /f 'type'`); строка **`[ROOT] uid=0` в
ops-логе = переключилось**; её НЕТ = баг (26.09 09:07: live-отчёт —
строки `[ROOT]` отсутствовала, SystemUI снова SecurityException — отсюда
и ревизия). Если root не переключилось — `[WARN]` + явная подсказка
«adb root и повторить manage.bat enable» (в экран И в лог).
GU `ro.debuggable=1`/test-keys → `adb root` работает. **LIVE (25.09)**:
enable от root → `[x]`, **перевод SystemUI заработал**. **LIVE (26.09
21:44, отчёт 214922): `uid=0` + WT_WtSystemUI `OK (установлен и включён)`
— root-путь закрыт насовсем.** Починен баг в моём же блоке root:
незакрытая `)` в echo-строках [ROOT] (экренирована `^(`, а `)` — нет)
рвала if/else → обе ветки писались в ops-лог, строка обрывалась →
выглядело как «не переключился».
**НОВОЕ (26.09): `wt_link` = STATE_NO_IDMAP** — единственный из 91:
установлен И включён (`mIsEnabled: true`), но idmap не строится,
перевод не применяется. Утром 26.09 он был `[x]`, после РЕБУТА +
переустановки — `---`. Статика RRO чистая: 242 ID ⊂ таргета (0 missing),
тип+имя 173/173, подписи RRO=таргет (platform c8a2e9bc), priority 1.
Причина снаружи (idmap2d Slog.w IdmapManager упала из буфера 43 = 2000
строк). В `collect_report.bat` добавлен `raw/46_idmap.txt` (полный
logcat IdmapManager/Idmap) — в следующем отчёте будет прямая причина.

## ЯКОРЬ (24.09d) — RU применяется и при локали ≠ ru (дубль в `values/`)

**СИМПТОМ**: перевод жил только в `values-ru/` → срабатывал строго при
ru-локали. ГУ сидит в `ru-BY,en-US,zh-CN` (10_locale.txt, `persist.sys.locale=en-US`)
→ при zh/en-локали WT-* показывали китайский из default `values/`,
AOSP-* — EN fallback. Перевод «не применялся».
**Решение (ДЕЛАТЬ ТАК ДАЛЬШЕ)**: генераторы пишут RU в ДВЕ папки
(значения идентичны): `res/values-ru/` (ru-локаль) + `res/values/`
(default-конфиг → при любой другой локали берётся RU). Изменено:
`generate_overlays{,_static}.py` (сборка файла 1 раз → 2 записи),
`create_rro_static.py` (компилирует ВСЕ `values*/`, было только `values-ru/`),
`create_rro_min.py` не менялся (уже все `values*/`). Flat-имена не пересекаются
(`values_strings.arsc.flat` ≠ `values-ru_strings.arsc.flat`).
**Состояние**: перегенерация 100+100, rebuild 100+100 = 0 FAIL,
`validate.py` full (aapt2 dump 200) = 0 ОШИБОК; в APK строка в ДВУХ конфигах
`() "…"` + `(ru) "…"` (plurals тоже). README/WORKFLOW/CHANGELOG [2026-09-24d]
обновлены. **Не править `overlays*/res/values*` руками** (генератор затирает).

## ЯКОРЬ (25.09) — «Умное обслуживание» `- -`: РЕШЕНО + LIVE-проверено, РЕШЕНИЕ по названиям = оставить кит.

**Корень (доказан live-А/B + smali):** `MainActivity.smali:R()`/`MaintainUtil.
getMaintainMessage()` делают `getString(id)` и **сравнивают со
`push.getMaintenanceProgram()` с сервера (Всегда КИТАЙСКИМ**): 8 строк
`dialog_part_{jiansuqiyou,zhidongye,kongtiaolvqing,jiyou,kongqilvqing,
lengqueye,lengqueye_title_text2,huohuasai}_title_text` — КЛЮЧИ, не надписи.
RU-значение → сравнение ложно → карточки не заполняются → заглушки
«Осталось - - км». zero/zh-оверлеи → совпадает → цифры.
**Fix:** `translations/exclude.json` {app:{name:причина}} — строки НЕ пишутся
в оверлей (на ГУ = zh). Поддерживается в `generate_overlays{,_static}.py`
(`load_excludes`/`filter_excluded`), в ignore-списки добавлен `exclude.json`
(все читеи transcripts: generate*, validate, improve_translations,
apply_db_translations). WT_AutoMaintenance 269→261, APK пересобраны
(min+static, verify 261/261). `order_edit_time_default_text` — безопасен
(same-getString sentry).
**LIVE-ПОДТВЕРЖДЕНИЕ (25.09):** цифры появились после установки 261-APK —
симптом СНЯТ. ОСТАТОК: названия разделов (空调滤芯/制动液/减速器油) на
ГУ — китайские. **РЕШЕНИЕ (утверждено): ОСТАВЛЯЕМ КАК ЕСТЬ, репак НЕ делать**
— это серверные данные (`maintenanceProgram` из API, `setText(program)`,
ресурса нет → RRO не покрывает); и те же ID `dialog_part_*_title_text` —
placeholder карточек в layout (заодно показываются кит. до загрузки данных).
Порог «русские названия деталей» = только smali-репак (маппинг 8 program→RU
перед setText 6 методов T/L/M/N/P/U) — НЕ ПРИНИМАТЬ: имена деталей = данные
производителя, RRO-путь проекта (без репаков) сохранён. RU-переводы этих
8 строк ЦЕЛЫ в `translations/WT_AutoMaintenance.json` (`ru` заполнено) —
не стирать «лишним» --defective-прогоном (исключены в exclude.json, но
значения нужны как справка/для будущего репака).
**Класс бага для других приложений** (скан 100 апп — см. результат в
`/tmp/opencode/func_keys.txt` сессии 25.09): `getString(I)` →
`Intrinsics.areEqual`/`equals`/`TextUtils.equals`. Инструменты изоляции
(оставить): `make_bisect_overs.py [K][A][B][NAME]`, `make_zh_control.py [N]`
(«все ID, значения цели» — контроль структура-vs-контент).
**Правило A/B на ГУ:** APK того же package ЗАМЕНЯЮТ друг друга при
`adb install` без uninstall — для бисекта: uninstall → install → ЧЕК (или
отдельные package-суффиксы).

### Бонус 25.09 — тот же класс бага вычистили по ВСЕМ 100 приложениям

Скан smali (`getString(I)` → equals/areEqual) по 100 app: **7 прил / 28
строк**. SAFE (self-consistent, не трогать): AdayoLog, Fota,
SettingsProvider, WT_IncallPersonalCenter, WT_InputMethod/ok, WT_Wcenter
(21 строка). **Починены, WT_HDCloudCamera:**
- `setting_guardian_mode` + `cruise_protect_model` — КЛЮЧИ голосовых команд
  (сравнение с `json.optString("Mode")`, внешний zh-источник,
  `SpeechOperateCommand.setGuardMode`) → **в `exclude.json`** (иначе команды
  «режим охраны» молча не срабатывают).
- `str_no_filter` — self-сравнение с `s_lapse_mode[0]` (оба кит. 无滤镜):
  RU разошлись → **выровнены** (`str_no_filter.ru = s_lapse_mode_0.ru =`
  «Без фильтра», в `translations/WT_HDCloudCamera.json`, не в overlay!).
- `str_no_limit` vs `time_items[6]` — УЖЕ совпадает (не трогаем);
  **памятка**: `LapseOperateView$a.c` иначе `parseInt(selected)` → краш —
  при будущих правках держать равным либо числовым.
Пересобраны APK min+static (495 res), `validate.py` 0 ошибок. Формат
`exclude.json`: `{"App": {"name": "причина"}}` — строка НЕ в оверлей, на
ГУ = zh. Правка значений «для согласованности» = только в
`translations/*.json` (источник), НИКОГДА руками в `overlays*/`.

## ЯКОРЬ (24.09d) — «Умное обслуживание» values `- -`: zero-тест ПОБЕДИЛ, бисекция (архив)

- **ФАКТЫ (24.09, HU):** (1) наш полный RRO (269 строк) → «Осталось - - км / дней»,
  цифры не появляются; (2) **`WT_AutoMaintenance_RRO_test_zero.apk`** (0 ресурсов,
  тот же package/target) → **данные ПОЯВЛЯЮТСЯ, UI на китайском** → механизм RRO
  безвреден, виноват **контент/присутствие наших 269 строк**; (3) удаление RRO
  = то же, что zero.
- **logcat zero-сессии** (`logs/logcat_auto.zip` → `logcat_auto.txt`):
  `InCallManager: startMaintainCache` → `mAuthState = ACTIVE` →
  `url=https://incall.changan.com.cn/hu-apigw/evhu/api/queryMaintainMsg?vin=…`
  → `code:200` (3 объекта: 减速器油 100000км/1768дн, 制动液 40000/673,
  空调滤芯 15000/673) → `MainActivity: observe mMaintainMSGDTO = 0` (0 = успех,
  цифры идут в TextView через `getString(0x7f0e00a8/9c, [n])`). Сетевой SDK
  (`com/incall/serversdk`, binder `com.incall.network.NETWORK_SERVICE`) стринг-
  ресурсы пакета НЕ читает.
- **Исключено локально:** ID 269/269 = canonical-ID таргета (slot string 0x0e);
  формат-спецификаторы %s 1:1 (0 mismatch); styled-строк в оверлее 0; логических
  (URL/коды/домены) строк среди 269 нет (все 1:1 UI-тексты, zh→ru); манифесты
  ok; размер на ГУ = локальный файл; `formatted="false"` у %s-строк = как в
  generate_overlays (норм). **Таргет содержит собственный values-ru (29 строк,
  в основном abc_* appcompat)** — при нашем оверлее 21 из них «наши» значения.
- **ИНСТРУМЕНТ** `make_bisect_overs.py [K] [A] [B] [NAME]` → `apks_rro_min/
  WT_AutoMaintenance_RRO_<NAME><i>.apk` — K кусков из [A:B) строк
  (`overlays/WT_AutoMaintenance/res/values-ru/strings.xml`, порядок =
  алфавитный, 269 всего), тот же package `…rro.wt_automaintenance`, ID
  зачищены, verify встроен. **Собрано: t1..t4** (по 67/67/67/68:
  t1 `app_name..dialog_part_zhidongye_text`, t2 `…zhidongye_title_text..
  maintain_health_text`, t3 `maintain_in_sync_text..order_record_navi_bt_text`,
  t4 `order_record_order_again_text..search_menu_title`).
  **t3 = карточка ТО** (maintain_mile_*_text 0x7f0e00a7/a8, day_* 0x7f0e009b/9c
  — в t2!) + диалоги ТО.
- **ПРОТОКОЛ НА ГУ (Windows+adb):** базовая точка = zero (д данные ОК):
  1. `adb uninstall -k com.android.vendor.translate.rro.wt_automaintenance`
     (zero уже стоит) → установить `WT_AutoMaintenance_RRO_t3.apk` (t3 в
     `test_hide\apks_rro_min\`, как и раньше) → reboot → экран ТО:
     **цифры есть?** нет→виновник в t3 (67 строк: `maintain_in_sync_text..
     order_record_navi_bt_text`); да→переходим к t1/t2/t4 по очереди
     (каждый поверх: uninstall старого → install нового → reboot → экран).
  2. ПЛОХОЙ кусок найден → рекурсия: `python3 make_bisect_overs.py 8 A B u1`
     (A..B — индексы строк куска в списке 269) → t→u1..u8 → и т.д. до одной
     строки.
  3. Параллельно в ЛЮБОЙ плохой конфигурации: `adb logcat -c` → открыть экран
     → `adb logcat -d -s wt_maintenance:* InCallManager:* Resources:* >
     logs\logcat_fail.txt` — смотреть `observe mMaintainMSGDTO = N` (N≠0 =
     данные не пришли) + стек-трейсы.
- **ЕСЛИ БИСЕКЦИЯ НЕ НАЙДЁТ ОДНУ СТРОКУ** (все 4 куска по отдельности «хорошие»,
  но в сумме «плохие») → эффект от ОБЪЁМА таблицы ресурсов (relink при 269 vs
  при 67) → решение: WT_AutoMaintenance вынести из RRO (перевод строк
  оставить в `translations/`, но не собирать оверлей), приложение останется
  с внутренними 29 строками values-ru таргета + китайский остальной.
- Не трогать остальные 99 оверлеев (на zero-снимке они стоят все и данные
  работают).

## ЯКОРЬ (24.09) — «ольш» в `Звуковые эффекты`: fix + аудит влезания RU в рамки

- **СИМПТОМ ПОЛЬЗОВАТЕЛЯ**: в WT_SmartSoundEffect (рекомендуемые, шапка
  секции) вместо «Больше» было «ольше» — `text_more` (更多, `wrap_content`
  TextView @36sp) внутри LinearLayout 128dp − стрелка 48dp = **80dp на текст**;
  «Больше» = 131px @36 → обрезка справа. **FIX**: RRO, «Больше» → «Ещё»
  (69.5px, 87%): `translations/WT_SmartSoundEffect.json` → generate_overlays*
  → **оба APK пересобраны** (`apks_rro_{min,static}/WT_SmartSoundEffect_RRO.apk`,
  aapt2: `0x7f0f0145 string/text_more = "Ещё"`, verify resId 369/369 OK).
  `text_more` у WT_ElectronicDirections («Больше» 51px @16) — влезает, не тронуто.
- **НОВЫЙ ИНСТРУМЕНТ** `audit_fitboxes.py` (вызвать:
  `python3 audit_fitboxes.py [app]`) → `logs/fitboxes_report.{txt,json}`:
  проверяет ВСЕ `decompiled/*/res/{layout*,menu}*.xml` TextView/Button/
  EditText с `@string/...`: RU-ширина (PIL + Roboto ГУ из
  `deepal-firmware/extracted/mnt_sys/system/fonts/Roboto*.ttf`, size из
  attr/@dimen/style, bold/ls/lse), свой/родительский dp-бюджет, word-wrap,
  multi-line `\n` (literal `\n` в JSON = `unesc()`), 0dp+weight, hLL-соседи,
  scroll-предки. Вердикты: FAIL (слово/линия > рамка, ИЛИ строк RU > вмещает
  СВОЯ фикс. высота), CLIP (maxLines=1/ellipsize), WARN (впритык >92% /
  RU-линий > ZH-линий влезая). Итог: **3374 строк / 70 appl: FAIL 132
  (17 appl), WARN 139, CLIP 33**. «Класс …ольш» (слово > контейнер-предок):
  14 строк — WT_VehicleCenter×7, WT_CarLink×2, WT_Launcher×2,
  WT_FusionNavigation×3 (пометка в JSON `why`: «…ольш»). Лечить —
  укорочением перевода (RRO не меняет layout): по списку FAIL в отчете.
  Ограничения: %s-аргументы = нижняя оценка; стили внешних lib → 14sp default;
  кастомные виджеты (WTButton и др. наследники) вне скоупа; 0dp-constraint
  = верхняя оценка предком.
- **Дальнейшие правки коротких строк**: править `translations/<app>.json`
  вручную (точечно) → `generate_overlays.py` + `generate_overlays_static.py`
  → `create_rro_{min,static}.py --only <App>` (собирает ВСЕ остальные? НЕТ:
  `--only` = только приложение; без `--only` = все 100) → `validate.py --app`.
  Не править `overlays*/res/values-ru` руками (генератор затирает).

## ЯКОРЬ (23.09b) — RRO: resId согласованы с таргетами (fix «Осталось - - км»)

Всё время у RRO были СВОИ ID ресурсов (aapt2 link `-I android.jar` →
`type string id=01`, алфавитная перенумерация), а не ID таргета
(`id=0e` у WT_AutoMaintenance). RRO применяется по ID таргета, поэтому
`getString(R.string.maintain_mile_normal_text, [n])` в smali читал чужое
значение → заглушки `Осталось - - км/дн` (см. CHANGELOG [2026-09-23b]).
**Fix** в обоих билдерах (`create_rro_min.py`, `create_rro_static.py`):
`write_resource_ids()` генерирует `res/values/public.xml` с canonical-ID из
`decompiled/<app>/res/values/public.xml` (только ресурсы, реально в
оверлее), post-link `_verify_resids()` сравнивает `aapt2 dump resources`
с таргетом, расхождение = **FAIL**. Пересобрано: 100/100 min + 100/100
static, 0 FAIL/WARN. Дальнейшая сборка — так же (без доп. шагов).
**Не применять** для: smali-литералов (там другие ID, RRO их не задевает).

## ЯКОРЬ (22.09) — ЖИВЫЕ ЛОГИ HU: скрипты починены, остаются 2 реальных дела

Разобраны `logs/bat/install-apk*.log`, `uninstall-apk.log`, diag и
report-zip (см. CHANGELOG [2026-09-22b]). **Скрипты:** false-`[ERROR]`
+ «OK:N / Ошибок:N» — неэкранированные скобки в `RESULT:`-строках
ops-лога (винтик: `if defined OPS_LOG echo RESULT: OK (…) >>` в блоке) —
починено в manage/manage_static + 3 legacy-обёртки; парсер отчёта под
реальный `pm list` = `package:PKG versionCode:N` (пробел, БЕЗ `=`;
было ложное «0/100», теперь 90/10); GROUP3 `WT_PhoneLink`→`PhoneLink`
(файл — `PhoneLink_RRO.apk`, пакет `…rro.phonelink`); ANR-dump — полный
путь `/data/anr/$f`.
**Итерация 2 (отчёт 22.09 21:26, прогон manage.bat install):**
подтверждено, что 22b-чинки работают (91/9, phonelink `[x]`, ver виден).
Починены ВТОРОЙ волной (CHANGELOG [2026-09-23]): потеря ops-логов
(`:OpSTs`: замена ПАРЫ `!X:=_!` → битое имя с `:` → файл не создавался;
теперь wmic/powershell-таймстемп), счётчик FATAL (`find /C` даёт
`---------- N C(S) FOUND`, токен1=дефисы; теперь построчный счётчик как
N_ANR), ANR-trace Permission denied (`anr_*` = system:system 600; `adb
root` ВСЕГДА перед дампом), скрытый `overlay enable` (теперь :DoOpAdb +
retry + `[WARN]` в лог при rc≠0), хрупкий `"%%I"=="Success"` (хвостовой
пробел/CR в for /f → префикс-матч `!L:~0,7!`). ОЖИДАЕМО в summary при
ровно 9 отсутствующих ( больше не «ПРОБЛЕМА» вслепую).
**ОТКРЫТО (решение за пользователем):**  (25.09: ОБА закрыты)
 1. ~~9 dynamic-оверлеев на этой сборке не ставятся `adb install`~~ —
    **РЕШЕНО 25.09: исключены из `manage.bat`** (список `EXCLUDE9`,
    manage.bat:51; вычеркнуты из GROUP1, `auto` их пропускает; A/auto =
    91). Причина не в enable, а в сканировании: чистые AOSP-таргеты
    (targets NetworkStack/MediaProviderLegacy/UserDictionaryProvider/
    DownloadProvider(+)Ui/CompanionDeviceManager/MtpService/
    CaptivePortalLogin/ContactsProvider) подписаны AOSP-ключом ≠ заводской
    + нет `targetName` → `adb install` = INSTALL_FAILED_INTERNAL_ERROR.
    Перевод их строк (если понадобится) — только через
    `manage_static.bat` (`/vendor/overlay`, root+remount; static-APK
    уже в `apks_rro_static/`).
 2. ~~WT_WtSystemUI: установлен, STATE_DISABLED~~ — **РЕШЕНО 25.09**:
    enable требовал ROOT (target com.android.systemui объявляет
    `<overlayable>` car-ui-lib/rotary-ui → AOSP 11 OverlayActorEnforcer
    запрещает shell uid 2000). `manage.bat` теперь делает `adb root` перед
    изменяющими прогонами (`:EnsureRoot`); enable от root → `[x]`,
    **перевод SystemUI заработал**. детали — в якорях 25.09 / CHANGELOG.
Мелочь: vendor-краш `com.tinnove.wecarspeech`
(`NumberFormatException ",11"`, `FileSizeUtil.java:3`, crash-buffer) —
НЕ наш, НО РАСТЁТ: 2 (утренний) → 4 (вечерний) FATAL за день;
отслеживать. ANR от 09-14 — старше установки, trace не достать без
системного root (build test-keys).

## Статус (22.09) — ЗАШИТЫЕ В LAYOUT НАДПИСИ: РАБОЧИЙ СТУЙ (smoke)
> **ОБНОВЛЕНО 25.09:** вариант ОТКЛОНЁН пользователем, все инструменты и
> данные вынесены в `/home/user/projects/deepal-HU-translate-bak-repack/`
> (см. шаг 12 WORKFLOW.md, CHANGELOG [2026-09-25c]). Ниже — история
> собранного пути.

**Симптом «массаж — по-китайски» объяснён** (примеры пользователя
换挡音/座椅按摩/通风加热/空调控制/座椅舒适/车外音): это **3 источника**
(см. CHANGELOG [2026-09-22]): (а) литералы binary-XML (главный, ~1487
уник./56 прил.); (б) данные assets/raw (голосовые хотворды TSpeech,
конфигурация MLWecarControl); (в) обычные resources (уже переведены ранее —
если на ГУ китайский — не установлен оверлей / стоит старый APK).

**СДЕЛАНО 22.09** — полный путь layout-литералов:
- `scan_layout_literals.py` → `logs/layout_literals.json` (122 APK scan):
  **56 apps / 1487 unique / 3761 uses**, 0 parse fail.
- `translations/layout_literals.json` — **1487/1487** (410 existing +
  1077 LLM, CJK=0, `^` и плейсхолдеры 1:1).
- `patch_apk_layouts.py` → **56 APK** в `apks_patched/` (surgical zip:
  `zip -d` + `zip` + `zipalign -f 4`; остальные записи побайто как в
  оригинале). Guard `verify_roundtrip` — структура дерева + только
  «свои» замены в пуле, иначе ABORT.
- `apksigner` (platform.jks, cert = заводской c8a2e9bc…, v3): **56/56 OK**.
- `verify_patched_apks.py` → `logs/apk_patch_verify.json`: **56/56 OK**,
  **cjk_left=0**, aapt2 decode OK (VC 20765 res — как в оригинале),
  package/versionCode/launchableActivity не изменились.
- `install_patched.bat` (data: `adb install -r -d`; system: root
  `pm path` → push → reboot) + `revert_patched.bat` (data: `pm uninstall`;
  system: оригинал из `original_apks/`). **Windows-машине: проверить live**
  (smoke без adb, как в 20.09).

**НЕ покрыто этим путём** (RRO и layout-patch не трогают):
- `WT_TSpeech/assets/{rule-config.json,command-config*.json,public/cfg/*}`
  — голосовые команды-хотворды (换挡音/车外音/空调控制/座椅按摩 как
  команды ассистента);
- `WT_MLWecarControl/res/raw/carconfig_*.json` (документы конфигурации:
  SeatComfortOutInSupportDoc=座椅舒适进出 и т.п.);
- `WT_TinnoveCoreService/res/raw/virtual_data.xml`; `WT_AISpace/assets`
  speech yaml; lottie-JSON (внутренние лейблы, не UI);
- CJK константы в smali: 0 по всем примерам (проверить не нужно).
→ решение: репак этих APK (тоже под platform-ключ) либо отдельный
  «assets-patched» пайплайн; ОТДЕЛЬНОЕ РЕШЕНИЕ (см. открытые задачи).

**Ключевые факсы инструмента:**
- `axml.py` — AXML read/write: byte-exact round-trip **137/137** (StorageWarn
  full set) перед патчем; в UTF-8 pool длина = [1B (<0x80) | 2B (0x80|hi,lo)],
  charLen+byteLen у записи, NUL; attr record = 20B: `ns, name,
  rawValue, size@12, res@14, dataType@15, data@16`.
- RRO layout override **невозможен**: aapt2 `link` из overlay не резолвит
  `@dimen/@drawable/@id/attr` target-пакета (даже 1 `@dimen` = error «not
  found in test.rro.vc») — **НЕ повторять заговор** (проверено 22.09,
  см. CHANGELOG).
- `apktool b` на этих APK **не проходит** (aapt2: `$drawable` invalid name;
  aapt1: `<id>` vs `item`) — поэтому бинарный патч, а не full-декомпиляция.
- Платформ.ключ `keys/platform.jks` = сертификат заводских APK
  (c8a2e9bccf…, v3) — переподпись совместима с in-place (data) обновлением.
- `decompiled/WT_VehicleCenter/unknown/values*/` — **артефакт apktool**
  (сырой `values/` в корне zip, только у WT_VehicleCenter); дубли default,
  рантаймом не читается. НЕ брать за источник (см. 22.09, `values/strings.xml`
  ≠ `res/values/strings.xml`).

## ЯКОРЬ ПРОДОЛЖЕНИЯ (21.09) — «пайплайн с нуля», 5 дыр

Задача: повторный прогон `extract_cjk → improve_translations → validate →
generate_overlays → create_rro_*` из чистого состояния не должен воспроизводить
найдённые баги. План/чекбоксы — в TODO.md блок «V. В РАБОТЕ».
СДЕЛАНО 21.09 (в сессии ~13:30):
- [x] 1 якорь; 2 бэкап 6 файлов (сост. ДО работ 21.09) → /tmp/opencode/bak_pipeline21/;
- [x] 3 extract_cjk.py ГИБРИД: plain прежним raw-regex (zero-drift),
  styled через ET, plurals/arrays через ET, ParseError → regex-fallback.
  **БАГ, НАЙДЕН В ЭТОЙ СЕССИИ**: первая ET-версия дублировала хвост последнего
  тэга (ET.tostring сам печатает c.tail — второй раз руками) И писала `&gt;`
  вместо литерального `>` у 9 WTN (<Data>…&lt;strong>…) — zh уезжал от файла,
  а ru-переводы сверены с файловой формой. Лечится `_string_inner_xml`
  (ручной обход, _xml_esc_min: &/< → &, не '>' ).
- [x] 4 ПЕСОЧНИЦА read-only: 17 832 plain побайтов как в JSON + ровно 13
  новых styled (13/13 побайто совпадают с текущими ru-сверенными json);
  self-close <br/> — обработан (8 синтез-кейсов); CDATA в data нет; nested в
  plurals/arrays нет. **НЕ ЗАПУСКАТЬ extract_cjk.py на живых данных** — main()
  затирает ru=``; и текущие 17 840 уже переведены (нет задач).
- [x] 5 improve_translations.py --styled: токены/fragments/verify/cache
  (механика fix_markup3) — код на месте, СЕТЬ не гоняли (механика проверена
  self-test п.8 синтетикой).
ОСТАЛОСЬ (с первого неотметленного):
- [ ] 6 validate.py: (а) STRING_TOO_LARGE в APK = ОШИБКА (rc=1, список);
  (б) байт-аудит >32700=WARN [Готово]; (в) CJK-ресурсы decompiled ∉ JSON = WARN.
- [ ] 7 create_rro_{min,static}.py: «string too large…» в ВЫВОДЕ aapt2 (STDOUT,
  compile и link, rc=0!) → FAIL приложения (rmtree → None).
- [ ] 8 test_improve_selftest.py: +кейсы (tokenize/cjk_frags pre-post emsp;,
  per-frag verify, fmt_plain_checked/fmt_styled_xml→None при >лимите,
  too-large detect по stdout).
- [ ] 9 верификация: validate полный + rebuild 100+100; md5 APK = базовым
  /tmp/opencode/apk_before_{min,static}.txt; selftest зелёный.
- [ ] 10 DOCS: WORKFLOW.md 5.13 + шпаргалка «с нуля» + предупреждение «extract_cjk
  ОБНУЛЯЕТ ru — не гонять после перевода»; MEMORY.md; CHANGELOG [2026-09-21] +блок.
Решения: лимит байт — только в генераторах; --styled пишет ru даже при
переливе (отсечёт генератор); 6 перелившихся = китайский фолбэк (решение
пользователя); fix_markup2/3.py — эталон механики, удалять не будем;
aapt2-предупреждение: `error: string too large to encode using UTF-8 written
instead as 'STRING_TOO_LARGE'.` (rc=0, в STDOUT).
Опять? → читать этот блок + TODO.md блок V и продолжать с первого
неотметленного [ ].

## Статус (20.09.2026, 23:58)

- Перевод: **17 840 строк** (базовые 17 827 + 13 строк с разметкой, ранее
  пропущенных `extract_cjk.py`; см. ниже), 100/100 приложений, CJK-in-ru: 0.
- APK: **100 dynamic + 100 static, 0 FAIL, 0 STRING_TOO_LARGE** в обоих
  наборах (проверено aapt2 dump по всем 200). `validate.py` (full): 0 ошибок.
  Self-test: 59/59.

### 20.09 — 13 «не переведённых» строк + лимит aapt2 (ВАЖНО)

- **Симптом**: на ГУ нашлись непереведённые фразы. Причина 1: `extract_cjk.py`
  regex `([^<]*)` обрывает на первом `<` → 13 строк с вложенной разметкой
  (`<b>`, `<a>`, `<annotation>`, `<Data>…&lt;br/&gt;…</Data>`) никогда не
  попадали в `translations/*.json`: 9 у WT_FusionNavigation (уступки/политика
  Amap), Fota/upgrade_service_agreement_content, CarService/imsi_protection_
  warning, PackageInstaller/uninstall_application_text_all_users,
  ManagedProvisioning/read_more_delete_profile.
- **Симптом 2 (скрытый, был ДО нас)**: aapt2 молча режет строку во значение
  `STRING_TOO_LARGE`, если её значение > **32767 UTF-8-байт** (проверено:
  32767 OK / 32768 FAIL; plain И span/styled одинаково; это и есть «не
  переведённые фразы» на ГУ). На момент до 20.09 в готовых APK было 2 такие
  строки: `WT_FusionNavigation/road_book_my_agreement_two_content` (33 152
  симв → 61 KB) и `WT_GameCenter/str_procotol` (38 949 симв → 70 KB).
- **Лечение**:
  1. Перевод по фрагментам (`fix_markup2.py`/`fix_markup3.py`, одноразовые;
     разметка сохраняется побайтово, переводим только текстовые фрагменты;
     верификация: токены 1:1, CJK=0). Записи помечены `"styled": true`.
  2. `generate_overlays.py`/`generate_overlays_static.py`: ветка `styled` →
     `fmt_styled_xml` пишет ru VERBATIM без `_esc()` (aapt2 сам парсит спаны;
     `formatted="false"`); лимит `AAPT2_MAX_BYTES=32700` — строка, не
     влезавшая, НЕ пишется в оверлей (на ГУ остаётся исходник, а не
     «STRING_TOO_LARGE»), обычный путь — `fmt_plain_checked` с тем же лимитом.
  3. `improve_translations.is_target()` промахивает `styled` записи (иначе
     `--all` перегенил бы и сломал разметку).
- **Сейчас НЕ влезает в oверлей (6 строк, в APK их нет → на ГУ текст
  источника)**: 4 больших документа WT_FusionNavigation (clause_content 69 KB,
  clause_content1 45 KB, policy_content 44 KB, policy_content1 70 KB — рус.
  перевод ~2x китайского по байтам) + 2 прежних (road_book_my_agreement_two_
  content, WT_GameCenter/str_procotol). Чтобы перевести их в oверлее — нужен
  split на несколько ресурсов (изменения в приложении) — НЕ решено.
  Остальные 7 из 13 переведены и работают (5 styled-строк WTN + Fota +
  CarService + PackageInstaller + ManagedProvisioning).
- Разметка в RU-документах: «голые» тела сущностей (`emsp;`) — остатки
  double-encoded `&amp;emsp;` — переводятся отдельно и подставляются
  побайтово (`pre`/`post` фрагмента), иначе модель добавляла `&` → новый
  тег → рассинхрон каркаса.

### Статус (18.09.2026, 12:43) — ЗАВЕРШЕНО, 100%

- Перевод: **17 827 / 17 827 (100.0%)**, 100/100 приложений. Все прогоны
  (`--all` + `--long`) доведены до конца. Последние 3 длинных юр. текста
  переведены; последняя — через точечный CJK-ремонт (6 фрагментов).
- Прогресс: `translations/improve_progress.json` (**17 747 done** = все).
  `--resume` продолжает / `--fresh` обнуляет. Лог: `logs/improve_translations.log`.
- APK: **100 dynamic + 100 static**, 0 FAIL. `validate.py` (с aapt2 dump):
  **0 ошибок**; self-test improve **42/42**.
- **Длинные строки** (`len(zh) >= API_LONG_THRESHOLD`, по умолч. 200) идут **по
  одной** (батч из 8 с длинной рывал пакет). Режим `--long` = только длинные
  дефектные, обходит progress-фильтр. Guard: дегенеративные ответы
  (`DEGENERATE_ANSWERS`) + `LONG_RATIO_MIN=0.25` для длинных.
- **CJK-ремонт (`_repair_cjk`)**: в длинном переводе, где модель оставила 2–5
  китайских слов, не пол-реген — точечно: окно ±50 симв. вокруг фрагмента →
  модель возвращает окно исправленным → подстановка. Lenient-парсер на
  кривой JSON модели. Полный повтор только как фолбэк. — CHANGELOG
  [2026-09-18b], [2026-09-18c].
- **Удалены (18.09):** исторический путь translate (translate_one/batch,
  api_translate_ambiguity, scan_ambiguities, apply_db_new_ru, revert_cjk,
  run_pipeline.sh) — см. CHANGELOG [2026-09-18]. Остался один путь переводов:
  `improve_translations.py`.
- ДУБАМИ (во время идущего LLM-прогона) НЕ запускать: `create_db.py`,
  `apply_db_translations.py --all` (без dry-run), а также ручное правление
  `translations/*.json` (процесс читал/пишет те же файлы; save атомарный,
  но с внешней перезаписью возможны гонки на строчке). Сейчас прогон не идёт.

## Текущий основной пайплайн

```
improve_translations.py (--all/--defective/--empty, запись в ru; guard: форматтеры
  + порядок, wake-word ***你好***, CJK; hint-retry на битые плейсхолдеры)
  → validate.py (обязательно)
  → generate_overlays.py + create_rro_min.py        (динамические)
  → generate_overlays_static.py + create_rro_static.py  (статические)
  → validate.py (финал, включая aapt2 dump APK)
```

### Ключевые файлы (текущие)

| Файл | Назначение |
|------|-----------|
| `logshot/` (Go, → `shot`/`shot.exe`) | Снимок живого logcat (буферы main,system,crash, host-штамп) + охота: `-q` фраза, `-cjk` ВСЕ китайские фрагменты (токены+частота+pid-атрибуция), `-offline shot_*.log` — по старому снимку. Для runtime-фраз (scene.db/ASR/TTS), которых нет в APK. Снимки/отчёты — `logs/logshot/`; пример анализа: `logs/logshot/ANALYSIS_20261004.md` (04.10: live-подтверждение фикса темок `isDayNightTheme=true`, pkg=resholder; 4 класса CJK-runtime) |
| `improve_translations.py` | LLM-улучшение/перевод → `ru` (режимы см. README; `--fit` — укорочение «раздутых» коротких UI-строк, два лимита: мягкий «только короче» + жёсткий cap в символах `max_chars` в пайлоаде; свой прогресс `improve_fit_progress.json`; stuck → `logs/fit_stuck.txt`) |
| `promt.md` | системный промпт (плейсхолдеры, HTML, wake-word, глоссарий, краткость коротких UI-строк 19.09) |
| `strwidth.py` | метрика display-ширины (CJK=2, остальное=1) + пороги `FIT_*` env; общая для `validate.py` (аудит 1c) и `improve_translations.py --fit` |
| `validate.py` | семантическая автопроверка (форматтеры zh↔ru по порядку, CJK, массивы/индексы, plurals, APK через aapt2, дубли name) + WARN-аудит ширины RU vs ZH коротких строк (секция 1c, `--length-report FILE`). Exit 1 при ошибках |
| `test_improve_selftest.py` | self-test: 59/59 (guard, fit-guard, specs, wake, aapt2 round-trip, lenient parse_repair) |
| `extract_cjk.py` | извлечение strings/arrays/plurals; массивы — ВСЕ элементы включая пустые (0..N-1) |
| `generate_overlays.py` / `generate_overlays_static.py` | `res/values-ru/` у обеих схем; plurals few/many = копия other; массивы 0..N непрерывно |
| `create_rro_min.py` / `create_rro_static.py` | aapt2 compile+link, подпись; компилируют `values*` |
| `create_db.py` / `apply_db_translations.py` | SQLite-словарь (17.09 починены: `--find` работало, матч (app,name), guard, атомарно) |
| `fix_placeholders.py` | одноразовая правка 12 строк (17.09), оставить как отчёт |
| `create_app_pipeline.sh` | полный цикл: create_db → generate_overlays(±static) → create_rro_* |
| `export-to-db.sh` | create_db + validate (+ dry-run apply_db) |

### Переменные окружения (LLM-прогоны)

```
API_URL=http://10.0.0.128:11434/v1/chat/completions  API_KEY=ollama
API_MODEL=qwen3.8:27b      # improve_translations.py
API_BATCH_SIZE=8  API_MAX_TOKENS=60000  API_TIMEOUT=600  API_DEBUG=1
API_LONG_THRESHOLD=200     # zh длиннее — отправляется по одной (не в пакете)
```

## Нормализация перевода (aapt2-safe)

Модельный ответ → `_sanitize_ru` → `ru` (сырой текст) → при генерации
`_esc()` в `generate_overlays.py` эксит ОДИН раз → aapt2.
- двойное экранирование → одинарное → raw-символы (иначе `&amp;lt;` = FAIL);
- `'` / `&apos;` / `&#x27;` → `’` U+2019 (aapt2 отклоняет и `'`, и `&apos;`);
- живые `\n`/`\r`/`\t` → литеральные;
- `%s %d %.1f %1$s %%` не трогаются; паритет И ПОРЯДОК гонится guard'ом.

### Префиксы пакетов (НАМЕРЕННО разные)

- динамические: `com.android.vendor.translate.rro.<app>` — лаунчер СКРЫВАЕТ
  пакеты `startsWith("com.android")` (`LAUNCHER_APP_HIDDEN_DESIGN.md`, фильтр №1);
- статические: `com.deepal.translate.rro.<app>`.
динамические — `manage.bat` (см. ниже), статические —
`manage_static.bat` (`install_static_8/36`, `install_all_static`,
`uninstall_all_static` остались как самостоятельные legacy-скрипты).
validate.py проверяет префикс по схеме.
**Сбор логов:** `manage.bat report` / `manage_static.bat report` →
`collect_report.bat` (только-чтение) → `logs\deepal_<scheme>_report_<TS>.zip`
(summary.txt + ops_*.log + raw: pm list, overlay states по 100 пакетам,
locale, /vendor/overlay, crash/FATAL/ANR(+trace, auto root), main-лог
работы apk, overlay/idmap, dump оверлеев в ошибке; авто-вывод «есть ли
проблемы»). Это файл, который отправляют на анализ.
- **Логи установки:** `logs\ops_<mode>_<TS>.log` — пишет каждый
  install/enable/disable/uninstall (оба менеджера): вывод adb-команд по
  каждому пакету + RESULT + итог. Последние 10 автоматически попадают
  в report-zip. Хелперы `:OpSTs`/`:DoOpAdb`.
- **Парсер отчёта (по живому формату, 2026-09-22b):** `pm list
  --show-versioncode` на ЭТОМ ГУ = `package:PKG versionCode:N` (ПРОБЕЛ,
  без `=`; проверено по репорту 22.09) → поиск `package:PKG ` (хвостовой
  пробел, `fota`≠`fotaservice`) + фолбэки `…=`/без хвоста; versionCode —
  `tokens=3 delims=:` (у обоих форматов ровно два `:`). Строка overlay
  list — двойной поиск: `PKG ` и regex `^.*PKG$` (точки экранированы);
  `/data/anr` — auto `adb root` + trace (`head -150 /data/anr/$f` — с
  полным путём!). **БАГ-КАПКА bat:** `echo text (c скобками)` как команда
  `if`/внутри блока ломает парсинг блока — СКОБКИ В ЭХО ВНУТРИ БЛОКОВ
  ОБЯЗАТЕЛЬНО `^(` `^)` (22.09-22b: строки `RESULT:` ops-лога → «OK: N /
  Ошибок: N» и ложный ERROR при успешной установке).
- **Меню bat'ов появляется ВСЕГДА** (даже без adb): быстрая проверка
  `:ADB_CHECK_FAST` рисует баннер статуса, полный `:ADB_CHECK` (рестарт
  демона, ожидание авторизации) — по пункту [R] или при выборе действия.
  `:ADB_CHECK` не прерывает скрипт (только флаг `A_OK`) — после того инцидента,
  когда `exit /b 1` внутри вызова по `call` убивал весь bat и меню не
  появлялось (+ вечный 45-сек цикл при unauthorized).

## Важные решения

- **P1 (отменён после проверки bat'ов)**: единения префикса NЕТ —
  `com.android.vendor.*` у динамических = скрытие из лаунчера.
- wake-word `***你好` в `WT_VehicleCenter/Exterior_voice_interaction_title`
  НЕ переводится (голосовая команда) — в `CJK_WHITELIST`.
- Arrays: пустые `<item></item>` обязательны (индексы 0..N-1 непрерывно;
  сдвинутый индекс = сдвинутые статусы Wi-Fi на ГУ).
- Plurals: `few`/`many` пишутся как копия `other` (пустой `few` = сломанная
  форма 2-4 шт. на ГУ).
- `specs()` в validate/improve: regex `%(\d+\$)?(\.?\d*)([dfs])|%%`,
  упорядоченно по вхождениям (сортировка гасила перестановку %1$s↔%2$s).
- **Длинные строки (len(zh)>=200) — по одной** в `improve_translations.py`
  (пакет из 8 с длинной рвал весь батч), режим `--long` обходит progress-фильтр.
  Причина `"None"` в данных: `str(None)` от JSON `null` — починено `or ""`;
  guard теперь отклоняет дегенеративные ответы + короткий ответ на длинном.

## Зависимости и окружение

- Ollama `10.0.0.128:11434`, Java 21+, Python 3.12+,
  Android SDK 34 (`/opt/android-sdk/...`), `aapt2`/`apksigner`, `keys/platform.jks`.
- Проект НЕ в git — бэкап критичных правок делайте вручную
  (в сессии 17.09 бэкапы были в `/tmp/opencode/bak_*.json`).

## Ширина RU vs ZH (перенос на 2 строки) — 19.09

- Проблема: RU-перевод заметно шире ZH-оригинала → в фиксированном виджете
  (кнопка/лейбл) переведённая строка переносится на 2 строки. RRO трогает
  только `string`, layout виджетов (maxLines/ellipsize) не меняется — лечится
  УКОРОЧЕНИЕМ перевода, а не правкой layout.
- Триаж (`strwidth.py`): короткие UI-строки (zh по display-ширине <= 14, <= 1
  перевода строки) где RU > 2.5x ZH и RU >= 24 юнита. По данным 18.09:
  **1067 строк / 71 прил.** Топ: WT_VehicleCenter=211, WT_FusionNavigation=142,
  WT_MultiMediaCenter=51, WT_TinnoveSmartScene=50.
- Лечение: `improve_translations.py --fit` (мягкий «только короче» + жёсткий
  cap `max_chars=min(28, 2·zh_w+8)` в пайлоаде). Не укоротилось — `ru` не
  затирается, строка в `logs/fit_stuck.txt` (часть слов просто не имеет
  короткого рус. эквивалента). Свой прогресс `improve_fit_progress.json`.
  Аудит «до/после» — `validate.py --skip-apk --length-report logs/fit_report.txt`.
- **СДЕЛАНО (19.09):** ПОЛНЫЙ `--fit`-прогон завершён: **1058/1059 укорочено**
  (1 stuck — `WT_FusionNavigation/guide_gps_low_subtitle`, модель трижды
  вернула пустой content; поправлено вручную «Выйдите на открытое место»).
  Перешироких **1067 → 3** (остаток у cap: Fota/upgrade_leave,
  WT_Link/car_control_off_tip, WT_SystemService/alarm_text_arr_55 — 24w).
  `validate.py` (full с aapt2) 0 ошибок; per-app diff против бэкапа: ровно
  71 приложение / 1067 строк (все укорочены, плейсхолдеры целы). Overlays
  перегенерированы, **оба набора APK пересобраны** (100+100, 0 FAIL).
- Пороги (`FIT_*`) — env-переопределяемые константы в `strwidth.py`; после
  первого полного прогона подкрутить по `logs/fit_report.txt`.

## Известные остатки (не блокирующие)

- **8 строк не влезает в лимит aapt2 (32 700 UTF-8-байт, 01.10)** и
  намеренно НЕ пишется в оверлеи (на ГУ — текст источника, а не
  «STRING_TOO_LARGE»): WT_FusionNavigation/{clause_content, clause_content1,
  policy_content, policy_content1}, WT_FusionNavigation/
  road_book_my_agreement_two_content, WT_GameCenter/str_procotol,
  **WT_BTPhone/dialog_privacy_details (42 107 B) и
  AdayoDvrLocalService/dvr_permission_tip_text (43 398 B, LONG 6407 симв.
  — выросли после правок 27.09/01.10)**. Полный перевод есть в
  `translations/*.json` (поле `ru`), включаются только при split-рефакторинге
  приложения. Генератор печатает `[WARN] … не влезли в лимит aapt2`;
  `validate.py` — 8 WARN «не влезает в аapt2-лимит».
- `apply_db_translations.py` — только «пополнение пустых»; все прогоны
  завершены, можно гонять через `--dry-run`.
- **bat-менеджеры: adb-зависимое не проверено автоматически.** Wine (20.09)
  подтвердил синтаксис/структуру/меню/скелет отчёта и поймал+починил 13
  live-багов (12 неэкранированных скобок в `echo` в `if (...)`-блоках +
  «ECHO is OFF» в summary). Но wine НЕ исполняет adb (mock не запускается
  `cmd.exe`) и даёт false-negative на `findstr /R "…$"` — поэтому
  ФОРМАТЫ `pm list --show-versioncode` / `cmd overlay list`, лог установки
  и реальный report-zip проверяются **только на живой Windows + adb + HU**.
  TODO: live-HU-проверка перед первой крупной установкой.
- (18.09) мусор вычищен: `__pycache__/`, `scripts/__pycache__/`, `rro_builds/`,
  `scripts/logs/`; устаревшие снапшоты `NEW_SESSION.md`/`PROJECT_DATA.md`/
  `REVIEW.md`/`TRANSLATE_TARGETS.md` удалены; `RRO-overlay-howto.md` перенесён
  в `docs/`. Источник процессных снапшотов — только `CHANGELOG.md`.
