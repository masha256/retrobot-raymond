---
name: google-api-troubleshooting
description: "Use when Google API calls 403 or hit the wrong calendar."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [google, oauth, gmail, calendar, drive, docs, sheets, 403, troubleshooting]
    category: productivity
    related_skills: [google-workspace]
---

# Google API Troubleshooting

Companion fixes for problems that show up *after* Google Workspace OAuth
(see the `google-workspace` skill for initial setup) succeeds but specific
calls still fail or silently return the wrong data. These are recurring
failure classes across any Google API integration, not one-off bugs.

## When to Use

- A Drive/Docs/Sheets call fails with `HttpError 403 ... SERVICE_DISABLED`
  even though OAuth completed and the scope was granted.
- Calendar `list`/`create`/`delete` against an account that's meant to act
  on a *different* person's calendar (a shared/delegate setup) returns
  empty results or writes to the wrong place with no error.
- `drive share --role owner` (or the equivalent raw Drive API call) fails
  with a `transferOwnership` or `sendNotificationEmail` 403.

## Fix 1: `SERVICE_DISABLED` after OAuth already succeeded

Granting an OAuth *scope* (e.g. `drive`, `documents`) during consent does
**not** auto-enable the underlying API in the Cloud Console project. The
first call to that API returns:

```
HttpError 403: <API name> has not been used in project <id> before or it
is disabled. Enable it by visiting
https://console.developers.google.com/apis/api/<api>.googleapis.com/overview?project=<id>
```

**Fix:** send the user the exact activation URL from the error message —
it's project- and API-specific, don't guess a generic Cloud Console link.
After they click Enable, **wait 1-2 minutes before retrying** — Google's
own error text says propagation takes a few minutes, and immediate retries
fail with the identical error, which can look like the fix didn't work.
If a user is setting up multiple services (e.g. Gmail + Calendar + Drive +
Docs), confirm *every* required API is enabled up front rather than
discovering them one at a time as each new call type is first used.

## Fix 2: Calendar commands hit the wrong (empty) calendar

Most calendar wrapper scripts default to the **authenticated account's own
primary calendar**. This is correct when the authenticated account IS the
user, but wrong for a common delegate pattern: a dedicated agent/service
account (e.g. an assistant persona's own mailbox) that the real user has
*shared their personal calendar with*, so the agent can read/write the
user's actual calendar rather than its own empty one.

**Fix:** always pass the target calendar explicitly by ID (the owner's
email address works as the calendar ID for a shared calendar) rather than
relying on the default:

```bash
$GAPI calendar list --calendar user@example.com
$GAPI calendar create --calendar user@example.com --summary "..." --start ... --end ...
$GAPI calendar delete EVENT_ID --calendar user@example.com
```

Omitting this silently succeeds against the wrong calendar — no error, just
empty results or events created somewhere the user never sees. If a
delegate/service-account setup is in play, treat the explicit calendar ID
as mandatory on every call, not optional.

## Fix 3: Drive ownership transfer (`role=owner`) 403 sequence

See `references/drive-ownership-transfer.md` for the exact two-step error
sequence and the code patch. Short version: the Drive API needs both
`transferOwnership=True` AND `sendNotificationEmail=True` set together for
a `role=owner` permission — most thin wrapper scripts only expose
`sendNotificationEmail` via a `--notify` flag and omit `transferOwnership`
entirely, so an owner-role share needs either an underlying script patch or
a raw API call with both parameters set.

Ownership transfer only works **within the same Google Workspace domain**
by default; transfers to an external consumer Gmail account are blocked by
Google outright — that's a platform limit, not something to patch around.

## Fix 4: All-day calendar events use an EXCLUSIVE end date

Google Calendar's all-day events (`start.date` / `end.date`, no time
component) use an **exclusive** end date in both the API and the UI. An
event that displays as spanning `2026-09-28` to `2026-10-03` actually covers
nights Sep 28 through Oct 2 — Oct 3 is the checkout/return day and is NOT
part of the event.

This causes real off-by-one mistakes when cross-referencing an all-day block
against a *timed* event on what looks like its last day (e.g. reading a
5-night trip block as ending on the day the user actually leaves, then
placing a same-morning reminder — like a rental/venue return — one full day
late because the display end-date was treated as inclusive).

**Fix:** when reasoning about an all-day event's actual last night, always
subtract one day from its displayed/stored end date before comparing it to
any timed event (flights, trains, check-ins) that should land on that same
day. Don't take the calendar UI's rendered end date at face value.

## Fix 5: Calendar `update` may be missing from a thin wrapper CLI

Some Google Calendar wrapper scripts (including Hermes' own `google_api.py`
compatibility layer) ship `list`/`create`/`delete` but no `update` verb,
forcing an unnecessary delete+recreate (which changes the event ID and
drops any attendee RSVPs) just to fix a date/time or description. If you
need to correct a single field on an existing event, check whether the
wrapper's argparser already has an `update` subcommand before resorting to
delete+recreate — and if it's genuinely missing, adding one (calling the
underlying `events().patch()` API method, which supports partial updates)
is a small, low-risk local fix worth making once rather than repeating the
delete+recreate workaround every time.

## Fix 6: Gmail body extraction returns empty on forwarded/nested multipart messages

A `gmail get MESSAGE_ID` call can return an empty `body` field even though
the message clearly has content — this shows up most often on **forwarded**
emails (e.g. a user forwarding a booking confirmation), which nest a
`multipart/*` MIME part inside another `multipart/*` part (e.g.
`multipart/mixed` wrapping a `multipart/alternative`).

Root cause: a body-extraction helper that only checks
`payload.body.data` and one level of `payload.parts[]` for `text/plain` or
`text/html` will find nothing when the actual text is nested two or more
MIME levels deep, and silently returns `""` instead of erroring — easy to
misdiagnose as "the email has no text" when it's actually a parsing gap.

**Fix:** walk the MIME tree recursively (not just one level of `parts`),
collecting the best `text/plain` (preferred) or `text/html` (fallback) part
found at any depth, decoding each part's own `body.data` as it's
encountered rather than assuming the payload's top-level `body.data` is
where the content lives. If you hit this on a wrapper script's body
extraction, patch the extractor to recurse through `payload.parts` at every
level rather than adding special-casing for one more MIME layout.

## Fix 7: Reminders for external rolling-window booking systems

Many reservation systems outside Google (state park campsites, national
parks, timed-entry permits, some restaurant/event platforms) don't take
bookings at arbitrary lead time — they open a fixed N-day/N-month rolling
window (e.g. ReserveCalifornia opens exactly 6 months ahead, at a fixed
daily time like 8:00 AM local). High-demand dates/sites at these systems
can sell out within minutes of the window opening, so "check back later"
is not a viable strategy — the user needs to be acting (or the agent needs
to be alerting) at the exact moment the window opens for their target date.

**Fix:** when a user wants a specific future date at one of these systems
and it isn't bookable yet, create a Google Calendar reminder dated exactly
(target date minus the window length), timed a few minutes BEFORE the
system's known daily unlock time (not after) so the user has a moment to be
at the keyboard:

```bash
$GAPI calendar create --calendar user@example.com \
  --summary "Check <system> for <specific dates/sites> (Nmo window opens)" \
  --start <window-open-date>T<unlock-time-minus-buffer><tz-offset> \
  --end   <window-open-date>T<unlock-time><tz-offset> \
  --description "<system> opens bookings on a rolling N-<day/month> window at <time> <tz>. Today unlocks <target date>. <Any specifics: site IDs, room type, what makes this date/site special or fast-selling>. Booking link: <url>."
```

Put the concrete unlock mechanics (window length, exact daily unlock time,
which specific sites/slots are known to sell out fastest) in the event
description, not just the summary — the user acting on this reminder months
from now will have long since lost the session context and needs the
description to be fully self-contained.

This is a lightweight alternative to a recurring `cronjob` monitor when the
real constraint is "be present at a known future instant," not "poll
repeatedly until a condition changes" — reach for a cron-based watch (see
the pricing/availability monitor pattern) only when the system takes
bookings continuously and cancellations can occur at unpredictable times.

Before reaching for browser automation against a login-gated booking UI to
check current availability, see `references/reservation-availability-checkers.md`
for known public, no-login read paths (e.g. California State Parks) that
are faster and avoid bot-detection entirely.

## Verification

- [ ] After enabling a flagged API, waited briefly before retrying rather than treating the first retry as proof the fix failed.
- [ ] Any calendar operation against a delegate/service account passes an explicit calendar ID, not the default.
- [ ] `drive share --role owner` returns `role: owner` in its response, and a follow-up `drive get` shows the new owner in the `owners` field.
- [ ] Any date math against an all-day event's stored end date treats it as exclusive (subtract one day for the real last-night/last-day).
- [ ] A rolling-window booking reminder is dated to the window-open day (not the target date) and its description is self-contained (system, window length, unlock time, target date/site, booking link).
- [ ] Before automating a login-gated booking UI just to READ availability, checked `references/reservation-availability-checkers.md` for a public no-login data source first.
