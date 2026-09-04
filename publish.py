#!/usr/bin/env python3
"""
Veroeffentlicht die faelligen Trademate-Instagram-Beitraege ueber die Graph API.

Verarbeitet werden Feed-Posts (schedule.json -> "posts") und Stories
(schedule.json -> "stories"). Beides laeuft ueber denselben Zweischritt aus
Media-Container und media_publish, Stories brauchen zusaetzlich
media_type=STORIES.

Laeuft in GitHub Actions, taeglich. Das Skript entscheidet selbst, ob gerade
etwas ansteht - der Cron feuert bewusst zweimal (Sommer-/Winterzeit), und nur
der Lauf, bei dem es in Berlin wirklich die Zielstunde ist, macht etwas.

Umgebungsvariablen:
    IG_USER_ID        Instagram-Professional-Account-ID (NICHT der @username)
    IG_ACCESS_TOKEN   Long-Lived Access Token
    IG_API_HOST       optional, Standard: graph.instagram.com
                      - graph.instagram.com  -> Business Login for Instagram
                      - graph.facebook.com   -> Facebook Login for Business

Aufruf:
    python3 publish.py                 # normaler Lauf
    python3 publish.py --dry-run       # zeigt nur, was passieren wuerde
    python3 publish.py --check         # prueft Token und Kontozugriff
    python3 publish.py --force 2026-08-24   # bestimmten Tag nachholen
    python3 publish.py --refresh-token      # Token um 60 Tage verlaengern
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

API_VERSION = "v25.0"
HOST = os.environ.get("IG_API_HOST", "graph.instagram.com").strip()
ROOT = Path(__file__).resolve().parent
SCHEDULE = ROOT / "schedule.json"
STATE = ROOT / "published.json"

# Meta empfiehlt, den Container-Status hoechstens minuetlich und nicht laenger
# als 5 Minuten abzufragen. Bei Einzelbildern ist er meist sofort FINISHED.
POLL_VERSUCHE = 10
POLL_PAUSE = 20


def api(method: str, path: str, params: dict) -> dict:
    url = f"https://{HOST}/{API_VERSION}/{path}"
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        url = f"{url}?{data.decode()}"
        req = urllib.request.Request(url, method="GET")
    else:
        req = urllib.request.Request(url, data=data, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            err = json.loads(body).get("error", {})
            msg = err.get("message", body)
            code = err.get("code", e.code)
            raise SystemExit(f"Graph-API-Fehler {code}: {msg}")
        except json.JSONDecodeError:
            raise SystemExit(f"Graph-API-Fehler {e.code}: {body}")


def load_state() -> set:
    if STATE.is_file():
        return set(json.loads(STATE.read_text()).get("published", []))
    return set()


def save_state(done: set):
    STATE.write_text(
        json.dumps({"published": sorted(done)}, indent=2) + "\n", encoding="utf-8"
    )


# Stories laufen ueber denselben Endpunkt wie Feed-Posts, brauchen aber
# media_type=STORIES. Eine Story-Caption zeigt Instagram nicht an, deshalb
# wird sie beim Container gar nicht erst mitgeschickt.
def alle_eintraege(plan: dict) -> list:
    """Alle geplanten Termine als (art, eintrag), Stories vor Feed-Posts."""
    eintraege = []
    for art, schluessel in (("story", "stories"), ("post", "posts")):
        for e in plan.get(schluessel, []):
            eintraege.append((art, e))
    return sorted(eintraege, key=lambda ae: (ae[1]["date"], ae[1]["hour"]))


def faellige_eintraege(plan: dict, jetzt: datetime, force: str | None) -> list:
    treffer = []
    for art, e in alle_eintraege(plan):
        if force:
            if e["date"] == force:
                treffer.append((art, e))
        # Nicht auf die exakte Stunde pruefen: GitHub-Cron ist regelmaessig
        # zwei bis vier Stunden verspaetet, dann waere die Zielstunde laengst
        # vorbei und der Termin fiele still aus. Stattdessen: alles ab der
        # Zielstunde am selben Tag zaehlt als faellig. Gegen Doppelposts
        # schuetzt published.json weiter unten, nicht das Zeitfenster.
        elif e["date"] == jetzt.date().isoformat() and jetzt.hour >= e["hour"]:
            treffer.append((art, e))
    return treffer


def zustands_schluessel(plan: dict, art: str, eintrag: dict) -> str:
    """Schluessel fuer published.json.

    Feed-Posts behalten ihr altes Format "<Woche>:<Datum>", damit bereits
    veroeffentlichte Tage nicht erneut gepostet werden. Ein Eintrag darf mit
    "week" eine abweichende Woche setzen - so laesst sich ein einzelner Termin
    der Folgewoche an den laufenden Plan haengen.
    """
    woche = eintrag.get("week", plan["week"])
    if art == "story":
        return f"{woche}:story:{eintrag['date']}"
    return f"{woche}:{eintrag['date']}"


def veroeffentliche(user_id: str, token: str, art: str, eintrag: dict) -> str:
    params = {"image_url": eintrag["image_url"], "access_token": token}
    if art == "story":
        params["media_type"] = "STORIES"
    else:
        params["caption"] = eintrag["caption"]

    container = api("POST", f"{user_id}/media", params)
    creation_id = container["id"]
    print(f"Container {creation_id} angelegt, warte auf Verarbeitung...")

    # Warten bis Meta das Bild geholt und verarbeitet hat.
    for _ in range(POLL_VERSUCHE):
        st = api(
            "GET",
            creation_id,
            {"fields": "status_code,status", "access_token": token},
        )
        code = st.get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            sys.exit(f"Container fehlgeschlagen: {st.get('status')}")
        time.sleep(POLL_PAUSE)
    else:
        sys.exit("Container wurde nicht rechtzeitig fertig. Nichts veroeffentlicht.")

    res = api(
        "POST",
        f"{user_id}/media_publish",
        {"creation_id": creation_id, "access_token": token},
    )
    return res.get("id", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--force", metavar="YYYY-MM-DD")
    ap.add_argument("--refresh-token", action="store_true")
    args = ap.parse_args()

    user_id = os.environ.get("IG_USER_ID", "").strip()
    token = os.environ.get("IG_ACCESS_TOKEN", "").strip()

    if not user_id or not token:
        sys.exit("IG_USER_ID und IG_ACCESS_TOKEN muessen gesetzt sein.")

    if args.refresh_token:
        if HOST != "graph.instagram.com":
            sys.exit(
                "--refresh-token gilt nur fuer Business Login for Instagram.\n"
                "Beim Facebook-Login-Weg mit System-User-Token entfaellt das Verlaengern."
            )
        res = api(
            "GET",
            "refresh_access_token",
            {"grant_type": "ig_refresh_token", "access_token": token},
        )
        tage = int(res.get("expires_in", 0)) // 86400
        print(f"Token verlaengert, laeuft in {tage} Tagen ab.")
        print("Neuen Token als Secret IG_ACCESS_TOKEN hinterlegen:")
        print(res.get("access_token", ""))
        return

    if args.check:
        info = api("GET", user_id, {"fields": "username,name", "access_token": token})
        print(f"Host:      {HOST}")
        print(f"Zugriff OK auf @{info.get('username')} ({info.get('name')})")
        limit = api(
            "GET",
            f"{user_id}/content_publishing_limit",
            {"access_token": token},
        )
        try:
            used = limit["data"][0].get("quota_usage")
            print(f"Publishing-Kontingent: {used} von 100 in den letzten 24 h")
        except (KeyError, IndexError):
            pass
        return

    if not SCHEDULE.is_file():
        sys.exit(f"schedule.json fehlt ({SCHEDULE}). Erst prepare_week.py laufen lassen.")

    plan = json.loads(SCHEDULE.read_text(encoding="utf-8"))
    tz = ZoneInfo(plan.get("timezone", "Europe/Berlin"))
    jetzt = datetime.now(tz)

    faellig = faellige_eintraege(plan, jetzt, args.force)

    if not faellig:
        print(
            f"Nichts faellig. Lokale Zeit {jetzt:%Y-%m-%d %H:%M %Z}, "
            f"Plan {plan['week']}."
        )
        # Damit im Log sofort sichtbar ist, WARUM nichts passt.
        print(f"  --force war: {args.force!r}")
        print(f"  Heute:       {jetzt.date().isoformat()}, Stunde {jetzt.hour}")
        print("  Termine im Plan:")
        for art, e in alle_eintraege(plan):
            print(f"    {e['date']} {e['hour']:02d}:00  {art:5s}  {Path(e['file']).name}")
        if not args.force:
            print(
                "  Hinweis: ohne --force zaehlt ein Termin erst ab seiner "
                "Zielstunde am selben Kalendertag."
            )
        return

    done = load_state()

    # Ein Lauf kann mehrere Termine abarbeiten - an einem Tag stehen Story und
    # Feed-Post nebeneinander, und der Cron startet fuer beide nur einmal.
    for art, eintrag in faellig:
        key = zustands_schluessel(plan, art, eintrag)
        if key in done and not args.force:
            print(f"{key} wurde bereits veroeffentlicht. Uebersprungen.")
            continue

        if not eintrag.get("image_url"):
            sys.exit(
                f"Kein image_url fuer {art} {eintrag['date']}. "
                "prepare_week.py mit --base-url laufen lassen."
            )

        erste = eintrag.get("caption", "").split("\n")[0]
        kurz = erste if len(erste) <= 90 else erste[:87] + "..."
        print(f"\nFaellig: {art} {eintrag['date']} {eintrag['hour']:02d}:00")
        print(f"Bild:    {eintrag['image_url']}")
        if kurz:
            print(f"Hook:    {kurz}")

        if args.dry_run:
            print("--dry-run: es wurde nichts gesendet.")
            continue

        media_id = veroeffentliche(user_id, token, art, eintrag)
        print(f"Veroeffentlicht. Media-ID {media_id}")
        done.add(key)
        save_state(done)


if __name__ == "__main__":
    main()
