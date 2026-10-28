#!/bin/bash
# Сборка и публикация GitHub-релиза проекта deepal-HU-translate-3.2.0.
#
# Каждый релиз = НОВЫЙ аннотированный тег (старые не перезаписываются).
#
# Использование:
#   build_release.sh <N> [тег] [--dry-run]
#     N  — номер сборки (в теге), напр. 26.1
#     тег — полный тег, по умолчанию v3.2.0-<N>
#     --dry-run — только пройтись по шагам 1–3 (git-чеки, входы, staging+zip),
#                 тег НЕ создавать и в GitHub НЕ публиковать
#
# Примеры:
#   build_release.sh 26.1          # тег v3.2.0-26.1 (по умолчанию)
#   build_release.sh 26.1 --dry-run
#   build_release.sh 26.2 v3.2.0-26.2
#
# Тег, который уже существует на GitHub, ПЕРЕИСПОЛЬЗОВАТЬ НЕЛЬЗЯ —
# выбирайте следующий N (или новый тег). Старые релизы не трогаются.
#
# Шаги:
#   1)  рабочее дерево чистое (все правки закоммичены);
#       если main впереди origin/main — push
#   2)  проверка входов: apks_rro_{min,static}/ (APK + .idsig),
#       deepl/deepl.exe/shot/shot.exe, targets.txt, RELEASE_README.md
#   3)  staging + zip (без .bat: APK, Go-бинарники, targets.txt, README.md)
#   4)  новый тег + push
#   5)  GitHub Release на новый тег + upload zip-ассета
#       (токен берётся из ~/.git-credentials)
#
# APK НЕ пересобираются — берутся из текущих каталогов apks_rro_{min,static}/.
# Для пересборки APK: create_app_pipeline.sh, проверка: validate.py.
set -euo pipefail
cd "$(dirname "$0")"
ROOT=$(pwd)
BRANCH=main

command -v git >/dev/null 2>&1  || { echo "ERROR: git не найден";  exit 1; }
command -v zip >/dev/null 2>&1  || { echo "ERROR: zip не найден";   exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 не найден"; exit 1; }

N=""
TAG=""
DRYRUN=0
for a in "$@"; do
    case "$a" in
        --dry-run) DRYRUN=1 ;;
        -*)
            echo "ERROR: неизвестный флаг $a"
            exit 1
            ;;
        *)
            if [ -z "$N" ]; then N=$a; else TAG=$a; fi
            ;;
    esac
done
[ -n "$N" ] || { echo "Использование: build_release.sh <N> [тег] [--dry-run]"; exit 1; }
[ -z "$TAG" ] && TAG="v3.2.0-$N"

# --- GitHub (owner/repo из remote origin) ---
REMOTE=$(git remote get-url origin 2>/dev/null || true)
case "$REMOTE" in
    https://github.com/*|*github.com/*)
        ORG_REPO=$(echo "$REMOTE" | sed -E 's#(https?://)?[a-z.]*github.com/##; s#\.git$##')
        ;;
    *)
        ORG_REPO=""
        ;;
esac
[ -n "$ORG_REPO" ] || { echo "ERROR: origin-remote не похож на github: $REMOTE"; exit 1; }
TOK=$(sed -n 's#https://[^:]*:\([^@]*\)@github.com#\1#p' ~/.git-credentials 2>/dev/null | head -1)
[ -n "$TOK" ] || { echo "ERROR: токен GitHub не найден в ~/.git-credentials"; exit 1; }
API="https://api.github.com/repos/$ORG_REPO"

# --- 1) чистое дерево + main в sync с origin ---
echo .
echo "[1/5] Проверка git-состояния ($ORG_REPO, ветка $BRANCH)..."
if [ -n "$(git status --porcelain)" ]; then
    echo "ERROR: есть незакоммиченные изменения — закоммитьте перед релизом:"
    git status --porcelain
    exit 1
fi
LOCAL=$(git rev-parse "$BRANCH")
REMOTE_HEAD=$(git ls-remote origin "refs/heads/$BRANCH" | awk '{print $1}')
if [ "$LOCAL" != "$REMOTE_HEAD" ]; then
    echo "  $BRANCH впереди/расходитесь ($LOCAL vs $REMOTE_HEAD) — push..."
    git push origin "$BRANCH"
fi
echo "[OK] дерево чистое, $BRANCH синхронен ($LOCAL)"

# --- 2) входы ---
echo .
echo "[2/5] Проверка in-файлов..."
fail=0
for d in apks_rro_min apks_rro_static; do
    if [ ! -d "$d" ]; then
        echo "  ERROR: нет каталога $d/ (сборка APK: create_app_pipeline.sh)"; fail=1; continue
    fi
    APK=$(ls "$d" | grep -c '_RRO\.apk$'  || true)
    IDSG=$(ls "$d" | grep -c '\.idsig$'   || true)
    if [ "$APK" -eq 0 ] || [ "$IDSG" -eq 0 ]; then
        echo "  ERROR: в $d/ нет APK/idsig (apk=$APK idsig=$IDSG)"; fail=1
    else
        echo "  [OK] $d/: $APK APK + $IDSG idsig"
    fi
done
for f in deepl deepl.exe shot shot.exe targets.txt RELEASE_README.md; do
    if [ -f "$f" ]; then
        echo "  [OK] $f"
    else
        echo "  ERROR: нет файла $f (Go-бинарники: build_go.sh)"; fail=1
    fi
done
[ "$fail" -eq 0 ] || exit 1

if [ "$DRYRUN" = "1" ]; then
    echo .
    echo "[DRY-RUN] пропущен шаг 3 (staging+zip), тег и GitHub-публикация не выполняются."
    echo .
    echo "========================================================"
    echo "  DRY-RUN: шаги 1–2 прошли; тег $TAG создание НЕ выполняется."
    echo "  Для публикации: build_release.sh $N"
    echo "========================================================"
    exit 0
fi

# --- 3) staging + zip ---
echo .
echo "[3/5] Staging + zip..."
STAGE="/tmp/opencode/release_${TAG}"
rm -rf "$STAGE" && mkdir -p "$STAGE"
cp -a "$ROOT/apks_rro_min" "$ROOT/apks_rro_static" "$STAGE/"
cp -a "$ROOT/deepl" "$ROOT/deepl.exe" "$ROOT/shot" "$ROOT/shot.exe" \
      "$ROOT/targets.txt" "$STAGE/"
cp -a "$ROOT/RELEASE_README.md" "$STAGE/README.md"
ZIPNAME="deepal-HU-translate_${TAG}.zip"
( cd "$STAGE" && zip -qr9 "$ZIPNAME" . )
ZIP="$STAGE/$ZIPNAME"
ZIPSZ=$(stat -c%s "$ZIP")
echo "[OK] $ZIP ($ZIPSZ байт): $(ls "$STAGE" | grep -v "$ZIPNAME" | tr '\n' ' ')"

# --- 4) новый тег + push ---
echo .
echo "[4/5] Тег $TAG -> $LOCAL ..."
if git ls-remote --tags origin "refs/tags/$TAG" | grep -q .; then
    echo "ERROR: тег $TAG уже существует на origin. Старые релизы не трогаем:"
    echo "  выберите следующий N:  build_release.sh <другой N>"
    exit 1
fi
git tag -a "$TAG" -m "deepal-HU-translate $TAG (S05, fw 3.2.0): сборка $N — RRO-оверлеи (dyn+stat), Go-инструменты, README" "$LOCAL"
git push origin "refs/tags/$TAG"
echo "[OK] тег $TAG создан (аннотированный, новый) и запушен"

# --- 5) GitHub Release + ассет ---
echo .
echo "[5/5] Публикация GitHub-релиза $TAG ..."
CREATED=$(curl -s -w '\n%{http_code}' -X POST -H "Authorization: token $TOK" \
    -H 'Content-Type: application/json' \
    -d "{\"tag_name\":\"$TAG\",\"name\":\"deepal-HU-translate $TAG\",\"body\":\"Сборка $N (fw 3.2.0, S05).\n\nСостав: apks_rro_min/ (динамические RRO, 100 APK+idsig), apks_rro_static/ (статические RRO, 100 APK+idsig), deepl/deepl.exe (менеджер RRO, обе схемы, пункт [9] — восстановление оригинальной локали zh-CN), shot/shot.exe (logcat-охота), targets.txt, README.md (инструкция установки; .bat нет).\"}" \
    "$API/releases")
HTTP_CODE=$(echo "$CREATED" | tail -1)
if [ "$HTTP_CODE" != "201" ]; then
    echo "ERROR: создание релиза: HTTP $HTTP_CODE"
    echo "$CREATED" | head -c 800
    exit 1
fi
UPLOAD_URL=$(echo "$CREATED" | head -n -1 | python3 -c "import json,sys; print(json.load(sys.stdin)['upload_url'].split('{')[0])")
RELEASE_URL=$(echo "$CREATED" | head -n -1 | python3 -c "import json,sys; print(json.load(sys.stdin)['html_url'])")

python3 - "$TOK" "$UPLOAD_URL" "$ZIP" "$ZIPNAME" <<'PYEOF'
import sys, urllib.parse, http.client
tok, up, zf, name = sys.argv[1:5]
data = open(zf, "rb").read()
u = urllib.parse.urlparse(up + "?name=" + name)
c = http.client.HTTPSConnection(u.netloc)
c.request("PUT", u.path + ("?" + u.query if u.query else ""), body=data,
          headers={"Authorization": f"token {tok}",
                   "Content-Type": "application/zip",
                   "User-Agent": "build-release"})
r = c.getresponse()
print("upload:", r.status)
if r.status != 201:
    print(r.read().decode()[:800]); sys.exit(1)
PYEOF

echo .
echo "========================================================"
echo "  РЕЛИЗ ГОТОВ: $TAG"
echo "  $RELEASE_URL"
echo "  Ассет: $ZIPNAME ($ZIPSZ байт)"
echo "========================================================"
echo "  Следующая сборка: build_release.sh <N+1>   (новый тег v3.2.0-<N+1>)"
