# Orion disclosure watcher — brainstorm brief (Mike + Raymond, 2026-10-23)

## Goal
When a protocol publishes something material (investor call, tokenomics/burn/policy post), Orion notices it, reads it,
compares the claims with what Orion measures, and files changes for Mike's approval. Never changes anything on its own.
Motivating example: Lighter Q3 2026 investor call (video only) -> manual review found 3 issues, now in
../dev-queue-revenue.md ("LIT — Robinhood revenue share, revenue source, unlock cadence").

## Decisions (Mike)
1. Scope v1: LIT only (pilot), generalize to other assets after.
2. Outputs split by type: value changes -> Orion proposals (inbox); code/data-source work -> dev-queue entries.
3. Discovery: keyless, calendar-driven (no paid X API).
4. Architecture: option C (hybrid) below.

## Architecture C (chosen)
1. Hermes side, deterministic script, no LLM: discovery + download + local transcription.
   Daily in the 5 weeks after each quarter end, weekly otherwise; Mike can paste a link to trigger immediately.
2. Orion side (new, small): `orion doc add <asset> --url <post> --file <transcript>` stores text + sha256 + source URL +
   kind (e.g. machine_transcript). Citation verification accepts verbatim quotes from a stored doc as well as pages
   fetched in the run, labelled machine transcript (persona rule: founder figures are dated claims, not facts).
3. Script then triggers `orion agent run <asset> --type triage --note doc:<id>` (or a new `disclosure` run type — spec decides).
   The analyst compares claims vs Orion data, files proposals (assumption_value / config / observation) citing the doc,
   and records catalysts in its journal.
4. Findings that need code come out as structured "dev findings" in the run summary; the Hermes step appends them to the
   dev queue and posts a short digest to #orion-ops linking the inbox items.
Rejected: A (all Hermes — value changes bypass Orion inbox/citations/audit); B (all Orion — puts yt-dlp/ASR deps and fuzzy
web discovery into the TS valuation repo).

## Facts established 2026-10-23
- Lighter posts investor calls on X only (blog lighter.xyz/blog has 1 post, Aug 19 2026; no RSS; no YouTube channel).
  Pattern: announce post 1-3 days before, call, recording posted next day, 1-3 weeks after quarter end:
  Q1 call 2026-04-02 (rec 2039862458572001352, Apr 3); Q2 call 2026-07-02 (announce Jun 29, rec 2073044023661453589, Jul 3);
  Q3 call 2026-10-21 (announce 2111481510230675531, rec 2113065839352336774, Oct 22).
- Keyless X: profile page 403 logged out; syndication.twitter.com timeline-profile 429; nitter/xcancel dead.
  WORKS: single post by ID via https://cdn.syndication.twimg.com/tweet-result?id=<id>&token=a (text, created_at, media).
  WORKS: yt-dlp on the post URL (audio format hls-audio-64000-Audio, ~19MB for 41 min).
- Discovery sources that find the post IDs keylessly: web search ("Lighter Q<n> Investor Update call"), event calendars
  coincarp.com/events (lists source tweet ID), coindar.org.
- Transcription: faster-whisper small.en int8, 4 threads, ~5 min for 41.5 min audio on this host. Pitfall: PyAV version in a
  fresh venv rejects faster-whisper's `metadata_errors` kwarg -> decode with ffmpeg to 16k mono wav and pass a numpy array
  (see transcribe-reference.py). Name errors to expect: "LIDAR"/"LID" for Lighter/LIT.
- Orion agent facts: web_fetch-only citation check (src/agent/guardrails.ts, research.ts fetchedPagesFrom); proposal kinds in
  src/db/proposals.ts; run budgets src/config/agentPolicy.ts (triage: 20 req, 500k in, 8 fetches, 10 proposals);
  skill skills/disclosure-research.md; persona personas/perp-exchange-analyst.md; agent_runs.run_type CHECK constraint
  (adding a run type = migration). Avg triage run ~240-750k input tokens.
- Test fixture: lit-q3-2026-call-transcript.txt (this dir). Expected outcomes on it, from the manual review:
  config proposal for unlock cadence (monthly from 2027-01-29, not weekly from 2026-12-29); dev findings for the Robinhood
  50% share missing from holder flow and for DefiLlama revenue counting 100% of Robinhood fees; journal catalysts
  (CFTC DCM/DCO filing Nov 2026 + up to 180d; vanilla options + portfolio margin by YE; Lighter EVM mainnet by YE).
