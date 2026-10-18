# Deepal HU Translate — приложения

Все APK с CJK-строками (прошивка 3.2.0): количество строк (`CJK`) и назначение.
Цифры — актуальные из `translations/*.json` (снимок 27.09, после adapt 3.2.0),
отсортированы по убыванию `CJK`. Все CJK-строки переведены (`ru`) — 100 %.

> `CJK` — количество CJK-строк (`zh`), подлежащих переводу.
> Общий итог: **18728** CJK-строк; записей в JSON всего **18813** (остальные —
> пустые/lat `zh`-плейсхолдеры). Переведено: **18728/18728 CJK-строк (100 %)**
> + **80** non-CJK-записей из БД (итого 18808 непустых `ru`).

Исключения (не входят в список RRO, т.к. не ставятся `adb install` — 
см. `EXCLUDE9` в manage.bat): NetworkStack, MediaProviderLegacy, 
UserDictionaryProvider, DownloadProvider(+)Ui, CompanionDeviceManager, 
MtpService, CaptivePortalLogin, ContactsProvider — переводятся статикой 
(`manage_static.bat`, `/vendor/overlay`, root).

**Без оверлея вовсе** (04.10, `NO_OVERLAY_APPS` в generate_overlays*.py): 
`WT_ThemeResourcesHolder` / `WT_ThemeResourcesTheme` — любой включённый RRO 
в пуле `com.autopai.theme.resholder` скин-менеджер (WT_TinnoveCoreService 
`SkinMallImpl` через OEM `IOverlayManager`) записывает как «текущую тему» 
(`Settings.Global.CurrentSkinInfo`), и `isDayNightTheme()`=false отключает 
все 3 кнопки тем дисплей-раздела WT_VehicleCenter. ИХ 13 строк у всех 
хост-приложений дублируются локально (покрыты их RRO) — перевод не 
теряется; `translations/*.json` оставлены как данные.

**Δ от 3.1.2 → 3.2.0:** новые — `WT_NewLauncher` (замена `WT_Launcher`), 
`WT_DLNA`, `WT_AISmartPainting`, `WT_ThemeResourcesHolder`/`WT_ThemeResourcesTheme` 
(замена `WT_ThemeResourcesDay/Night`). Убраны из прошивки — `WT_Launcher`, 
`WT_ThemeResourcesDay`, `WT_ThemeResourcesNight`. `WT_ThemeResourcesCarModel` — 
в 3.2.0, но без CJK-строк (не входит в RRO).

| Приложение | CJK | Назначение |
|---|---|---|
| WT_VehicleCenter | 2153 | Центр управления автомобилем |
| WT_FusionNavigation | 1757 | Навигация |
| WT_TinnoveSmartScene | 834 | Умные сцены (атмосфера/режимы) |
| CarService | 832 | Android Automotive: системные сервисы авто |
| WT_MultiMediaCenter | 590 | Медиацентр |
| WT_HDCloudCamera | 577 | Облачная камера (удалённый HD-мониторинг) |
| WT_AIAssistant | 520 | Голосовой ассистент |
| WT_NewLauncher | 515 | Главная панель (launcher) [заменил WT_Launcher из 3.1.2] |
| Fota | 479 | OTA-обновление |
| WT_IncallPersonalCenter | 400 | Персональный центр в авто (профиль) |
| WT_VisualizationService | 399 | 3D-визуализация автомобиля |
| WT_Album | 394 | Фото/медиа |
| WT_AISmartPainting | 390 | AI-рисование (SmartPainting) [новое в 3.2.0] |
| WT_SmartSoundEffect | 388 | Звуковые эффекты |
| WT_BTPhone | 307 | Bluetooth + телефон |
| WT_AutoMaintenance | 296 | Обслуживание авто |
| WT_AISpace | 290 | AI-пространство (виджеты/персонализация) |
| WT_CarLink | 288 | CarLink (связь с телефоном/зеркалирование) |
| WT_AppStore | 288 | Магазин приложений |
| WT_TSpeech | 287 | Озвучка (TTS) |
| WT_LightSoundLab | 279 | Лаборатория света и звука |
| WT_IncallFunBox | 262 | FunBox в авто (мини-приложения) |
| WT_WtSystemUI | 250 | Системный UI (системные экраны) |
| Camera | 233 | Камера |
| WT_AISceneMode | 230 | AI-режимы сцен |
| WT_AirConditioner | 225 | Климат-контроль |
| WT_SystemService | 224 | Системные сервисы/сообщения |
| WT_Customer | 221 | Поддержка/сервис |
| WT_TinnoveCoreService | 216 | Ядро системы (системные сообщения) |
| WT_Wcenter | 215 | Центр уведомлений (Wcenter, Tencent) |
| WT_ElectronicDirections | 214 | Электронные знаки/дорожные ситуации |
| ManagedProvisioning | 211 | Provisioning устройства (профиль) |
| WT_FileManager | 198 | Файловый менеджер |
| DeepalShowCarMode | 186 | 3D-показ машины (ShowCar) |
| WT_Link | 174 | Связь с устройствами (Link) |
| AdayoAPA | 155 | Автопарковка (APA) |
| AdayoDvr | 155 | Видеорегистратор |
| WT_DLNA | 152 | DLNA (медиа-стриминг в машину) [новое в 3.2.0] |
| WT_MLWecarControl | 144 | WeCar: управление медиа |
| PackageInstaller | 126 | Установщик пакетов |
| DeepalDriveMode | 124 | Режимы вождения |
| AdayoDvrLocalService | 116 | Видеорегистратор (локальный сервис) |
| WT_DownloadLog | 112 | Журнал загрузок |
| Puremic | 99 | Микрофон (запись/караоке) |
| WT_IncallLive | 98 | Видео/Live в авто |
| WT_InputMethod | 97 | Клавиатура (input method) |
| WT_AccountServer | 93 | Сервер аккаунта |
| WT_ECall | 93 | Экстренный вызов SOS |
| SensetimeAiService | 90 | AI-сервис (Sensetime) |
| WT_GameCenter | 88 | Игры (центр) |
| EMode | 86 | E-режим (экономия/электро) |
| ldm | 83 | Лёгкие динамические модули (системный фреймворк) |
| WT_GameZone | 80 | Игровая зона |
| PowerManager | 79 | Управление питанием |
| Upgrade | 75 | Обновление ПО |
| CarPlayView | 74 | CarPlay UI |
| AdayoLog | 74 | Системные логи |
| CertInstaller | 68 | Установка сертификатов |
| WT_FiveChess | 59 | Игра «Пять в ряд» |
| SystemUpdater | 57 | Обновление системы |
| WT_WTAISceneEngine | 56 | AI-движок сцен |
| HwDMSDPDevice | 55 | Сервис разрешений/устройств (Huawei DMS) |
| InputDevices | 43 | Устройства ввода |
| AdayoAgnssService | 42 | A-GNSS (спутниковая позиция) |
| CarActivityResolver | 39 | Резолвер activities (Car) |
| DownloadProvider | 37 | Провайдер загрузок |
| WT_Spacecraft | 36 | Игра: космос |
| WT_SpeedRun | 34 | Игра: гонки (SpeedRun) |
| DownloadProviderUi | 32 | UI загрузок |
| WT_SweepMine | 30 | Игра: сапёр |
| CaptivePortalLogin | 29 | Captive portal (Wi-Fi-авторизация) |
| WT_BubblePop | 28 | Мини-игра (с блокировкой при вождении) |
| MtpService | 26 | MTP (USB-обмен) |
| DynoMode | 26 | Режим динамометра (Dyno) |
| WT_TinnoveCore3D | 24 | 3D-ядро (рендер-сервер) |
| AutoTest | 24 | Автоматизированное тестирование |
| Shell | 23 | Системный shell |
| AdayoAlarm | 23 | Будильники/оповещения |
| NaviManagerService | 23 | Навигационный сервис |
| fotaservice | 21 | OTA-сервис |
| HiSight | 21 | Системный сервис (Huawei HiSight, в основном общие UI-строки) |
| StorageWarn | 21 | Предупреждения о хранилище |
| HiViewLite | 21 | Huawei HiView (системная диагностика) |
| Player857 | 21 | Медиаплеер |
| WT_MiniApp | 21 | Мини-приложения |
| PhoneLink | 21 | Связь с телефоном |
| MediaProviderLegacy | 21 | Legacy media-провайдер |
| BackupRestoreConfirmation | 20 | Бэкап/восстановление |
| ContactsProvider | 16 | Контакты |
| VpnDialogs | 16 | VPN-диалоги |
 | WT_ThemeResourcesHolder | 13 | Темы: холдер ресурсов [заменил WT_ThemeResourcesDay]; **без оверлея** (ломает скин) |
 | WT_ThemeResourcesTheme | 13 | Темы: ресурсные пакеты (тема) [заменил WT_ThemeResourcesNight]; **без оверлея** (ломает скин) |
| deCoreApp | 12 | Контроль целостности приложений (системная безопасность) |
| DynamicSystemInstallationService | 12 | Установка динамической системы |
| KeyChain | 8 | Хранилище ключей |
| NetworkStack | 7 | Сетевой стек |
| ExternalStorageProvider | 4 | Внешнее хранилище |
| SettingsProvider | 3 | Провайдер настроек |
| CompanionDeviceManager | 3 | Управление сопряжёнными устройствами |
| CarFrameworkPackageStubs | 2 | Стубы Car-фреймворка |
| FusedLocation | 1 | Сводное определение местоположения |
| UserDictionaryProvider | 1 | Пользовательский словарь |
| **Итого** | **18728** | **102 приложений, переведено 18728/18728 CJK-строк (100 %)** |
