#!/usr/bin/env python3
"""
Veroeffentlicht den faelligen Trademate-Instagram-Post ueber die Graph API.

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

    faellig = None
    for p in plan["posts"]:
        if args.force:
            if p["date"] == args.force:
                faellig = p
                break
        elif p["date"] == jetzt.date().isoformat() and p["hour"] == jetzt.hour:
            faellig = p
            break

    if not faellig:
        print(
            f"Nichts faellig. Lokale Zeit {jetzt:%Y-%m-%d %H:%M %Z}, "
            f"Plan {plan['week']}."
        )
        return

    key = f"{plan['week']}:{faellig['date']}"
    done = load_state()
    if key in done and not args.force:
        print(f"{key} wurde bereits veroeffentlicht. Nichts zu tun.")
        return

    if not faellig.get("image_url"):
        sys.exit(f"Kein image_url fuer {faellig['date']}. prepare_week.py mit --base-url laufen lassen.")

    erste = faellig["caption"].split("\n")[0]
    kurz = erste if len(erste) <= 90 else erste[:87] + "..."
    print(f"Faellig: {faellig['date']} {faellig['hour']:02d}:00")
    print(f"Bild:    {faellig['image_url']}")
    print(f"Hook:    {kurz}")

    if args.dry_run:
        print("\n--dry-run: es wurde nichts gesendet.")
        return

    # Schritt 1: Media-Container anlegen
    container = api(
        "POST",
        f"{user_id}/media",
        {
            "image_url": faellig["image_url"],
            "caption": faellig["caption"],
            "access_token": token,
        },
    )
    creation_id = container["id"]
    print(f"Container {creation_id} angelegt, warte auf Verarbeitung...")

    # Schritt 2: warten bis Meta das Bild geholt und verarbeitet hat
    for versuch in range(POLL_VERSUCHE):
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

    # Schritt 3: veroeffentlichen
    res = api(
        "POST",
        f"{user_id}/media_publish",
        {"creation_id": creation_id, "access_token": token},
    )

    print(f"Veroeffentlicht. Media-ID {res.get('id')}")
    done.add(key)
    save_state(done)


if __name__ == "__main__":
    main()
