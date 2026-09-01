# Karussell-Vorlage (Instagram)

Erzeugt mehrteilige Karussell-Posts im gleichen Design wie die Wochenposts
unter `../images/KW-*/`: 1080x1080, Inter, Silber-/Anthrazit-Headlines,
schwarze Datenkarte auf dunklem Verlauf, Wortmarke oben links bzw. unten.

Die Layout-Tokens in `render.py` (Raender, Schriftgroessen, Kartenmasse,
Farben) sind an `../images/KW-36/*.jpg` abgemessen, die Wortmarke ist aus
demselben Export freigestellt (`assets/wordmark-*.png`).

## Nutzung

```bash
pip install pillow
python3 carousel/render.py fun-trader          # -> carousel/out/fun-trader/01..07.jpg
python3 carousel/render.py prop-firm           # -> carousel/out/prop-firm/01..07.jpg
python3 carousel/render.py reset-loop          # -> carousel/out/reset-loop/01..06.jpg
python3 carousel/render.py trade-four          # -> carousel/out/trade-four/01..06.jpg
python3 carousel/render.py fourth-trade        # -> carousel/out/fourth-trade/01..07.jpg
python3 carousel/render.py fun-trader --keep-html   # HTML der Slides mit ausgeben
CHROME=/pfad/zu/chrome python3 carousel/render.py fun-trader
```

Gerendert wird mit headless Chrome; unter macOS wird Google Chrome automatisch
gefunden, sonst `CHROME=` setzen. Neben den JPGs entsteht `caption.txt` mit
dem Text fuer den Post.

## Neue Story anlegen

`stories/<name>.json` kopieren und Texte/Zahlen austauschen. Aufbau:

```jsonc
{
  "id": "ordnername-in-out",
  "caption": "Text fuer Instagram",
  "slides": [ ... 6-7 Slides ... ]
}
```

Slide-Typen:

- **`statement`** - reine Textkarte. `theme` `light` oder `dark`, `align`
  `left` (Wortmarke unten rechts) oder `center` (Wortmarke unten mittig),
  `lines` als Array (jede Zeile ein Eintrag, kein automatischer Umbruch),
  optional `cue` fuer den Swipe-Hinweis auf Slide 1.
- **`metric`** - dunkle Karte mit Daten, `headline` plus `card`:
  - `kind: "donut"` - Ring mit Win Rate und drei Werten darunter.
  - `kind: "bars"` - zwei Balken (gruen/rot) plus drei Kacheln.
  - `kind: "hero"` - grosse Summe, Kurve, drei Kacheln (wie der Performance-Post).
  - `kind: "rows"` - Liste: Name, Chip (`chip` frei oder `count`), Betrag.
    `highlight: true` hebt eine Zeile rot hinterlegt hervor (z. B. der Trade,
    um den es geht). Ab vier Zeilen ruecken die Zeilen automatisch enger.
  - `kind: "calendar"` - Monatsraster wie im Kalender-Post: `kpis` (vier
    Werte oben), `offset` (Leerzellen vor dem Ersten) und `days` mit
    `n`/`amount`/`highlight`; `amount: null` = handelsfreier Tag.
    Kalender-Slides bekommen automatisch die groessere Karte und die
    Wortmarke unten rechts.
  - `tone: "green"|"red"` faerbt einzelne Werte ein.
- **`number`** - eine einzige grosse Zahl mit Eyebrow darueber und einer
  Zeile darunter (`label`, `value`, `size`, `sub`). Fuer minimale Slides
  ohne Karte.
- **`split`** - zwei Zahlen nebeneinander, getrennt von einer Haarlinie
  (`items` mit `label`/`value`, optional `tone` und `foot`).
- **`cta`** - Abschlussslide mit Headline, gruener Zeile und Wortmarke.

`"counter": false` auf Story-Ebene blendet den `01 / 07`-Zaehler aus - fuer
sehr reduzierte Stories.

`note` setzt die kleine Zeile am unteren Rand - fuer Beispielzahlen bitte
gesetzt lassen (`Product example - figures illustrate the feature, not real
trader results.`), analog zu den Captions der Wochenposts.

Zeilen werden **nicht** automatisch umbrochen: bei mehr als ~19 Zeichen pro
Zeile warnt `render.py` und die Zeile gehoert manuell geteilt.

## Veroeffentlichen

`publish.py` postet bisher nur Einzelbilder. Fuer ein Karussell braucht die
Graph API pro Bild einen Container mit `is_carousel_item=true` und danach
einen Container mit `media_type=CAROUSEL` und `children=<ids>`; die JPGs
lassen sich wie die Wochenbilder ueber GitHub Pages ausliefern. Bis das
eingebaut ist: Bilder in der Reihenfolge `01..07` manuell hochladen,
`caption.txt` als Text.
