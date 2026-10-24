# scripts/

Вспомогательные инструментарии (кроме пайплайн-шагов из корня — те в корне).
Запускать отовсюду: пути к проекту вычисляются от расположения файла.

## Диагностический набор «китайский на ГУ» (18–19.10, layout-литералы)

Каскадная диагностика: почему часть строк с RU-переводом на экране
показывается по-китайски. Прогонять по порядку A→K; итог — в
`MEMORY.md` § «layout-литералы» и `CHANGELOG.md`.

| Скрипт | Что делает |
|---|---|
| `inv_A_json.py` | субстроковый поиск zh-фраз по `translations/*.json` |
| `inv_B_exact.py` | точные совпадения `zh == фраза` (app, name, ru) |
| `inv_C_decompiled.py` | те же zh-тексты в `decompiled/*/res` — владелец ресурса в ROM |
| `inv_D_chain.py` | цепочка JSON → overlays (values-ru/values) → наличие RRO-APK |
| `inv_E_owner.py` | по ПЕРЕВЕДЁННЫМ (ru) строкам экрана — owner-app |
| `inv_F_layouts.py` | CJK-литералы в layout-XML (android:text/hint/contentDescription) |
| `inv_G_targeted.py` | точечный поиск фраз в res (values* + layout) отдельных приложений |
| `inv_H_public.py` | presence `public.xml` (private layout ⇒ только static RRO), manifest static RRO |
| `inv_I_scale.py` | масштаб layout-литералов: топы приложений, примеры |
| `inv_J_precise.py` | точная статистика: файлы × атрибуты × приложения |
| `inv_final.py` | verdict по каждой фразе: А=layout / B=runtime / C=@string + dump типов RRO-APK |
| `find_cjk_in_ru.py` | какие записи JSON содержат CJK в поле `ru` (wake-words) |
| `check_overlays.py` | видимость заданных имён в `overlays*/.../values{-ru,-zh-rCN}` |
| `check_intro_breaks.py` | WT_TinnoveSmartScene: где нужны `_`-разрывы в `mode_introduce_*` — сколько страниц (split "_" в IntroductionDialog.smali), сколько строк влезает в страницу диалога (Roboto/PIL, 36sp, 850dp) |

Фраг-списки фраз для диагностики — в самих скриптах (константы), под
скриншоты 19.10; для нового набора фраз править константу в начале.
