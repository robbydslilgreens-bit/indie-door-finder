#!/usr/bin/env python3
"""contact_routes.py - label each row of a door_finder.py CSV by how you could actually reach it.

  python contact_routes.py doors.csv --out doors-routes.csv

Adds two columns:
  contact_route  email | website | phone-only | none   (best route OpenStreetMap gave us)
  email_domain_mx  yes | no | unknown | ""            (does the email's domain accept mail?)

The MX check asks Cloudflare's public DNS-over-HTTPS endpoint (one small request per distinct
email domain), so it needs no packages and no keys. It is a first filter only: a domain that
accepts mail says nothing about whether that mailbox exists, or whether a person reads it.
Run a real verifier before you send, and find the buyer's name before you write.
"""
import argparse
import csv
import json
import sys
import urllib.parse
import urllib.request

DOH = "https://cloudflare-dns.com/dns-query"
UA = "indie-door-finder/1.1 (https://github.com/robbydslilgreens-bit/indie-door-finder)"


def has_mx(domain):
    """'yes' / 'no' / 'unknown' (lookup failed - do not treat as 'no')."""
    url = DOH + "?" + urllib.parse.urlencode({"name": domain, "type": "MX"})
    req = urllib.request.Request(url, headers={"accept": "application/dns-json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.load(r)
    except Exception:
        return "unknown"
    if data.get("Status") == 3:  # NXDOMAIN
        return "no"
    if data.get("Status") != 0:
        return "unknown"
    return "yes" if any(a.get("type") == 15 for a in data.get("Answer", [])) else "no"


def route(row):
    if (row.get("email") or "").strip():
        return "email"
    if (row.get("website") or "").strip():
        return "website"
    if (row.get("phone") or "").strip():
        return "phone-only"
    return "none"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_in")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.csv_in, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    cache = {}
    for row in rows:
        row["contact_route"] = route(row)
        email = (row.get("email") or "").strip()
        row["email_domain_mx"] = ""
        if email and "@" in email:
            dom = email.rsplit("@", 1)[1].lower()
            if dom not in cache:
                cache[dom] = has_mx(dom)
            row["email_domain_mx"] = cache[dom]

    fields = list(rows[0]) if rows else ["name"]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    counts = {}
    for row in rows:
        counts[row["contact_route"]] = counts.get(row["contact_route"], 0) + 1
    print(f"{len(rows)} rows -> {args.out}")
    for k in ("email", "website", "phone-only", "none"):
        print(f"  {k}: {counts.get(k, 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
