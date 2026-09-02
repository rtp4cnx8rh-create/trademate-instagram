# M8 AI — Instagram Story / Reel

Animated product explainer for M8 AI, built in code so it can be re-rendered
with new numbers, new copy or a new language without touching a design tool.

| File | Format | Use |
|---|---|---|
| `m8_story_en.mp4` | 1080×1920, 15.0 s, 30 fps, H.264 | Story / Reel (EN) |
| `m8_story_de.mp4` | 1080×1920, 15.0 s, 30 fps, H.264 | Story / Reel (DE) |
| `m8_cover_en.jpg` / `m8_cover_de.jpg` | 1080×1920 | Reel cover (full frame) |
| `m8_cover_feed_en.jpg` / `m8_cover_feed_de.jpg` | 1080×1350 | Reel cover, feed crop |
| `captions.md` | — | Captions EN/DE, sticker text, on-screen script |

## Design

Same system as the daily feed posts: charcoal gradient ground, the Trademate
lockup at the top, headline in Inter Tight 800 with a white→grey vertical
ramp, dark cards with a hairline border, `#1FDD7F` green and a classic
`#C62A30` / `#DC3A40` red for result values. The phone screen is a code
rebuild of the app's dashboard — same layout, wording and trade rows as the
in-app screen, rendered at 1080 px wide instead of screen-recorded. It carries
the first two scenes and then hands over to the finding cards, so the second
half runs on type and cards alone.

The dashboard figures (130 trades, 55 %, 2.17, the recent-trade rows) are the
ones from the reference screens. The findings use rounded illustrative
amounts — -$1,500 / +$900 / +$800 — and the M8 AI card on the phone teases the
same 12:00 finding the story then blows up, so no two screens show the same
hour with different numbers. Everything is labelled as a product example on
screen from 6.4 s onward.

## Re-rendering

Requires Node with `playwright-core`, a Chromium build, Python with `Pillow`
and an ffmpeg with libx264 (`pip install imageio-ffmpeg`). The Inter and
Inter Tight faces in `src/fonts` (SIL Open Font License) must be installed
for the system so Chromium can resolve them.

```
cd src
cp fonts/*.ttf ~/.fonts/ && fc-cache -f
node render.js en          # writes frames_en/0000.png … 0449.png
./encode.sh en ../m8_story_en.mp4
```

`node render.js en preview 0.8,4.2,8.6` renders single frames at the given
timestamps instead of the full sequence — the fast way to check a change.

To change copy, edit the `COPY` object in `src/story.html`; both languages and
all on-screen strings live there. To change timing, edit the `T` table and the
`seg(t, …)` ranges in `render(t)` — one function drives the whole 15 s.
