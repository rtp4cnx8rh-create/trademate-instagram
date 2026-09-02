# Reddit-Monitor

Sucht taeglich Threads in Trading-Subreddits, die zu TradeMates Themen passen,
und legt sie mit Kommentarentwuerfen unter `briefings/` ab. Du liest, du
entscheidest, du kommentierst.

**Der Monitor postet nichts.** Die Reddit-App bekommt bewusst nur Lesezugriff.
Ein Bot, der automatisch in fremden Subreddits kommentiert, ist dort Spam:
Shadowban ist der Normalfall, und im schlimmeren Fall wird `trademate-app.com`
sub-weit gesperrt - dann kann auch kein echter Nutzer den Link mehr posten.

## Einmalige Einrichtung

**1. Reddit-App anlegen** unter <https://www.reddit.com/prefs/apps> ->
"create another app...", Typ **script**, Redirect-URI `http://localhost:8080`
(wird nicht benutzt). Du bekommst eine Client-ID (unter dem App-Namen) und ein
Secret.

**2. GitHub-Secrets setzen** (Settings -> Secrets and variables -> Actions):

| Secret | Pflicht | Wofuer |
|---|---|---|
| `REDDIT_CLIENT_ID` | ja | Reddit-App |
| `REDDIT_CLIENT_SECRET` | ja | Reddit-App |
| `ANTHROPIC_API_KEY` | nein | Kommentarentwuerfe; ohne ihn kommt das Briefing ohne Entwuerfe |

**3. Profil-Bio setzen.** In der Bio des Reddit-Kontos, mit dem du antwortest,
muss stehen, dass du TradeMate baust - z.B. *"Trader, baue nebenbei TradeMate
(Trading-Journal)."* Darauf ist alles andere aufgebaut: die Entwuerfe nennen das
Produkt nie, weil die Offenlegung am Profil haengt. Ohne den Bio-Eintrag waeren
es Werbekommentare, die sich als neutrale Fachbeitraege ausgeben.

**4. `reddit_watch.json` anpassen** - mindestens `reddit_username`, sonst
drosselt Reddit den User-Agent.

**5. Testlauf:** Actions -> "Reddit Monitor" -> Run workflow, mit
`check_only = true`. Danach einmal mit `dry_run = true`.

## Taeglicher Ablauf

Der Workflow laeuft um 06:00 UTC. Er schreibt `briefings/YYYY-MM-DD.md` ins Repo
und legt dasselbe als GitHub-Issue an, damit du eine Benachrichtigung bekommst.
Pro Tag maximal fuenf Threads - die Grenze ist Absicht, nicht Sparsamkeit.

Fuer jeden Thread bekommst du Link, Alter, Score, die getroffenen Keywords, einen
Auszug und den Entwurf. Vor dem Abschicken:

- **Thread lesen.** Der Entwurf kennt nur den Ausgangspost, nicht die Antworten
  darunter. Steht deine Antwort da schon, lass es.
- **Umschreiben, was nicht nach dir klingt.** Ein Kommentar, den du nicht selbst
  formuliert haettest, faellt in Trading-Subs auf.
- **Auf Rueckfragen selbst antworten.** Fragt jemand, womit du trackst, sag es
  offen und als du selbst. Genau dafuer gibt es die Bio.

Threads, die einmal im Briefing standen, landen in `answered.json` und kommen
nicht wieder - unabhaengig davon, ob du geantwortet hast. Nach 60 Tagen wird
aufgeraeumt.

## Schrauben

Alles Einstellbare steht in `reddit_watch.json`:

- `subreddits` / `queries` - wo und wonach gesucht wird
- `keywords` - nur fuer die Reihenfolge im Briefing, nicht fuer die Suche
- `filter` - Alter, Mindest-Score, maximale Kommentarzahl, Textlaenge,
  Threads pro Lauf. Kommt zu wenig durch, zuerst `min_score` senken und
  `max_alter_stunden` erhoehen.
- `entwurf` - Sprache, Laenge, Produktbeschreibung fuer den Entwurfstext

Lokal testen ohne irgendetwas zu schreiben:

```bash
export REDDIT_CLIENT_ID=... REDDIT_CLIENT_SECRET=...
python3 reddit_monitor.py --check
python3 reddit_monitor.py --dry-run --no-draft
```
