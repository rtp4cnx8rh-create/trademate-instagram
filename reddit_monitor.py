#!/usr/bin/env python3
"""
Sucht taeglich passende Reddit-Threads und legt ein Briefing mit
Kommentarentwuerfen ab. Der Monitor postet NICHTS - er hat bewusst nur
Lesezugriff. Kommentiert wird von Hand.

Warum so herum: ein Bot, der automatisch Kommentare absetzt, ist in fremden
Subreddits Spam, fliegt schnell auf und kann die Domain sub-weit sperren.
Ein Mensch, der taeglich fuenf vorbereitete Threads vorgelegt bekommt und
selbst antwortet, ist zulaessig - und kann auf Rueckfragen reagieren.

Vorausgesetzt wird, dass das Reddit-Profil in der Bio offenlegt, dass du
TradeMate baust. Die Entwuerfe nennen das Produkt deshalb nie von sich aus;
wer wissen will, wer da schreibt, sieht es am Profil, und auf eine direkte
Nachfrage antwortest du selbst.

Umgebungsvariablen:
    REDDIT_CLIENT_ID       aus https://www.reddit.com/prefs/apps ("script"-App)
    REDDIT_CLIENT_SECRET   dito
    ANTHROPIC_API_KEY      optional - ohne ihn gibt es das Briefing ohne Entwuerfe
    GITHUB_TOKEN           optional - nur fuer --issue

Aufruf:
    python3 reddit_monitor.py                 # normaler Lauf
    python3 reddit_monitor.py --dry-run       # nur ausgeben, nichts schreiben
    python3 reddit_monitor.py --check         # nur Zugangsdaten pruefen
    python3 reddit_monitor.py --no-draft      # ohne Kommentarentwuerfe
    python3 reddit_monitor.py --issue         # zusaetzlich GitHub-Issue anlegen
"""

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "reddit_watch.json"
STATE = ROOT / "answered.json"
BRIEFINGS = ROOT / "briefings"

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API = "https://oauth.reddit.com"

# Reddit erlaubt 100 Requests pro Minute. Wir brauchen eine Handvoll,
# die Pause ist reine Hoeflichkeit gegenueber der API.
PAUSE = 1.0

# Wie lange ein einmal gemeldeter Thread als "schon gesehen" gilt.
STATE_TAGE = 60


# ---------------------------------------------------------------- Reddit-API

def user_agent(cfg: dict) -> str:
    # Reddit verlangt einen aussagekraeftigen User-Agent und drosselt
    # generische Strings ("python-urllib") hart.
    name = cfg.get("reddit_username", "unknown")
    return f"script:trademate-reddit-monitor:v1.0 (by /u/{name})"


def reddit_token(cfg: dict) -> str:
    cid = os.environ.get("REDDIT_CLIENT_ID", "").strip()
    secret = os.environ.get("REDDIT_CLIENT_SECRET", "").strip()
    if not cid or not secret:
        sys.exit("REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET fehlen.")

    basic = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Basic {basic}",
            "User-Agent": user_agent(cfg),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())["access_token"]
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:400]
        sys.exit(f"Token-Abruf fehlgeschlagen ({e.code}): {body}")


def reddit_get(path: str, params: dict, token: str, cfg: dict) -> dict:
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": user_agent(cfg),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:400]
        print(f"  ! {path} -> HTTP {e.code}: {body}", file=sys.stderr)
        return {}


# ---------------------------------------------------------------- Auswahl

def relevanz(post: dict, keywords: list) -> tuple:
    """Zaehlt Keyword-Treffer in Titel und Text. Titel zaehlt doppelt."""
    titel = post.get("title", "").lower()
    text = post.get("selftext", "").lower()
    treffer = []
    punkte = 0
    for kw in keywords:
        k = kw.lower()
        if k in titel:
            punkte += 2
            treffer.append(kw)
        elif k in text:
            punkte += 1
            treffer.append(kw)
    return punkte, treffer


def passt(post: dict, f: dict, jetzt: datetime) -> str:
    """Gibt den Ablehnungsgrund zurueck, oder '' wenn der Post durchkommt."""
    if post.get("locked") or post.get("archived"):
        return "gesperrt"
    if post.get("stickied"):
        return "angepinnt"
    if post.get("over_18"):
        return "nsfw"
    if not post.get("is_self"):
        return "kein Textpost"

    alter = jetzt - datetime.fromtimestamp(post.get("created_utc", 0), timezone.utc)
    if alter > timedelta(hours=f["max_alter_stunden"]):
        return f"zu alt ({alter.days}d {alter.seconds // 3600}h)"
    if post.get("score", 0) < f["min_score"]:
        return f"zu wenig Score ({post.get('score', 0)})"
    if post.get("num_comments", 0) > f["max_kommentare"]:
        return f"zu viele Kommentare ({post.get('num_comments')})"
    if len(post.get("selftext", "")) < f["min_text_zeichen"]:
        return "Text zu kurz"
    return ""


def suchen(cfg: dict, token: str, gesehen: set) -> list:
    subs = "+".join(cfg["subreddits"])
    f = cfg["filter"]
    jetzt = datetime.now(timezone.utc)
    kandidaten = {}
    verworfen = 0

    for query in cfg["queries"]:
        antwort = reddit_get(
            f"/r/{subs}/search",
            {
                "q": query,
                "restrict_sr": "on",
                "sort": "new",
                "t": "week",
                "limit": 25,
                "raw_json": 1,
            },
            token,
            cfg,
        )
        kinder = antwort.get("data", {}).get("children", [])
        print(f"  '{query}': {len(kinder)} Treffer")

        for kind in kinder:
            post = kind.get("data", {})
            pid = post.get("id")
            if not pid or pid in kandidaten or pid in gesehen:
                continue
            grund = passt(post, f, jetzt)
            if grund:
                verworfen += 1
                continue
            punkte, treffer = relevanz(post, cfg["keywords"])
            if punkte == 0:
                verworfen += 1
                continue
            post["_punkte"] = punkte
            post["_treffer"] = sorted(set(treffer))
            post["_query"] = query
            kandidaten[pid] = post

        time.sleep(PAUSE)

    print(f"  {len(kandidaten)} Kandidaten, {verworfen} durch Filter gefallen")
    sortiert = sorted(
        kandidaten.values(),
        key=lambda p: (p["_punkte"], p.get("score", 0)),
        reverse=True,
    )
    return sortiert[: f["pro_lauf"]]


# ---------------------------------------------------------------- Entwurf

SYSTEM = """Du entwirfst Reddit-Kommentare fuer den Gruender von {produkt}, {beschreibung}.

Sein Reddit-Profil legt in der Bio offen, dass er {produkt} baut. Der Kommentar
selbst ist deshalb reine Fachantwort - er wirbt nicht.

Harte Regeln:
- Nenne {produkt} NIE. Kein Produktname, kein Link, kein "ein Tool, das ich kenne",
  keine Andeutung eines Tools. Wer nachfragt, bekommt die Antwort spaeter von ihm
  persoenlich - nicht aus diesem Entwurf.
- Beantworte die tatsaechliche Frage des Posts. Substanz vor Freundlichkeit.
- Sprache: {sprache}. Hoechstens {max_woerter} Woerter.
- Ton: ein erfahrener Trader, der kurz antwortet. Kein Lob-Einstieg
  ("Great post!", "This is so relatable"), keine Emojis, keine Hashtags,
  kein Coaching-Sprech, keine Aufzaehlung von Binsenweisheiten.
- Konkret werden: Zahlen, ein Beispiel, eine Unterscheidung, die der Poster
  noch nicht gemacht hat. Wenn du nichts Konkretes beizutragen hast, sag das
  nicht - dann antworte gar nicht.
- Keine Heilsversprechen und keine Renditeversprechen.

Wenn der Thread keine substanzielle Fachantwort hergibt (reines Venting, Meme,
Kontostand-Flex, Frage nach Signalen), antworte ausschliesslich mit: SKIP"""


def entwurf(post: dict, cfg: dict) -> str:
    """Kommentarentwurf ueber die Claude-API. Leerer String = kein Entwurf."""
    try:
        import anthropic
    except ImportError:
        return ""

    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        return ""

    e = cfg["entwurf"]
    system = SYSTEM.format(
        produkt=e["produkt"],
        beschreibung=e["produkt_beschreibung"],
        sprache=e["sprache"],
        max_woerter=e["max_woerter"],
    )
    text = post.get("selftext", "")
    if len(text) > 2500:
        text = text[:2500] + " [...]"

    frage = (
        f"Subreddit: r/{post.get('subreddit')}\n"
        f"Titel: {post.get('title')}\n\n"
        f"Post:\n{text}\n\n"
        "Entwirf den Kommentar. Nur den Kommentartext, keine Vorrede."
    )

    try:
        client = anthropic.Anthropic()
        antwort = client.messages.create(
            model="claude-opus-5",
            max_tokens=4000,
            system=system,
            thinking={"type": "adaptive"},
            output_config={"effort": "medium"},
            messages=[{"role": "user", "content": frage}],
        )
    except Exception as fehler:                     # noqa: BLE001
        print(f"  ! Entwurf fehlgeschlagen: {fehler}", file=sys.stderr)
        return ""

    if antwort.stop_reason == "refusal":
        return ""
    roh = "".join(b.text for b in antwort.content if b.type == "text").strip()
    return "" if roh.strip().upper().startswith("SKIP") else roh


# ---------------------------------------------------------------- Ausgabe

def kuerzen(text: str, zeichen: int = 600) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    if len(text) <= zeichen:
        return text
    return text[:zeichen].rsplit(" ", 1)[0] + " [...]"


def briefing(posts: list, cfg: dict, mit_entwurf: bool) -> str:
    heute = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    zeilen = [
        f"# Reddit-Briefing {heute}",
        "",
        "Gelesen, nicht gepostet. Kommentieren machst du selbst - der Monitor hat",
        "keine Schreibrechte.",
        "",
        f"**Vor dem ersten Kommentar pruefen:** steht in der Bio von /u/{cfg['reddit_username']}, "
        f"dass du {cfg['entwurf']['produkt']} baust? Wenn nein, zuerst eintragen. "
        "Die Entwuerfe nennen das Produkt bewusst nicht - die Offenlegung haengt am Profil.",
        "",
    ]

    if not posts:
        zeilen += ["Heute nichts Passendes. Kein Grund, etwas zu erzwingen.", ""]
        return "\n".join(zeilen)

    for i, post in enumerate(posts, 1):
        alter = datetime.now(timezone.utc) - datetime.fromtimestamp(
            post["created_utc"], timezone.utc
        )
        stunden = int(alter.total_seconds() // 3600)
        zeilen += [
            "---",
            "",
            f"## {i}. {post['title']}",
            "",
            f"r/{post['subreddit']} - {stunden}h alt - {post.get('score', 0)} Punkte - "
            f"{post.get('num_comments', 0)} Kommentare - Treffer: {', '.join(post['_treffer'])}",
            "",
            f"https://www.reddit.com{post['permalink']}",
            "",
            "> " + kuerzen(post.get("selftext", "")).replace("\n", "\n> "),
            "",
        ]
        if mit_entwurf:
            text = post.get("_entwurf", "")
            if text:
                zeilen += ["**Entwurf:**", "", "```", text, "```", ""]
            else:
                zeilen += [
                    "**Entwurf:** keiner - entweder gibt der Thread fachlich nichts her "
                    "oder die Claude-API war nicht erreichbar. Selbst entscheiden.",
                    "",
                ]

    zeilen += [
        "---",
        "",
        "Entwuerfe sind Entwuerfe. Lies den Thread, bevor du etwas abschickst, und",
        "schreib um, was nicht nach dir klingt. Wenn jemand nach einem Tool fragt,",
        "antworte offen und als du selbst.",
        "",
    ]
    return "\n".join(zeilen)


def issue_anlegen(titel: str, koerper: str) -> None:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not token or not repo:
        print("  ! GITHUB_TOKEN/GITHUB_REPOSITORY fehlen - kein Issue angelegt.")
        return

    data = json.dumps({"title": titel, "body": koerper}).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "trademate-reddit-monitor",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"  Issue angelegt: {json.loads(r.read().decode())['html_url']}")
    except urllib.error.HTTPError as e:
        print(f"  ! Issue fehlgeschlagen ({e.code}): "
              f"{e.read().decode(errors='replace')[:300]}", file=sys.stderr)


# ---------------------------------------------------------------- Zustand

def state_laden() -> dict:
    if not STATE.exists():
        return {"gesehen": {}}
    return json.loads(STATE.read_text())


def state_speichern(state: dict) -> None:
    grenze = (datetime.now(timezone.utc) - timedelta(days=STATE_TAGE)).strftime("%Y-%m-%d")
    state["gesehen"] = {
        pid: eintrag
        for pid, eintrag in state["gesehen"].items()
        if eintrag.get("datum", "") >= grenze
    }
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- Ablauf

def main() -> None:
    p = argparse.ArgumentParser(description="Reddit-Monitor fuer TradeMate (nur lesend).")
    p.add_argument("--dry-run", action="store_true", help="nichts schreiben, nur ausgeben")
    p.add_argument("--check", action="store_true", help="nur Zugangsdaten pruefen")
    p.add_argument("--no-draft", action="store_true", help="ohne Kommentarentwuerfe")
    p.add_argument("--issue", action="store_true", help="Briefing als GitHub-Issue anlegen")
    args = p.parse_args()

    cfg = json.loads(CONFIG.read_text())
    token = reddit_token(cfg)

    if args.check:
        antwort = reddit_get("/r/" + cfg["subreddits"][0] + "/about", {}, token, cfg)
        name = antwort.get("data", {}).get("display_name_prefixed", "?")
        print(f"Token ok. Zugriff auf {name} bestaetigt.")
        if cfg["reddit_username"] == "DEIN_REDDIT_NAME":
            print("! reddit_username in reddit_watch.json ist noch der Platzhalter.")
        return

    state = state_laden()
    gesehen = set(state["gesehen"])
    print(f"Suche in r/{'+'.join(cfg['subreddits'])} ({len(gesehen)} Threads bereits gemeldet)")

    posts = suchen(cfg, token, gesehen)

    mit_entwurf = not args.no_draft
    if mit_entwurf:
        for post in posts:
            post["_entwurf"] = entwurf(post, cfg)
            print(f"  Entwurf {'ok' if post['_entwurf'] else 'uebersprungen'}: "
                  f"{post['title'][:60]}")

    text = briefing(posts, cfg, mit_entwurf)
    heute = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if args.dry_run:
        print("\n" + text)
        return

    BRIEFINGS.mkdir(exist_ok=True)
    ziel = BRIEFINGS / f"{heute}.md"

    # Zweiter Lauf am selben Tag: alles Gefundene steht schon in answered.json,
    # der Lauf faende also nichts und wuerde ein gutes Briefing leer ueberschreiben.
    if not posts and ziel.exists():
        print(f"Nichts Neues - {ziel.name} bleibt unveraendert.")
        return

    ziel.write_text(text)
    print(f"Briefing geschrieben: {ziel.relative_to(ROOT)}")

    for post in posts:
        state["gesehen"][post["id"]] = {
            "datum": heute,
            "subreddit": post["subreddit"],
            "titel": post["title"][:120],
        }
    state_speichern(state)

    zusammenfassung = os.environ.get("GITHUB_STEP_SUMMARY")
    if zusammenfassung:
        Path(zusammenfassung).write_text(text)

    if args.issue and posts:
        issue_anlegen(f"Reddit-Briefing {heute} ({len(posts)} Threads)", text)


if __name__ == "__main__":
    main()
