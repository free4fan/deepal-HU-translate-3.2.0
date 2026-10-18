@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
set "LOGS_DIR=logs"
set "TARGETS_FILE=..\..\..\home\user\projects\deepal-HU-translate-3.2.0\targets.txt"
call :LoadTargets
call :EnsureRuLocale
exit /b 0
