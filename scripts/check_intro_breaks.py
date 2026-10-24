#!/usr/bin/env python3
"""Проверка «когда нужен _-разрыв» для mode_introduce_* (WT_TinnoveSmartScene).

Механика (по smali, не угадывание):
  IntroductionDialog.kt:  context.getString(R.string.mode_introduce_X).split("_")
  -> куски складываются в List (ea/i.b); ViewPager2-vpAdapter:
     getItemCount() = list.size(), onBindViewHolder(i) -> setText(list[i]).
  IМЕННО ПОТОМУ КАЖДЫЙ КУСОК МЕЖДУ _ = ОДНА СТРАНИЦА ДИАЛОГА
  (layout_introduce_content.xml, TextView tv_content, 36sp, wrap_content).
  Слово-перенос ВНУТРИ куска TextView делает сам (line breaks),
  «крупные» разрывы = только _.

Анатомия диалога (layout_introduction_dialog.xml):
  контейнер 1000x600dp; контент = 1000 - 80L - 73R = 850dp шириной,
  высота под текстом ~ 600 - 88 (title) - 24 - 40 (guide) = 448dp,
  высота строки 36sp ~ 42.5dp -> на страницу ~10 строк (для точной высоты
  текста вычесть картинку iv_content внизу — по скриншоту).

ФЛАГИ:
  ПЕРЕНОС ВЫСОТЫ   — страница не влезает в ~448dp -> нужен ещё один _-разрыв;
  НЕСОГЛАСИЕ СТРАНИЦ — RU-страниц больше, чем в ZH: индикатор точек и
  нумерация 1./2./3. сбита — вернуть количество кусков как в zh-оригинале
  (длинные куски пусть переносятся строками ВНУТРИ страницы);
  СКОшенные страницы — очень разной длины (короткая/длинная) — при желании
  сдвинуть границу _ для симметрии (не флаг, подсказка).

ЗОЛОТОЙ КРИТЕРИЙ: количество страниц = как в ZH, каждая страница <= 10 строк.

Запуск:  python3 scripts/check_intro_breaks.py [фильтр-по-имени-ключа]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT_CANDIDATES = (
    "/home/user/projects/deepal-firmware/extracted/mnt_sys/system/fonts/Roboto-Regular.ttf",
    "/tmp/opencode/tsr/m320/system/fonts/Roboto-Regular.ttf",
    "/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf",
)
TSP = 36.0                  # textSize tv_content, sp
AVAIL_W_DP = 850.0          # 1000 - 80 - 73
AVAIL_H_DP = 448.0          # 600 - ~88 - 24 - 40
MS = 100                    # размер измерения


def load_font():
    from PIL import ImageFont
    for p in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(p, MS)
        except OSError:
            continue
    sys.exit("Roboto-Regular.ttf не найден (пробовали: " + ", ".join(FONT_CANDIDATES) + ")")


def main() -> int:
    f = load_font()
    k = TSP / MS
    line_h = TSP * (f.getmetrics()[0] + f.getmetrics()[1]) / MS
    max_lines = int(AVAIL_H_DP / line_h)

    def w(s: str) -> float:
        return f.getlength(s) * k

    def wrap(par: str) -> list[str]:
        lines, cur = [], ""
        for word in par.split(" "):
            trial = (cur + " " + word).strip()
            if not cur or w(trial) <= AVAIL_W_DP:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    data = json.load(open(ROOT / "translations/WT_TinnoveSmartScene.json"))
    only = sys.argv[1] if len(sys.argv) > 1 else None
    bad = 0
    for e in data:
        n = e["name"]
        if not n.startswith("mode_introduce_") or (only and only not in n):
            continue
        parts = e["ru"].split("_")
        zh_parts = e["zh"].split("_")
        print(f"\n=== {n}  ({len(parts)} стр. | в zh {len(zh_parts)}) ===")
        for i, part in enumerate(parts, 1):
            lines = wrap(part)
            longest = max((w(l) for l in lines), default=0.0)
            h = len(lines) * line_h
            flags = []
            if len(lines) > max_lines:
                flags.append("ПЕРЕНОС ВЫСОТЫ — нужен ещё _")
                bad += 1
            if i > len(zh_parts):
                flags.append("лишняя страница (zh: нет)")
            print(f"  п.{i}: {len(lines):d} стр., h={h:3.0f}/{AVAIL_H_DP:.0f}dp, "
                  f"maxW={longest:3.0f}/{AVAIL_W_DP:.0f}dp"
                  + ("   " + "; ".join(flags) if flags else ""))
        if len(parts) != len(zh_parts):
            print(f"  *** НЕСОГЛАСИЕ СТР.: RU={len(parts)} vs ZH={len(zh_parts)} "
                  f"(индикатор/нумерация съедены) ***")
            bad += 1
        if len(parts) >= 2:
            ls = [len(wrap(p)) for p in parts]
            if min(ls) <= 2 and max(ls) >= 4:
                print(f"  (кривой баланс: {ls} — страницы разной длины; при желании "
                      f"перенести границы _ для симметрии)")
    print(f"\nфлагов: {bad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
