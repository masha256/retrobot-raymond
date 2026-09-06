---
name: situational-safety-monitoring
description: "Watch fires/outages near user; alert only on real change."
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [wildfire, power-outage, evacuation, emergency, disaster, weather, safety, monitoring, cronjob]
    related_skills: [product-price-monitor, competitor-news-monitor, maps]
---

# Situational Safety Monitoring

Track a live, fast-moving physical-safety situation (wildfire, power outage,
storm, flood, evacuation zone) that affects a user's actual or planned
location, and report only meaningful changes. This is the safety-event
sibling of `product-price-monitor` and `competitor-news-monitor` — same
cron + state-file + silent-unless-changed shape, but the domain is physical
risk to the user, not commerce or business intel, so source hierarchy and
staleness handling are different and matter more.

## When to Use

- "Is there a fire near me / where I'm traveling?"
- "Watch this wildfire/storm/outage and tell me if anything changes."
- User is physically in or traveling through an area with an active
  wildfire, PSPS (public safety power shutoff), storm, flood, or
  evacuation order.
- A cron tick fires for an existing safety watch.

Don't use for: general news curiosity about a disaster far from the user,
or a one-off "what's the latest on X" lookup with no ongoing user exposure
(just answer directly with `web_search`).

## Source Hierarchy (critical — aggregators lie stale)

Official incident/utility sources update in near-real-time during an active
event; general aggregators that cache/poll periodically can be badly stale
and contradict the primary source without any indication they're behind.

1. **Incident command / government fire tracker** — e.g. CAL FIRE incident
   page, county Sheriff's Office / OES page, `emergencywashoe.com`-style
   regional emergency operations center pages. These carry containment %,
   acreage, and evacuation zone status directly from unified command.
2. **Utility's own outage alert channel** — the utility's own X/Twitter
   account and `<utility>.org/electric-outage-information` page, not a
   third-party aggregator. A utility's own "OUTAGE ALERT" posts are the
   ground truth for restoration status.
3. **Local TV/wire stories with explicit timestamped updates** (e.g. "Aug
   22, 11:00pm update") — good for cross-checking acreage/containment
   trend, but always check the update time, not just the headline.
4. **Third-party outage aggregators (poweroutage.us and similar)** — useful
   as a rough cross-check ONLY. Verified failure mode observed in practice:
   showed "0 customers out / 0%, last updated 13h ago" for a utility whose
   own live alert said "ALL customers out of power" posted more recently.
   Never report an aggregator's number as current without checking its
   own "last updated" timestamp against the primary source's most recent
   post — and prefer the primary source when they disagree.

When sources disagree (e.g. two outlets give different acreage, or a cached
site contradicts the official one), say so explicitly rather than picking
one silently — surface the discrepancy and flag which figure is likely
freshest based on timestamps.

## Procedure — Setup (foreground, once)

### 1. Pin the situation and the user's exposure

Record: event name/location, why it matters to the user (physically
present, traveling through, property in area), and the specific facts that
matter — containment/acreage for fire, restoration status for outages,
evacuation zone name/boundary for evacuations. Note the user's itinerary/
timeline if traveling (dates, route) so alerts can be judged against it.

### 2. Establish a baseline, then schedule

Do one live foreground check across the source hierarchy above before
scheduling. Then create the cron job:

```
cronjob(action="create",
        schedule="every 30m",   # tighter for fast-moving fire/evac, looser for a resolved-but-monitored outage
        continuity=true,
        deliver=<user's destination>,
        enabled_toolsets=["web"],
        prompt="Check <event> via <hierarchy above>. Compare to prior known
                state: <baseline>. Only message the user if there is a
                MEANINGFUL CHANGE: containment/acreage shifts significantly,
                evacuation orders expand/change/lift, power outage status
                changes, or new areas are threatened relevant to the user's
                location/route. Prefer the utility's own alerts over
                aggregators; if sources disagree, say so and flag the
                freshest one by timestamp. If nothing meaningful changed,
                stay silent.")
```

`continuity=true` lets each tick compare against its own last output
instead of drifting; embedding the explicit "stay silent unless meaningful
change" instruction in the prompt (not just relying on model judgment) is
what keeps this from turning into alert spam every 30 minutes.

## Procedure — Tick / on-demand check

### 3. Check the hierarchy in order, note timestamps

Pull incident-command page, utility's own channel, and 1-2 timestamped news
updates. Record the update time on each — a 13-hour-old "0% outage" beats
nothing, but a same-hour "ALL customers out" from the utility itself wins.

### 4. Compare to baseline / last report

Only surface: containment or acreage change large enough to matter,
evacuation order/warning boundary change, restoration or new outage, or a
newly threatened area relevant to the user. Trivial noise (acreage revised
by a few dozen acres, a "still active" restatement) is not a meaningful
change.

### 5. Deliver or stay silent

When reporting, always give: the figure, its timestamp/recency, the source,
and explicit uncertainty flags where sources disagree. Never assert
containment, restoration, or evacuation status as settled fact if the only
evidence is a stale aggregator — say so and point to how to verify directly
(utility phone line, official map site) for anything safety-critical and
time-sensitive enough that being wrong matters.

## Pitfalls

- Trusting a third-party outage aggregator over the utility's own posted
  alert without checking either one's timestamp.
- Treating "not mentioned in latest search results" as "resolved" — absence
  of a fresh update is not confirmation of an all-clear.
- Alerting every tick regardless of whether anything changed (defeats the
  purpose — embed the silence rule explicitly in the cron prompt, don't
  assume the model will infer it).
- Reporting conflicting acreage/containment numbers from different outlets
  as if they agree — flag the discrepancy.
- Forgetting to stop the monitor once the user's exposure ends (they leave
  the area, event fully resolved) — ask or confirm before leaving a safety
  cron running indefinitely.

## Verification

- [ ] Baseline check happened in foreground before scheduling.
- [ ] Cron prompt explicitly instructs silence unless meaningful change —
      not left implicit.
- [ ] Source hierarchy followed: incident command / utility direct >
      timestamped news > aggregator-as-cross-check-only.
- [ ] Any cross-source disagreement is surfaced, not silently resolved.
- [ ] User told directly to verify via official channel when the situation
      is safety-critical and current data is uncertain or stale.
