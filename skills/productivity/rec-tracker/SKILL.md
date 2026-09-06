---
name: "rec-tracker"
description: "Track recs from people/discoveries; rank by recommender."
version: "v1.4"
date: "2026-09-05"
---

# Recommendation Tracker

Track recommendations from friends/family AND things Mike discovers on his own. Log what you want to consume, rate it after, and get suggestions ranked by predicted enjoyment. One queue, one system — no separate watchlist needed.

## Storage

- **Data file:** `~/.hermes/workspace/rec-tracker/recommendations.json` (default) — array of recommendation entries
- **Script:** `scripts/rec-tracker.py` — all operations via CLI
- **Override the data file** (e.g. for testing against a different dataset): pass `--data-file <path>` as an argument anywhere in the command, or set the `REC_TRACKER_FILE` env var. Precedence: `--data-file` flag > `REC_TRACKER_FILE` env var > default path.

## Entry shape

```json
{
  "id": "rec-001",
  "title": "The Three-Body Problem",
  "type": "book",
  "recommended_by": [
    {"name": "Alice", "date_received": "2026-07-24", "notes": "She said it blew her mind"},
    {"name": "Bob", "date_received": "2026-07-28", "notes": ""}
  ],
  "from": "Alice",
  "source": "recommendation",
  "date_received": "2026-07-24",
  "notes": "She said it blew her mind",
  "location": "Sacramento",
  "tags": ["hard-sci-fi", "space"],
  "url": "https://...",
  "status": "pending",
  "consumed_date": null,
  "rating": null,
  "review": ""
}
```

### Multiple recommenders

`recommended_by` is a list of `{name, date_received, notes}` objects. When someone recommends a title that already exists (matched by title + type, case-insensitive), they're appended to the list instead of creating a duplicate entry. The `from` field is kept as a backward-compat alias for the first recommender.

All recommenders get credit in stats and leaderboards when the entry is rated. For `suggest`, the highest recommender's adjusted score is used as the predicted score.

### Sources

- **`recommendation`** — someone else recommended it to Mike (`recommended_by` contains one or more people)
- **`discovery`** — Mike found it on his own (`recommended_by` contains `self`)

Both live in the same file, same queue. Discoveries are excluded from recommender stats/leaderboard by default (they'd just rank yourself, which isn't useful).

## Types

`movie`, `tv`, `book`, `recipe`, `restaurant`, `album`, `podcast`, `game`, `activity`, `other`

The type field is freeform — any string works. The list above is just what's been used so far. New types are accepted automatically, no registration needed.

## Commands

All via `python3 scripts/rec-tracker.py <command> [args]` with `|` as argument separator. Add `--data-file <path>` anywhere to point at a non-default data file.

### Log a recommendation (from someone else)

```
add <title> | <from> | <type> | [notes] | [location] | [tags:comma,separated] | [url]
```

### Log a personal discovery

```
discover <title> | <type> | [notes] | [location] | [tags:comma,separated] | [url]
```

Shortcut for `add` with `from="self"`. Use this for anything Mike finds on his own — a movie he stumbled across, a restaurant he walked past, a book he saw reviewed.

### Mark consumed + rate

```
done <title-or-id> | <rating 1-5> | [review]
```

### Skip (decided not to consume)

```
skip <title-or-id> | [reason]
```

### Get suggestions (ranked by predicted score)

```
suggest [type] [limit] [location] [tags:comma,separated]
```

Returns pending recs ordered by recommender's adjusted score, optionally filtered by location and tags. Discoveries get a neutral predicted score (global type average).

### Recommender stats

```
stats [person] [--include-self]
```

Shows avg rating, count, adjusted score (Bayesian), and confidence per type. Excludes `self` by default; pass `--include-self` to include Mike's own ratings.

### Leaderboard by type

```
leaderboard [type] [--include-self]
```

### List / filter

```
list [status] [type] [location] [tags:comma,separated]
pending [type] [location] [tags:comma,separated]
```

### Search across all fields

```
search <query>
```

Searches title, notes, location, tags, recommender name, and review text.

### Migrate old entries

```
migrate
```

Migrates old entries to the current format: adds `recommended_by` list from legacy `from` field, adds missing `source`, `location`, `tags`, `url` fields. Safe to run repeatedly — only changes entries that need it.

## Scoring

Bayesian shrinkage: `adjusted = (count / (count + 3)) * avg + (3 / (count + 3)) * global_type_avg`

- Low count → shrinks toward global average for that type
- High count → reflects recommender's true average
- Confidence: low (<2), medium (2-4), high (5+)
- Discoveries (`self`) are excluded from scoring — they get the global type average as predicted score
- Multi-recommender entries credit all recommenders in stats/leaderboard

## Natural language triggers

When Mike says things like:
- "Alice recommended a book called X" → add (infer type and location from context)
- "Bob also recommends X" → add (merges into existing entry — no duplicate)
- "I found a movie called X" / "I want to watch X" / "I came across X" → discover (infer type and tags from context)
- "I just watched X, give it 4 stars" → done
- "What should I watch tonight?" → suggest
- "How good is Alice at recommending books?" → stats Alice
- "Who's the best at movie recommendations?" → leaderboard movie
- "Skip X, not interested" → skip
- "Show me recommendations near Tahoe" → list with location filter
- "What has Greg recommended?" → search Greg
- "Any breakfast spots pending?" → list pending restaurant breakfast (via tags)
- "What's on my watchlist?" → pending

Parse the intent, extract fields (including location and tags from context), run the script. Don't ask for confirmation on simple adds/discovers/dones — just do it and confirm what was recorded. When adding or discovering, try to extract location and relevant tags from the conversation context.
