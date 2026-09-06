#!/usr/bin/env python3
"""Recommendation tracker - query, score, and rank recommendations.

Supports two sources:
  - "recommendation": something someone else recommended to Mike
  - "discovery": something Mike found on his own (from="self")

Supports multiple recommenders per entry:
  - `recommended_by` is a list of {name, date_received, notes} objects
  - When someone recommends a title that already exists, they're appended
  - Stats and leaderboards credit all recommenders for an entry
"""

import json
import sys
import os
from datetime import datetime, date
from pathlib import Path

DEFAULT_DATA_FILE = str(Path.home() / ".hermes" / "workspace" / "rec-tracker" / "recommendations.json")


def _resolve_data_file(argv):
    """Resolve the data file path with precedence: --data-file flag > REC_TRACKER_FILE env var > default.
    Strips --data-file <path> out of argv in place and returns (path, cleaned_argv)."""
    cleaned = []
    path = os.environ.get("REC_TRACKER_FILE", DEFAULT_DATA_FILE)
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--data-file":
            if i + 1 >= len(argv):
                print("Usage: --data-file <path>")
                sys.exit(1)
            path = argv[i + 1]
            i += 2
            continue
        if arg.startswith("--data-file="):
            path = arg.split("=", 1)[1]
            i += 1
            continue
        cleaned.append(arg)
        i += 1
    return path, cleaned


DATA_FILE, _ = _resolve_data_file(sys.argv)

VALID_STATUSES = {"pending", "consumed", "skipped"}


def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def find_existing(data, title, rec_type):
    """Find an existing entry by title (case-insensitive) and type."""
    title_lower = title.lower()
    for e in data:
        if e["title"].lower() == title_lower and e["type"] == rec_type:
            return e
    return None


def add(title, from_person, rec_type, notes="", location="", tags=None, url=""):
    data = load_data()

    existing = find_existing(data, title, rec_type)
    if existing:
        names = [r["name"] for r in existing["recommended_by"]]
        if from_person not in names:
            existing["recommended_by"].append({
                "name": from_person,
                "date_received": date.today().isoformat(),
                "notes": notes
            })
            if location and not existing.get("location"):
                existing["location"] = location
            if tags:
                existing_tags = set(existing.get("tags") or [])
                existing_tags.update(tags)
                existing["tags"] = sorted(existing_tags)
            if url and not existing.get("url"):
                existing["url"] = url
            save_data(data)
            return existing
        else:
            return existing

    rec_id = f"rec-{len(data)+1:03d}"
    source = "discovery" if from_person == "self" else "recommendation"
    entry = {
        "id": rec_id,
        "title": title,
        "type": rec_type,
        "recommended_by": [
            {
                "name": from_person,
                "date_received": date.today().isoformat(),
                "notes": notes
            }
        ],
        "date_received": date.today().isoformat(),
        "notes": notes,
        "location": location,
        "tags": tags if tags else [],
        "url": url,
        "source": source,
        "status": "pending",
        "consumed_date": None,
        "rating": None,
        "review": ""
    }
    data.append(entry)
    save_data(data)
    return entry


def discover(title, rec_type, notes="", location="", tags=None, url=""):
    """Shortcut for add with from='self'. For things Mike finds on his own."""
    return add(title, "self", rec_type, notes, location, tags, url)


def mark_consumed(identifier, rating, review=""):
    data = load_data()
    entry = find_entry(data, identifier)
    if not entry:
        return None
    entry["status"] = "consumed"
    entry["consumed_date"] = date.today().isoformat()
    entry["rating"] = rating
    entry["review"] = review
    save_data(data)
    return entry


def skip(identifier, reason=""):
    data = load_data()
    entry = find_entry(data, identifier)
    if not entry:
        return None
    entry["status"] = "skipped"
    entry["review"] = reason
    save_data(data)
    return entry


def find_entry(data, identifier):
    for e in data:
        if e["id"] == identifier:
            return e
    identifier_lower = identifier.lower()
    matches = [e for e in data if identifier_lower in e["title"].lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        pending = [m for m in matches if m["status"] == "pending"]
        if pending:
            return pending[-1]
        return matches[-1]
    return None


def get_recommenders(entry):
    """Get list of recommender names from an entry (handles both old and new format)."""
    if "recommended_by" in entry:
        return [r["name"] for r in entry["recommended_by"]]
    return [entry.get("from", "self")] if entry.get("from") else []


def recommender_stats(data, person=None, include_self=False):
    """Compute adjusted scores per recommender per type using Bayesian shrinkage.
    Excludes 'self' entries by default unless include_self=True.
    Credits all recommenders for multi-recommender entries."""
    stats = {}
    type_averages = {}

    for e in data:
        if e["status"] != "consumed" or e["rating"] is None:
            continue
        recommenders = get_recommenders(e)
        for r in recommenders:
            if not include_self and r == "self":
                continue
            key = (r, e["type"])
            if key not in stats:
                stats[key] = {"ratings": [], "count": 0, "sum": 0}
            stats[key]["ratings"].append(e["rating"])
            stats[key]["count"] += 1
            stats[key]["sum"] += e["rating"]

        t = e["type"]
        if t not in type_averages:
            type_averages[t] = {"sum": 0, "count": 0}
        type_averages[t]["sum"] += e["rating"]
        type_averages[t]["count"] += 1

    global_avgs = {}
    for t, v in type_averages.items():
        global_avgs[t] = v["sum"] / v["count"] if v["count"] > 0 else 3.0

    PRIOR_WEIGHT = 3
    results = []
    for (person_name, rec_type), s in stats.items():
        if person and person_name.lower() != person.lower():
            continue
        if not include_self and person_name == "self":
            continue
        avg = s["sum"] / s["count"]
        global_avg = global_avgs.get(rec_type, 3.0)
        adjusted = (s["count"] / (s["count"] + PRIOR_WEIGHT)) * avg + \
                   (PRIOR_WEIGHT / (s["count"] + PRIOR_WEIGHT)) * global_avg
        results.append({
            "recommender": person_name,
            "type": rec_type,
            "avg_rating": round(avg, 2),
            "count": s["count"],
            "adjusted_score": round(adjusted, 2),
            "confidence": "high" if s["count"] >= 5 else "medium" if s["count"] >= 2 else "low"
        })

    results.sort(key=lambda x: x["adjusted_score"], reverse=True)
    return results


def suggest(data, rec_type=None, limit=5, location=None, tags=None):
    """Suggest pending recommendations, ranked by predicted score.
    Uses the best recommender's score for multi-recommender entries."""
    pending = [e for e in data if e["status"] == "pending"]
    if rec_type:
        pending = [e for e in pending if e["type"] == rec_type]
    if location:
        loc_lower = location.lower()
        pending = [e for e in pending if loc_lower in (e.get("location") or "").lower()]
    if tags:
        tag_set = set(t.lower() for t in tags)
        pending = [e for e in pending if tag_set & set(t.lower() for t in (e.get("tags") or []))]

    if not pending:
        return []

    stats = recommender_stats(data)

    score_map = {}
    for s in stats:
        score_map[(s["recommender"], s["type"])] = s["adjusted_score"]

    type_avgs = {}
    consumed = [e for e in data if e["status"] == "consumed" and e["rating"] is not None]
    type_groups = {}
    for e in consumed:
        if e["type"] not in type_groups:
            type_groups[e["type"]] = []
        type_groups[e["type"]].append(e["rating"])
    for t, ratings in type_groups.items():
        type_avgs[t] = sum(ratings) / len(ratings) if ratings else 3.0

    results = []
    for e in pending:
        recommenders = get_recommenders(e)
        non_self = [r for r in recommenders if r != "self"]
        if non_self:
            scores = [score_map.get((r, e["type"]), None) for r in non_self]
            valid_scores = [s for s in scores if s is not None]
            if valid_scores:
                predicted = max(valid_scores)
            else:
                predicted = type_avgs.get(e["type"], 3.0)
        else:
            predicted = type_avgs.get(e["type"], 3.0)

        results.append({
            "id": e["id"],
            "title": e["title"],
            "type": e["type"],
            "recommended_by": recommenders,
            "source": e.get("source", "recommendation"),
            "predicted_score": round(predicted, 2),
            "date_received": e.get("date_received", ""),
            "location": e.get("location", ""),
            "tags": e.get("tags", []),
            "notes": e.get("notes", "")
        })

    results.sort(key=lambda x: x["predicted_score"], reverse=True)
    return results[:limit]


def list_recs(data, status=None, rec_type=None, location=None, tags=None, source=None):
    results = data
    if status:
        results = [e for e in results if e["status"] == status]
    if rec_type:
        results = [e for e in results if e["type"] == rec_type]
    if location:
        loc_lower = location.lower()
        results = [e for e in results if loc_lower in (e.get("location") or "").lower()]
    if tags:
        tag_set = set(t.lower() for t in tags)
        results = [e for e in results if tag_set & set(t.lower() for t in (e.get("tags") or []))]
    if source:
        results = [e for e in results if e.get("source") == source]
    return results


def leaderboard(data, rec_type=None, include_self=False):
    stats = recommender_stats(data, include_self=include_self)
    if rec_type:
        stats = [s for s in stats if s["type"] == rec_type]
    return stats


def search(data, query):
    """Search across all fields: title, notes, location, tags, recommenders, review."""
    q_lower = query.lower()
    results = []
    for e in data:
        recommenders = get_recommenders(e)
        searchable = " ".join([
            e.get("title", ""),
            e.get("notes", ""),
            e.get("location", ""),
            " ".join(recommenders),
            " ".join(e.get("tags") or []),
            e.get("review", ""),
        ]).lower()
        if q_lower in searchable:
            results.append(e)
    return results


def migrate_entry(e):
    """Migrate old entry format to new format with recommended_by list."""
    changed = False

    if "recommended_by" not in e:
        from_person = e.get("from", "self")
        e["recommended_by"] = [{
            "name": from_person,
            "date_received": e.get("date_received", date.today().isoformat()),
            "notes": e.get("notes", "")
        }]
        changed = True
    else:
        for r in e["recommended_by"]:
            if "notes" not in r:
                r["notes"] = ""
                changed = True
            if "date_received" not in r:
                r["date_received"] = e.get("date_received", date.today().isoformat())
                changed = True

    if "from" not in e:
        e["from"] = e["recommended_by"][0]["name"] if e["recommended_by"] else "self"
        changed = True
    else:
        first_name = e["recommended_by"][0]["name"] if e["recommended_by"] else "self"
        if e["from"] != first_name:
            e["from"] = first_name
            changed = True

    if "location" not in e:
        e["location"] = ""
        changed = True
    if "tags" not in e:
        e["tags"] = []
        changed = True
    if "url" not in e:
        e["url"] = ""
        changed = True
    if "source" not in e:
        e["source"] = "discovery" if e.get("from") == "self" else "recommendation"
        changed = True

    return e, changed


def main():
    global DATA_FILE
    _, argv_no_flag = _resolve_data_file(sys.argv)
    raw_argv = [a for a in argv_no_flag if a != "|"]
    sys.argv = raw_argv

    if len(sys.argv) < 2:
        print("Usage: rec-tracker.py <command> [args...]")
        print("Commands: add, discover, done, skip, suggest, stats, leaderboard, list, pending, search, migrate")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "add":
        if len(sys.argv) < 5:
            print("Usage: add <title> | <from> | <type> | [notes] | [location] | [tags:comma,separated] | [url]")
            sys.exit(1)
        title = sys.argv[2]
        from_person = sys.argv[3]
        rec_type = sys.argv[4]
        notes = sys.argv[5] if len(sys.argv) > 5 else ""
        location = sys.argv[6] if len(sys.argv) > 6 else ""
        tags_str = sys.argv[7] if len(sys.argv) > 7 else ""
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
        url = sys.argv[8] if len(sys.argv) > 8 else ""
        entry = add(title, from_person, rec_type, notes, location, tags, url)
        print(json.dumps(entry, indent=2))

    elif cmd == "discover":
        if len(sys.argv) < 4:
            print("Usage: discover <title> | <type> | [notes] | [location] | [tags:comma,separated] | [url]")
            sys.exit(1)
        title = sys.argv[2]
        rec_type = sys.argv[3]
        notes = sys.argv[4] if len(sys.argv) > 4 else ""
        location = sys.argv[5] if len(sys.argv) > 5 else ""
        tags_str = sys.argv[6] if len(sys.argv) > 6 else ""
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
        url = sys.argv[7] if len(sys.argv) > 7 else ""
        entry = discover(title, rec_type, notes, location, tags, url)
        print(json.dumps(entry, indent=2))

    elif cmd == "done":
        if len(sys.argv) < 4:
            print("Usage: done <title-or-id> | <rating> | [review]")
            sys.exit(1)
        identifier = sys.argv[2]
        rating = int(sys.argv[3])
        review = sys.argv[4] if len(sys.argv) > 4 else ""
        entry = mark_consumed(identifier, rating, review)
        if entry:
            print(json.dumps(entry, indent=2))
        else:
            print(f"Not found: {identifier}")
            sys.exit(1)

    elif cmd == "skip":
        if len(sys.argv) < 3:
            print("Usage: skip <title-or-id> | [reason]")
            sys.exit(1)
        identifier = sys.argv[2]
        reason = sys.argv[3] if len(sys.argv) > 3 else ""
        entry = skip(identifier, reason)
        if entry:
            print(json.dumps(entry, indent=2))
        else:
            print(f"Not found: {identifier}")
            sys.exit(1)

    elif cmd == "suggest":
        rec_type = sys.argv[2] if len(sys.argv) > 2 else None
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        location = sys.argv[4] if len(sys.argv) > 4 else None
        tags_str = sys.argv[5] if len(sys.argv) > 5 else None
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else None
        data = load_data()
        data = [migrate_entry(e)[0] for e in data]
        save_data(data)
        results = suggest(data, rec_type, limit, location, tags)
        print(json.dumps(results, indent=2))

    elif cmd == "stats":
        person = None
        include_self = False
        for arg in sys.argv[2:]:
            if arg == "--include-self":
                include_self = True
            else:
                person = arg
        data = load_data()
        data = [migrate_entry(e)[0] for e in data]
        save_data(data)
        results = recommender_stats(data, person, include_self=include_self)
        print(json.dumps(results, indent=2))

    elif cmd == "leaderboard":
        rec_type = None
        include_self = False
        for arg in sys.argv[2:]:
            if arg == "--include-self":
                include_self = True
            else:
                rec_type = arg
        data = load_data()
        data = [migrate_entry(e)[0] for e in data]
        save_data(data)
        results = leaderboard(data, rec_type, include_self=include_self)
        print(json.dumps(results, indent=2))

    elif cmd == "list":
        status = sys.argv[2] if len(sys.argv) > 2 else None
        rec_type = sys.argv[3] if len(sys.argv) > 3 else None
        location = sys.argv[4] if len(sys.argv) > 4 else None
        tags_str = sys.argv[5] if len(sys.argv) > 5 else None
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else None
        data = load_data()
        data = [migrate_entry(e)[0] for e in data]
        save_data(data)
        results = list_recs(data, status, rec_type, location, tags)
        print(json.dumps(results, indent=2))

    elif cmd == "pending":
        rec_type = sys.argv[2] if len(sys.argv) > 2 else None
        location = sys.argv[3] if len(sys.argv) > 3 else None
        tags_str = sys.argv[4] if len(sys.argv) > 4 else None
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else None
        data = load_data()
        data = [migrate_entry(e)[0] for e in data]
        save_data(data)
        results = list_recs(data, "pending", rec_type, location, tags)
        print(json.dumps(results, indent=2))

    elif cmd == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        if not query:
            print("Usage: search <query>")
            sys.exit(1)
        data = load_data()
        data = [migrate_entry(e)[0] for e in data]
        save_data(data)
        results = search(data, query)
        print(json.dumps(results, indent=2))

    elif cmd == "migrate":
        data = load_data()
        changed = False
        for i, e in enumerate(data):
            e, entry_changed = migrate_entry(e)
            if entry_changed:
                changed = True
        if changed:
            save_data(data)
            print(f"Migrated {len(data)} entries to new format (with recommended_by).")
        else:
            print(f"All {len(data)} entries already in new format.")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
