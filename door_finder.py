#!/usr/bin/env python3
"""door_finder.py - list independent cafes, juice bars, health-food stores, delis and grocers
near any place, using only free OpenStreetMap services. No API keys, standard library only.

  python door_finder.py --city "Asheville, NC" --radius-mi 10 --out doors.csv
  python door_finder.py --lat 35.5951 --lon -82.5515 --radius-mi 15 --out doors.csv

What it does: geocodes the place (Nominatim), asks Overpass for shops in the categories below,
drops obvious chains, and writes a CSV with whatever contact info OpenStreetMap has.

What it does not do: OpenStreetMap coverage is uneven and only a minority of shops carry an
email, so treat the output as a list of candidates. Check each shop's website or call before
you pitch, and verify any email address before you send to it.

Both services have fair-use limits. This makes one geocode request and one Overpass request
per run; do not loop it over hundreds of towns.
"""
import argparse
import csv
import json
import math
import sys
import urllib.parse
import urllib.request

UA = "indie-door-finder/1.0 (https://github.com/robbydslilgreens-bit/indie-door-finder)"
OVERPASS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
NOMINATIM = "https://nominatim.openstreetmap.org/search"

# (osm key, osm value, label)
CATEGORIES = [
    ("amenity", "cafe", "cafe"),
    ("amenity", "juice_bar", "juice bar"),
    ("shop", "health_food", "health food store"),
    ("shop", "deli", "deli"),
    ("shop", "greengrocer", "greengrocer"),
    ("shop", "farm", "farm shop"),
    ("shop", "organic", "organic store"),
    ("shop", "convenience", "convenience / corner store"),
    ("shop", "supermarket", "grocer"),
]
DEFAULT_SKIP = {"convenience", "supermarket"}  # noisy and chain-heavy; opt in with --broad

# Lowercase substrings that mark a national or regional chain. Extend as you find more.
CHAINS = [
    "starbucks", "dunkin", "peet", "tim hortons", "mcdonald", "subway", "7-eleven", "7 eleven",
    "wawa", "sheetz", "circle k", "speedway", "shell", "exxon", "chevron", "bp ", "cvs", "walgreens",
    "walmart", "target", "kroger", "safeway", "publix", "aldi", "lidl", "whole foods", "trader joe",
    "food lion", "giant", "harris teeter", "costco", "sam's club", "family dollar", "dollar general",
    "dollar tree", "panera", "tropical smoothie", "smoothie king", "jamba", "einstein", "caribou",
    "coffee bean", "dutch bros", "scooter", "biggby", "krispy kreme", "wegmans", "stop & shop",
    "meijer", "h-e-b", "heb ", "albertsons", "vons", "sprouts", "fresh market", "earth fare",
]


def get(url, data=None, timeout=70):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def geocode(place):
    q = urllib.parse.urlencode({"q": place, "format": "json", "limit": 1})
    hits = get(f"{NOMINATIM}?{q}")
    if not hits:
        sys.exit(f"Could not geocode {place!r}. Try --lat/--lon instead.")
    return float(hits[0]["lat"]), float(hits[0]["lon"])


def overpass(lat, lon, radius_m, cats):
    parts = []
    for key, val, _ in cats:
        parts.append(f'nwr["{key}"="{val}"](around:{radius_m},{lat},{lon});')
    query = "[out:json][timeout:50];(" + "".join(parts) + ");out center tags;"
    body = urllib.parse.urlencode({"data": query}).encode()
    last = None
    for url in OVERPASS:
        try:
            return get(url, data=body)["elements"]
        except Exception as e:  # fall through to the next mirror
            last = e
    sys.exit(f"Overpass request failed on every mirror: {last}")


def is_chain(tags):
    if tags.get("brand") or tags.get("brand:wikidata") or tags.get("operator:wikidata"):
        return True
    name = (tags.get("name") or "").lower()
    return any(c in name for c in CHAINS)


def miles(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 3958.8 * 2 * math.asin(math.sqrt(a))


def address(t):
    street = " ".join(x for x in (t.get("addr:housenumber"), t.get("addr:street")) if x)
    return ", ".join(x for x in (street, t.get("addr:city"), t.get("addr:state"), t.get("addr:postcode")) if x)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--city", help='place name, e.g. "Asheville, NC"')
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--radius-mi", type=float, default=10, help="search radius in miles (default 10)")
    ap.add_argument("--broad", action="store_true", help="also include convenience stores and supermarkets")
    ap.add_argument("--out", default="doors.csv")
    a = ap.parse_args()

    if a.city:
        lat, lon = geocode(a.city)
    elif a.lat is not None and a.lon is not None:
        lat, lon = a.lat, a.lon
    else:
        ap.error("give --city or both --lat and --lon")

    cats = [c for c in CATEGORIES if a.broad or c[1] not in DEFAULT_SKIP]
    labels = {(k, v): lab for k, v, lab in CATEGORIES}
    els = overpass(lat, lon, int(a.radius_mi * 1609.34), cats)

    rows, seen = [], set()
    for e in els:
        t = e.get("tags", {})
        name = t.get("name")
        if not name or is_chain(t):
            continue
        clat = e.get("lat") or e.get("center", {}).get("lat")
        clon = e.get("lon") or e.get("center", {}).get("lon")
        key = (name.lower(), round(clat or 0, 3), round(clon or 0, 3))
        if key in seen:
            continue
        seen.add(key)
        cat = next((labels[(k, t[k])] for k, _, _ in cats if (k, t.get(k)) in labels), "")
        rows.append({
            "name": name,
            "category": cat,
            "address": address(t),
            "phone": t.get("phone") or t.get("contact:phone") or "",
            "website": t.get("website") or t.get("contact:website") or "",
            "email": t.get("email") or t.get("contact:email") or "",
            "miles_away": round(miles(lat, lon, clat, clon), 1) if clat else "",
            "osm_url": f"https://www.openstreetmap.org/{e['type']}/{e['id']}",
        })
    rows.sort(key=lambda r: (r["miles_away"] == "", r["miles_away"]))

    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["name"])
        w.writeheader()
        w.writerows(rows)

    with_email = sum(1 for r in rows if r["email"])
    with_site = sum(1 for r in rows if r["website"])
    print(f"{len(rows)} independent candidates within {a.radius_mi:g} mi -> {a.out}")
    print(f"  {with_site} list a website, {with_email} list an email in OpenStreetMap")


if __name__ == "__main__":
    main()
