# Trademate Fast-Cut-Reels (Remotion)

Zwei Kompositionen (30 fps) aus den woechentlichen Figma-Exporten unter
`../images/KW-*/`, jeweils in drei Seitenverhaeltnissen:

- **TrademateReel** (~6,5 s): zwei Text-Hooks, danach schnelle Cuts mit
  Punch-Zoom durch alle Motive der Woche, am Ende eine CTA-Endcard.
- **TrademateRapid** (~3,5 s): nur die App-UI, keine Text-Hooks. Karten- und
  Detail-Ausschnitte (Zahlen, Chart, Kalenderzellen, Ratios) als harte
  Jump-Cuts in einem Bezel-Rahmen, kurzer Wortmarken-Abbinder. Die
  Ausschnitt-Rechtecke in `src/TrademateRapid.tsx` sind Pixelkoordinaten in
  den Quellbildern und muessen fuer neue Wochen auf die neuen Motive
  angepasst werden.

## Formate

Jede Komposition existiert dreimal (siehe `src/formats.ts`):

| Composition-ID | Aufloesung | Verwendung |
| --- | --- | --- |
| `TrademateReel` / `TrademateRapid` | 1080x1920 (9:16) | Reels, Stories, TikTok |
| `...-Square` | 1080x1080 (1:1) | Instagram-Feed |
| `...-Wide` | 1920x1080 (16:9) | YouTube, Website, Meta-Ads-Placement |

Das Layout skaliert mit dem Format: das quadratische Motiv im Reel und der
Bezel-Rahmen im Rapid-Clip werden aus der Videogroesse berechnet, das
9:16-Ergebnis bleibt unveraendert.

## Nutzung

```bash
cd video
npm install
npm run render                 # TrademateReel 9:16, Ausgabe: out/trademate-reel.mp4
npm run render:rapid           # TrademateRapid 9:16, Ausgabe: out/trademate-rapid.mp4
npm run render:all             # alle sechs Varianten nach out/*-{9x16,1x1,16x9}.mp4
WEEK=KW-35 npm run render      # bestimmte Woche statt der neuesten
npm run dev                    # Remotion Studio (Vorschau im Browser)
```

In Umgebungen ohne Chrome-Download (z. B. der Cloud-Container) den lokalen
Browser mitgeben:
`npx remotion render <ID> <Datei> --browser-executable=<pfad-zu-chrome>`.

`npm run render` kopiert vorher automatisch die Bilder der Woche und die
Inter-Fonts nach `public/` (siehe `scripts/sync-assets.mjs`). Neue Wochen
brauchen keine Codeaenderung: Ordner `images/KW-XX/` anlegen, fertig.

Timing und Look liegen in `src/TrademateReel.tsx` (`INTRO_BEAT`,
`CUT_DURATION`, `OUTRO_DURATION` in Frames bei 30 fps), Farben in
`src/theme.ts`.

Das Reel ist bewusst ohne Musik gerendert - Musik am besten direkt in
Instagram ueber die Sound-Library legen, das hilft der Reichweite und
vermeidet Lizenzfragen.

Hinweis: `publish.py` veroeffentlicht bisher nur Bild-Posts. Fuer Reels
braeuchte es einen eigenen Schritt (Graph API `media` mit `media_type=REELS`
und `video_url`); die gerenderte Datei laesst sich dafuer wie die Bilder ueber
GitHub Pages ausliefern.
