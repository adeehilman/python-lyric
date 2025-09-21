#!/usr/bin/env python3
import re, json, os, shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"
DIST = ROOT / "dist"

LRC_TS = re.compile(r"\[(\d{1,2}):(\d{2})(?:\.(\d{1,2}))?\]")

def parse_lrc(text: str):
    meta = {"ti":"", "ar":"", "al":""}
    lines = []
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw: continue
        if raw.startswith("[ti:"): meta["ti"] = raw[4:-1].strip(); continue
        if raw.startswith("[ar:"): meta["ar"] = raw[4:-1].strip(); continue
        if raw.startswith("[al:"): meta["al"] = raw[4:-1].strip(); continue

        matches = list(LRC_TS.finditer(raw))
        if not matches:
            # baris tanpa timestamp—append ke waktu terakhir (opsional)
            if lines:
                lines[-1]["text"] += (" " + raw)
            continue

        # teks setelah semua tag waktu
        text_start = matches[-1].end()
        lyric_text = raw[text_start:].strip()
        if not lyric_text: lyric_text = "…"

        for m in matches:
            mm = int(m.group(1))
            ss = int(m.group(2))
            cs = int(m.group(3) or 0)
            start = mm*60 + ss + cs/100.0
            lines.append({"start": start, "text": lyric_text})

    # sort by time
    lines.sort(key=lambda x: x["start"])
    return meta, lines

def copy_assets():
    (DIST / "assets").mkdir(parents=True, exist_ok=True)
    for p in ASSETS.glob("*"):
        shutil.copy2(p, DIST / "assets" / p.name)

def main():
    DIST.mkdir(exist_ok=True)
    # read lrc
    lrc_path = ROOT / "lyrics.lrc"
    lrc_text = lrc_path.read_text(encoding="utf-8")
    meta, lines = parse_lrc(lrc_text)

    # template
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(['html'])
    )
    tpl = env.get_template("base.html")

    audio_url = "assets/song-real.mp3"
    cover_url = "assets/cover.jpg" if (ASSETS / "cover.jpg").exists() else "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="

    html = tpl.render(
        title = meta.get("ti") or "Unknown Title",
        artist = meta.get("ar") or "",
        cover_url = cover_url,
        audio_url = audio_url,
        data_json = json.dumps(lines, ensure_ascii=False)
    )
    (DIST / "index.html").write_text(html, encoding="utf-8")
    copy_assets()
    print("✅ Build done → dist/index.html")

if __name__ == "__main__":
    main()
