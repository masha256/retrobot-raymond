---
name: browser-exec-headless-setup
description: "Use when browser_exec fails chrome-not-running headless."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [browser, browser_exec, browser-harness, headless, chrome, CDP]
    category: software-development
---

# browser_exec on a headless Linux server

`browser_exec` is backed by the `browser-harness` CLI, which expects to find
a desktop Chrome/Chromium already running with remote debugging reachable.
On a headless server (no X session, no user ever opened a browser window)
this fails every time with `chrome-not-running: no supported browser is
running and none could be launched`. This skill is the fix path, learned the
hard way across many failed retries — follow it in order instead of
re-discovering it.

## Diagnose first

```bash
export PATH="$HOME/.local/share/uv/tools/browser-use/bin:$PATH"
browser-harness --doctor
```

Reads as a checklist: `chrome running`, `daemon alive`, `active browser
connections`, `Browser Use cloud auth (optional)`. Whichever line says
`[FAIL]` tells you what's actually missing — don't assume it's the daemon
when it's really "no browser process at all".

## Step 1: Install real Google Chrome — NOT the Snap package

`apt-get install chromium-browser` on Ubuntu pulls the **Snap-packaged**
Chromium. It runs fine standalone but Snap's sandboxing blocks the DevTools
protocol exposure browser-harness needs — you'll get chrome-not-running
forever even though Chrome is clearly running. Confirm this trap with:

```bash
browser-harness doctor --fix-snap
```

The real fix is the `.deb` build direct from Google, not Chromium at all:

```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb
```

This requires sudo — if you don't have it, ask the user to run these two
lines and confirm before continuing.

## Step 2: Launch Chrome headless, in a profile dir browser-harness scans

browser-harness detects "is a browser running" by checking `SingletonLock`
in a **fixed list** of profile directories (see `browser_harness/daemon.py`
`_LINUX_PROFILES`): `~/.config/google-chrome`, `~/.config/chromium`,
`~/.config/chromium-browser`, `~/.config/microsoft-edge`, and a few Flatpak
paths. Launching Chrome with an arbitrary custom `--user-data-dir` (e.g.
`~/.chrome-profile`) will start Chrome fine but browser-harness will still
report chrome-not-running, because that directory isn't one it scans. Use
the real default dir:

```bash
# terminal(background=true) — this must be a background process, it never exits
google-chrome-stable --headless=new --remote-debugging-port=9222 \
  --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --user-data-dir=$HOME/.config/google-chrome
```

Verify the CDP endpoint is actually up before touching browser_exec:

```bash
curl -s http://localhost:9222/json/version
# expect a JSON blob with "webSocketDebuggerUrl"
```

Then re-run `browser-harness --doctor` — `chrome running` should flip to
`[ok]`. `daemon alive` / `active browser connections` will still show FAIL
until the next actual `browser_exec` call, that's normal — the daemon
auto-starts on first use.

## Step 3: Use browser_exec normally

Once Chrome is up in the right profile dir, `new_tab()` / `goto_url()` /
`js()` / `click_at_xy()` / `capture_screenshot()` work exactly as documented
in the browser_exec tool description. No further env vars are needed —
don't bother setting `BU_CDP_WS` manually; once Chrome is in a scanned
profile dir, browser-harness finds it on its own.

## Pitfalls during a session

- **Intermittent `Runtime.evaluate timed out` / `TimeoutError` on the IPC
  socket** shows up even with plenty of free RAM and a healthy Chrome
  process. It's daemon-side, not a resource problem — don't start
  troubleshooting memory/CPU. Fix: `browser-harness --reload` (stops the
  daemon; it restarts clean on the next call), then retry the same action —
  it typically succeeds on the very next attempt. Don't loop more than once
  or two on the same failing call without reloading.
- **Killing a manually-launched Chrome and relaunching under a *different*
  custom profile dir** (e.g. troubleshooting by trying `~/.chrome-profile`,
  then `~/.config/google-chrome`) can leave a stale `SingletonLock`/PID
  mismatch. If doctor still says chrome-not-running after a relaunch,
  `pkill -f google-chrome-stable`, `rm -rf` the profile dir you're about to
  reuse, then relaunch fresh — don't layer a new launch on top of a half-dead
  old one.
- **Coordinate clicks landing on the wrong element** (e.g. a sponsored
  widget overlapping the real button) is common on ad-heavy travel/booking
  sites. Prefer finding the element via `js()` (query by text/role, dispatch
  a real click event on that exact node) over blind `click_at_xy` when a
  page has third-party embeds — a text-matched `document.querySelectorAll`
  scan is far more reliable than pixel coordinates on such pages.
- **Some booking/travel sites (e.g. Trainline) fingerprint and silently
  redirect/block automated sessions** after a few interactions — the page
  swaps to something like a Cloudflare/bot-check interstitial with no clear
  error. Don't keep retrying the same UI flow against a site once this
  happens. Two better pivots that worked: (1) construct the results URL
  directly with query params instead of driving the search form (many sites
  accept `?origin=...&destination=...&outwardDate=...` style deep links —
  inspect the URL after one successful manual-ish search to learn the
  pattern), or (2) fall back to `web_search`/published fare pages for
  pricing instead of scraping the live booking flow.
- **LNER (and similar heavily-protected sites) blocks headless access
  outright** ("Access to this page has been denied") — don't burn retries
  on a site that blocks on the very first request; pivot immediately to
  `web_search` for that source instead of trying alternate load strategies.
- **`Runtime.evaluate timed out` shows up sporadically even after the
  daemon has been reloaded once and things are otherwise working fine** —
  it's not a one-time startup hiccup, it can recur mid-session on an
  otherwise-healthy connection. Standard recovery is: wait a couple seconds
  and retry the exact same call once before reaching for `--reload` again;
  most single timeouts clear on their own on the next attempt without
  needing a daemon restart at all.

## Verification

```bash
curl -s http://localhost:9222/json/version   # CDP reachable
browser-harness --doctor                     # chrome running: [ok]
```
Then a trivial browser_exec call (`new_tab("https://example.com")` +
`page_info()`) should succeed without a chrome-not-running error.
