#!/usr/bin/env python3
"""Keep only reviews posted inside the report window.

Usage: filter_reviews.py RAW.json OUT.json [--hours 48] [--now ISO8601]

RAW.json is the review export for the place: either a list of places with a
"reviews_data" list, or a plain list of reviews. Each review needs
"review_timestamp" (unix seconds) or "review_datetime_utc".
"""
import argparse
import json
from datetime import datetime, timedelta, timezone


def parse_time(review):
    if review.get("review_timestamp"):
        return datetime.fromtimestamp(int(review["review_timestamp"]), timezone.utc)
    raw = review.get("review_datetime_utc", "")
    for fmt in ("%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def collect(data):
    """Flatten whatever shape the export came in to a list of reviews."""
    if isinstance(data, dict):
        data = data.get("data", [data])
    reviews = []
    for item in data:
        if isinstance(item, list):
            reviews.extend(collect(item))
        elif isinstance(item, dict) and "reviews_data" in item:
            reviews.extend(item["reviews_data"] or [])
        elif isinstance(item, dict):
            reviews.append(item)
    return reviews


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw")
    ap.add_argument("out")
    ap.add_argument("--hours", type=int, default=48)
    ap.add_argument("--now", help="window end, ISO 8601 (default: now)")
    args = ap.parse_args()

    end = datetime.fromisoformat(args.now) if args.now else datetime.now(timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    start = end - timedelta(hours=args.hours)

    with open(args.raw) as f:
        reviews = collect(json.load(f))

    kept, seen = [], set()
    for r in reviews:
        t = parse_time(r)
        rid = r.get("review_id") or (r.get("author_title"), r.get("review_timestamp"))
        if t is None or not (start <= t <= end) or rid in seen:
            continue
        seen.add(rid)
        kept.append({
            "review_id": r.get("review_id"),
            "author": r.get("author_title") or "Guest",
            "rating": r.get("review_rating"),
            "datetime_utc": t.isoformat(),
            "text": (r.get("review_text") or "").replace("<br>", "\n"),
            "owner_answer": r.get("owner_answer"),
        })
    kept.sort(key=lambda r: r["datetime_utc"], reverse=True)

    out = {
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "count": len(kept),
        "reviews": kept,
    }
    with open(args.out, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"{len(kept)} of {len(reviews)} reviews in window {start:%d %b %H:%M} – {end:%d %b %H:%M} UTC")


if __name__ == "__main__":
    main()
