# Major update poll — carousel + story

Carousel: 7 slides, 1080×1080. Story: 1080×1920, with a marked zone for the
native poll sticker (`*_guide.jpg` shows where it goes, post the clean file).
Both in EN and DE.

## Carousel caption (EN)

Day trading and swing trading keep the same journal and ask it completely
different questions. Thirty entries a day means the visual record is the
thing that goes missing — our own M8 data puts screenshot coverage at 0.77%.
Six trades a month means the sample is the thing that goes missing — about
seventeen months to reach a hundred trades on one setup.

Two features would close those gaps, and both are on the roadmap for the
next major update. One of them ships first. Backtesting runs a tagged setup
across years of price history before real money. Auto charts attach the chart
to every trade the moment it closes, entry to exit, no screenshots.

Comment A for backtesting, B for auto charts — or vote in today's story.

Product concept: the panels shown are planned features, not final UI.

#tradingjournal #daytrading #swingtrading #backtesting #tradinganalytics

## Carousel caption (DE)

Daytrading und Swingtrading führen dasselbe Journal und stellen ihm völlig
verschiedene Fragen. Dreißig Entries am Tag heißt: Das Bild zum Trade ist das,
was fehlt — unsere eigenen M8-Daten zeigen 0,77 % Screenshot-Abdeckung. Sechs
Trades im Monat heißt: Die Stichprobe ist das, was fehlt — rund siebzehn
Monate bis hundert Trades auf einem Setup.

Zwei Funktionen würden diese Lücken schließen, beide stehen auf der Roadmap
für das nächste Major Update. Eine davon kommt zuerst. Backtesting lässt ein
getaggtes Setup über Jahre Kurshistorie laufen, bevor echtes Geld im Spiel
ist. Auto-Charts hängen jedem Trade seinen Chart an, sobald er schließt —
Entry bis Exit, ohne Screenshot.

Kommentar A für Backtesting, B für Auto-Charts — oder stimm in der heutigen
Story ab.

Produktkonzept: Die gezeigten Panels sind geplante Funktionen, kein finales UI.

#tradingjournal #daytrading #swingtrading #backtesting #tradinganalytics

## Story

Place the native poll sticker in the dashed zone of the guide file:
- EN: "Which ships first?" · Backtesting / Auto charts
- DE: "Was kommt zuerst?" · Backtesting / Auto-Charts

Link the carousel from the story (Post sticker) so the vote and the deep dive
point at each other.

## Re-rendering

Needs the same toolchain as `video/m8-ai` (Node + playwright-core, Chromium,
the Inter/Inter Tight faces installed). `node render.js` writes all 18 files
to `out/`; `node render.js story` or `node render.js _de` limits the run.
All copy lives in the `C` object in `post.html`.
