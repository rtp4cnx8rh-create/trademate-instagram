#!/usr/bin/env python3
"""
Rendert eine Karussell-Story als 1080x1080-JPGs im Design der Wochenposts.

Die Story steht als JSON in stories/<name>.json, das Layout kommt aus den
Tokens weiter unten (abgemessen an images/KW-36/*.jpg). Gerendert wird mit
headless Chrome: pro Slide eine in sich geschlossene HTML-Datei (Fonts und
Wortmarke als data:-URI), danach Screenshot -> PNG -> JPG.

    python3 carousel/render.py fun-trader
    python3 carousel/render.py fun-trader --keep-html   # HTML zum Debuggen behalten
    CHROME=/pfad/zu/chrome python3 carousel/render.py fun-trader

Voraussetzungen: Pillow (pip install pillow) und ein Chrome/Chromium-Binary.
"""

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
STORIES = ROOT / "stories"
OUT = ROOT / "out"

SIZE = 1080
MARGIN = 96          # Aussenrand wie in den Wochenposts
LOGO_W = 352         # Wortmarke inkl. 6px Freiraum; Marke selbst 340px breit
LOGO_PAD = 6         # transparenter Rand im PNG, wird bei der Position abgezogen
CARD = dict(x=118, y=469, w=844, h=515, r=28)

# Farben aus den Vorlagen (images/KW-36) gepickt.
COLORS = dict(
    dark_bg_from="#23262b",
    dark_bg_mid="#15171b",
    dark_bg_to="#0b0c0e",
    light_bg_from="#ffffff",
    light_bg_to="#e6e7eb",
    card="#000000",
    tile="#101215",
    green="#00e677",
    red="#fb4c5b",
    muted="#9aa0a8",
    white="#ffffff",
)

# Silber-/Anthrazit-Verlauf der Headlines.
SILVER = "linear-gradient(135deg,#ffffff 0%,#e2e5ea 45%,#9399a2 100%)"
GRAPHITE = "linear-gradient(135deg,#101216 0%,#2f3238 45%,#767b84 100%)"


def data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def font_face(weight: int) -> str:
    uri = data_uri(ASSETS / "fonts" / f"inter-latin-{weight}-normal.woff2", "font/woff2")
    return (
        "@font-face{font-family:'Inter';font-style:normal;"
        f"font-weight:{weight};src:url({uri}) format('woff2');font-display:block;}}"
    )


def base_css() -> str:
    return "".join(font_face(w) for w in (500, 700, 800)) + f"""
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:{SIZE}px;height:{SIZE}px;overflow:hidden;}}
body{{font-family:'Inter','Liberation Sans',sans-serif;-webkit-font-smoothing:antialiased;}}
.slide{{position:relative;width:{SIZE}px;height:{SIZE}px;overflow:hidden;}}
.slide.dark{{background:linear-gradient(135deg,{COLORS['dark_bg_from']} 0%,{COLORS['dark_bg_mid']} 45%,{COLORS['dark_bg_to']} 100%);}}
.slide.light{{background:linear-gradient(135deg,{COLORS['light_bg_from']} 0%,#f4f5f7 55%,{COLORS['light_bg_to']} 100%);}}
.mark{{position:absolute;width:{LOGO_W}px;}}
.mark.tl{{left:{MARGIN - LOGO_PAD}px;top:{MARGIN - LOGO_PAD}px;}}
.mark.bc{{left:50%;transform:translateX(-50%);bottom:{SIZE - 982 - LOGO_PAD}px;}}
.mark.br{{right:{MARGIN - LOGO_PAD}px;bottom:{SIZE - 982 - LOGO_PAD}px;}}
.headline{{font-weight:800;font-size:94px;line-height:101px;letter-spacing:-2.6px;
  background-clip:text;-webkit-background-clip:text;color:transparent;}}
.headline.silver{{background-image:{SILVER};}}
.headline.graphite{{background-image:{GRAPHITE};}}
.counter{{position:absolute;right:{MARGIN}px;top:{MARGIN + 12}px;font-weight:700;font-size:26px;
  letter-spacing:3px;}}
.note{{position:absolute;left:{MARGIN}px;right:{MARGIN}px;bottom:44px;font-weight:500;
  font-size:22px;letter-spacing:0.2px;text-align:center;}}
.card{{position:absolute;left:{CARD['x']}px;top:{CARD['y']}px;width:{CARD['w']}px;height:{CARD['h']}px;
  background:{COLORS['card']};border-radius:{CARD['r']}px;border:1px solid rgba(255,255,255,0.09);
  box-shadow:0 40px 90px rgba(0,0,0,0.55);padding:34px 34px 30px;display:flex;flex-direction:column;}}
.card-title{{display:flex;align-items:center;justify-content:space-between;
  font-weight:700;font-size:34px;color:{COLORS['muted']};letter-spacing:-0.4px;}}
.chev{{color:#5c6069;font-size:34px;font-weight:700;}}
.stats{{display:flex;gap:20px;}}
.stats .cell{{flex:1;text-align:center;}}
.stats .cell .l{{font-weight:500;font-size:26px;color:{COLORS['muted']};}}
.stats .cell .v{{font-weight:700;font-size:46px;color:{COLORS['white']};letter-spacing:-1px;margin-top:6px;}}
.tiles{{display:flex;gap:18px;}}
.tiles .tile{{flex:1;background:{COLORS['tile']};border-radius:20px;padding:20px 0 24px;text-align:center;}}
.tiles .tile .l{{font-weight:500;font-size:26px;color:{COLORS['muted']};}}
.tiles .tile .v{{font-weight:700;font-size:46px;color:{COLORS['white']};letter-spacing:-1px;margin-top:6px;}}
.rows{{flex:1;display:flex;flex-direction:column;justify-content:center;margin-bottom:12px;}}
.rows .row{{display:flex;align-items:center;padding:22px 0;border-bottom:1px solid rgba(255,255,255,0.07);}}
.rows .row:last-child{{border-bottom:none;}}
.rows .row .name{{flex:1;font-weight:500;font-size:30px;color:#d7dae0;letter-spacing:-0.3px;}}
.rows .row .count{{min-width:74px;text-align:center;font-weight:700;font-size:26px;color:{COLORS['muted']};
  background:{COLORS['tile']};border-radius:12px;padding:8px 0;margin-right:26px;}}
.rows .row .amount{{min-width:190px;text-align:right;font-weight:700;font-size:40px;letter-spacing:-1px;}}
.green{{color:{COLORS['green']};}}
.red{{color:{COLORS['red']};}}
.stats .cell .v.green,.tiles .tile .v.green{{color:{COLORS['green']};}}
.stats .cell .v.red,.tiles .tile .v.red{{color:{COLORS['red']};}}
"""


def mark(kind: str, position: str) -> str:
    name = "wordmark-white" if kind == "dark" else "wordmark-dark"
    uri = data_uri(ASSETS / f"{name}.png", "image/png")
    return f'<img class="mark {position}" src="{uri}">'


def counter(index: int, total: int, theme: str) -> str:
    color = "rgba(255,255,255,0.30)" if theme == "dark" else "rgba(20,22,26,0.28)"
    return f'<div class="counter" style="color:{color}">{index:02d} / {total:02d}</div>'


def note(text: str, theme: str) -> str:
    if not text:
        return ""
    color = "rgba(255,255,255,0.34)" if theme == "dark" else "rgba(20,22,26,0.34)"
    return f'<div class="note" style="color:{color}">{text}</div>'


def statement(slide: dict, index: int, total: int) -> str:
    theme = slide.get("theme", "light")
    tone = "silver" if theme == "dark" else "graphite"
    align = slide.get("align", "left")
    lines = "<br>".join(slide["lines"])
    if align == "center":
        block = (
            f'<div class="headline {tone}" style="position:absolute;left:{MARGIN}px;right:{MARGIN}px;'
            'top:50%;transform:translateY(-50%);text-align:center">'
            f"{lines}</div>"
        )
        logo = mark(theme, "bc")
    else:
        block = (
            f'<div class="headline {tone}" style="position:absolute;left:{MARGIN}px;right:{MARGIN}px;'
            'top:50%;transform:translateY(calc(-50% - 44px))">'
            f"{lines}</div>"
        )
        logo = mark(theme, "br")

    cue = ""
    if slide.get("cue"):
        color = "rgba(255,255,255,0.42)" if theme == "dark" else "rgba(20,22,26,0.42)"
        cue = (
            f'<div style="position:absolute;left:{MARGIN}px;bottom:{MARGIN + 4}px;color:{color};'
            f'font-weight:700;font-size:28px;letter-spacing:4px">{slide["cue"].upper()} &#8594;</div>'
        )

    return (
        f'<div class="slide {theme}">{block}{cue}{logo}'
        f"{counter(index, total, theme)}{note(slide.get('note', ''), theme)}</div>"
    )


def cta(slide: dict, index: int, total: int) -> str:
    theme = slide.get("theme", "light")
    tone = "silver" if theme == "dark" else "graphite"
    lines = "<br>".join(slide["lines"])
    sub_color = COLORS["green"] if theme == "dark" else "#0f9d5a"
    body = (
        f'<div style="position:absolute;left:{MARGIN}px;right:{MARGIN}px;top:50%;'
        'transform:translateY(-54%);text-align:center">'
        f'<div class="headline {tone}">{lines}</div>'
        f'<div style="margin-top:52px;font-weight:700;font-size:36px;letter-spacing:2px;'
        f'color:{sub_color}">{slide["sub"]}</div>'
        "</div>"
    )
    return (
        f'<div class="slide {theme}">{body}{mark(theme, "bc")}'
        f"{counter(index, total, theme)}{note(slide.get('note', ''), theme)}</div>"
    )


def donut(card: dict) -> str:
    r, stroke = 104, 19
    circumference = 2 * 3.141592653589793 * r
    gap = 14  # kleine Luecke zwischen den beiden Boegen, wie in der Vorlage
    green = card["green_share"] * circumference - gap
    red = (1 - card["green_share"]) * circumference - gap
    return f"""
<svg width="{2 * (r + stroke)}" height="{2 * (r + stroke)}" viewBox="0 0 {2 * (r + stroke)} {2 * (r + stroke)}">
  <g transform="translate({r + stroke},{r + stroke}) rotate(-90)">
    <circle r="{r}" fill="none" stroke="{COLORS['green']}" stroke-width="{stroke}"
      stroke-linecap="round" stroke-dasharray="{green:.1f} {circumference - green:.1f}"/>
    <circle r="{r}" fill="none" stroke="{COLORS['red']}" stroke-width="{stroke}"
      stroke-linecap="round" stroke-dasharray="{red:.1f} {circumference - red:.1f}"
      stroke-dashoffset="{-(green + gap):.1f}"/>
  </g>
  <text x="50%" y="43%" text-anchor="middle" fill="{COLORS['muted']}"
    font-family="Inter" font-weight="500" font-size="28">{card['center_label']}</text>
  <text x="50%" y="64%" text-anchor="middle" fill="{COLORS['white']}"
    font-family="Inter" font-weight="700" font-size="54" letter-spacing="-1">{card['center_value']}</text>
</svg>"""


def stats_row(stats: list) -> str:
    cells = "".join(
        f'<div class="cell"><div class="l">{s["label"]}</div>'
        f'<div class="v {s.get("tone", "")}">{s["value"]}</div></div>'
        for s in stats
    )
    return f'<div class="stats">{cells}</div>'


def tiles_row(stats: list) -> str:
    cells = "".join(
        f'<div class="tile"><div class="l">{s["label"]}</div>'
        f'<div class="v {s.get("tone", "")}">{s["value"]}</div></div>'
        for s in stats
    )
    return f'<div class="tiles">{cells}</div>'


def spark(values: list) -> str:
    w, h = 776, 150
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    step = w / (len(values) - 1)
    pts = [(i * step, h - 12 - (v - lo) / span * (h - 30)) for i, v in enumerate(values)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"0,{h} " + line + f" {w},{h}"
    return f"""
<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{COLORS['green']}" stop-opacity="0.42"/>
      <stop offset="100%" stop-color="{COLORS['green']}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <polygon points="{area}" fill="url(#fade)"/>
  <polyline points="{line}" fill="none" stroke="{COLORS['green']}" stroke-width="5"
    stroke-linejoin="round" stroke-linecap="round"/>
</svg>"""


def rows(card: dict) -> str:
    """Liste gefundener Leaks: Regelbruch, Anzahl, Kosten."""
    out = ""
    for r in card["rows"]:
        color = COLORS["green"] if r.get("tone") == "green" else COLORS["red"]
        out += (
            f'<div class="row"><span class="name">{r["name"]}</span>'
            f'<span class="count">{r["count"]}x</span>'
            f'<span class="amount" style="color:{color}">{r["amount"]}</span></div>'
        )
    return f'<div class="rows">{out}</div>'


def bars(card: dict) -> str:
    rows = ""
    for b in card["bars"]:
        color = COLORS["green"] if b["tone"] == "green" else COLORS["red"]
        rows += f"""
<div style="margin-top:34px">
  <div style="display:flex;justify-content:space-between;align-items:baseline">
    <span style="font-weight:500;font-size:28px;color:{COLORS['muted']}">{b['label']}</span>
    <span style="font-weight:700;font-size:44px;letter-spacing:-1px;color:{color}">{b['value']}</span>
  </div>
  <div style="margin-top:14px;height:22px;border-radius:11px;background:#141619">
    <div style="width:{b['share'] * 100:.1f}%;height:100%;border-radius:11px;background:{color}"></div>
  </div>
</div>"""
    return rows


def metric(slide: dict, index: int, total: int) -> str:
    card = slide["card"]
    head = "<br>".join(slide["headline"])
    inner = ""
    if card.get("title"):
        inner = f'<div class="card-title"><span>{card["title"]}</span><span class="chev">&#8250;</span></div>'

    if card["kind"] == "donut":
        inner += (
            '<div style="flex:1;display:flex;align-items:center;justify-content:center">'
            f"{donut(card)}</div>{stats_row(card['stats'])}"
        )
    elif card["kind"] == "rows":
        inner += rows(card) + tiles_row(card["stats"])
    elif card["kind"] == "bars":
        inner += f'<div style="flex:1">{bars(card)}</div>{tiles_row(card["stats"])}'
    else:  # hero: grosse Zahl, Kurve, Kacheln - wie der Performance-Post
        inner = f"""
<div style="text-align:center">
  <div style="font-weight:500;font-size:28px;color:{COLORS['muted']}">{card['label']}</div>
  <div style="font-weight:700;font-size:78px;letter-spacing:-2px;color:{COLORS['white']};margin-top:4px">{card['value']}</div>
  <div style="font-weight:500;font-size:28px;color:{COLORS['muted']};margin-top:6px">
    <span class="green" style="font-weight:700">{card['delta']}</span> {card['delta_suffix']}</div>
</div>
<div style="flex:1;display:flex;align-items:flex-end;justify-content:center;padding-bottom:20px">{spark(card['spark'])}</div>
{tiles_row(card['stats'])}"""

    return (
        '<div class="slide dark">'
        f'{mark("dark", "tl")}'
        f'<div class="headline silver" style="position:absolute;left:{MARGIN}px;right:{MARGIN}px;top:206px">{head}</div>'
        f'<div class="card">{inner}</div>'
        f"{counter(index, total, 'dark')}{note(slide.get('note', ''), 'dark')}</div>"
    )


RENDERERS = {"statement": statement, "cta": cta, "metric": metric}


MAX_LINE = 19  # Zeichen pro Headline-Zeile bei 94px - darueber bricht Chrome um


def check_lines(slide: dict, index: int) -> None:
    for line in slide.get("lines", []) + slide.get("headline", []):
        if len(line) > MAX_LINE:
            print(
                f"  ! Slide {index:02d}: \"{line}\" ist {len(line)} Zeichen "
                f"(> {MAX_LINE}) und bricht wahrscheinlich um.",
                file=sys.stderr,
            )


def slide_html(slide: dict, index: int, total: int) -> str:
    body = RENDERERS[slide["type"]](slide, index, total)
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{base_css()}</style></head><body>{body}</body></html>"


def find_chrome() -> str:
    env = os.environ.get("CHROME")
    if env:
        return env
    candidates = [
        "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
        "/opt/pw-browsers/chromium",
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    sys.exit("Kein Chrome gefunden - Pfad ueber CHROME=... setzen.")


def shoot(chrome: str, html: Path, png: Path) -> None:
    subprocess.run(
        [
            chrome,
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            f"--window-size={SIZE},{SIZE}",
            f"--screenshot={png}",
            html.as_uri(),
        ],
        check=True,
        capture_output=True,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("story", help="Name der JSON-Datei in stories/ (ohne .json)")
    ap.add_argument("--keep-html", action="store_true")
    ap.add_argument("--quality", type=int, default=92)
    args = ap.parse_args()

    story = json.loads((STORIES / f"{args.story}.json").read_text())
    slides = story["slides"]
    out_dir = OUT / story["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome()
    work = Path(tempfile.mkdtemp(prefix="carousel-"))

    for i, slide in enumerate(slides, start=1):
        check_lines(slide, i)
        html = work / f"{i:02d}.html"
        html.write_text(slide_html(slide, i, len(slides)))
        png = work / f"{i:02d}.png"
        shoot(chrome, html, png)
        jpg = out_dir / f"{i:02d}.jpg"
        Image.open(png).convert("RGB").save(jpg, quality=args.quality, subsampling=0)
        print(f"{jpg.relative_to(ROOT.parent)}  ({slide['type']})")

    (out_dir / "caption.txt").write_text(story["caption"] + "\n")
    print(f"{(out_dir / 'caption.txt').relative_to(ROOT.parent)}")

    if args.keep_html:
        for f in work.glob("*.html"):
            shutil.copy(f, out_dir / f.name)
    else:
        shutil.rmtree(work)


if __name__ == "__main__":
    main()
