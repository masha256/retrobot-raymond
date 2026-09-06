---
name: aesthetic-slide-decks
description: "Use when a deck must look designed, not templated."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [pptx, powerpoint, slides, design, images, wikimedia, layout]
    category: productivity
    related_skills: [powerpoint]
---

# Aesthetic Slide Decks

Default deck-builder output (standard layouts, plain bulleted placeholders,
no imagery) is functional but generic. When the user explicitly wants a
deck that looks *designed* — a trip itinerary, a pitch deck, anything meant
to read like an editorial layout rather than an internal status update —
use this pattern on top of whatever pptx-building tool is available (e.g.
the `powerpoint` skill's `pptx_create.py`).

## When to Use

- User asks for a deck to be made "more aesthetically pleasing," "less
  corporate," or otherwise pushes back on a plain bulleted-list result.
- The subject matter is inherently visual (travel, places, products) and a
  photo-forward layout would communicate better than bullet text.
- Any request for a one-off presentation where visual polish is explicitly
  part of the ask, not just informational accuracy.

Don't reach for this on internal working decks, data-review decks, or
anywhere the user hasn't signaled they care about visual design — plain
bulleted layouts are faster to produce and easier to edit for that case.

## The pattern: full-bleed image + color overlay panel + freeform text

Build each slide from a blank layout, not a bulleted placeholder layout:

1. Blank layout, slide `background` set to that slide's theme color.
2. One image sized to cover roughly half (or more) of the slide — a real,
   specific photo of the subject, not a generic icon or stock graphic.
3. A solid-color rectangle covering the remaining portion of the slide,
   filled with the same theme color as the background, with its outline
   suppressed (borderless) so it reads as a color panel, not a boxed shape.
   This is what the text sits on.
4. Freeform positioned text blocks (not a bulleted placeholder) over that
   panel: a small all-caps kicker line (section/date label), a large serif
   headline, an italic subhead with a key logistics fact, and a body block
   with generous line spacing (~1.3x). Multiple short paragraphs read
   better than one long block or a dense bullet list.

Alternate image placement left/right slide-to-slide so a multi-slide deck
doesn't feel like one template stamped out repeatedly.

## Per-section color theming

For a deck with distinct phases/sections (days of a trip, chapters of a
pitch), give each section its own background/panel color rather than one
color for the whole deck — it reads as more intentional and helps orient
the viewer across a longer deck. Keep body/headline text color constant
(an off-white or off-black, not pure white/black) across every section so
legibility doesn't depend on remembering per-slide contrast.

## Sourcing free-use photos (no API key needed)

Wikimedia Commons serves full-resolution images directly via a predictable
URL pattern:

```bash
# 1. Find a candidate: web_search("<subject> wikimedia commons image file")
#    — results reliably surface commons.wikimedia.org/wiki/File:<name> pages.
# 2. URL-encode the exact file name (spaces, parens, commas and all):
encoded=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "Exact File Name.jpg")
# 3. Fetch via Special:FilePath with a width param:
curl -sL -A "Mozilla/5.0" "https://commons.wikimedia.org/wiki/Special:FilePath/${encoded}?width=1600" -o photo.jpg
# 4. Sanity-check before embedding — confirm it's a real image, not an HTML error page:
file photo.jpg
```

Repeat per location/subject, then embed the local files as the deck's
images. This avoids stock-photo licensing questions entirely for anything
with an existing Commons entry (landmarks, cities, buildings, most named
public places).

## Applying this in python-pptx (via the `powerpoint` skill)

The technique needs: a shape with a suppressible border (fill + no line)
for the color panel, and a freeform textbox primitive that supports
multiple styled paragraphs at arbitrary coordinates — not just the
standard bulleted-placeholder helper. If the `powerpoint` skill's
`pptx_create.py` spec format doesn't yet accept a `textboxes` key or a
`"line": "none"` option on `shapes`, both are small additions to that
script's `build_slide()` function — check `pptx_create.py --help` for the
live field list before assuming a feature is missing.

## Verification

Always render every slide to PNG and visually review it before sharing —
this layout style has far more room for overlap/overflow than
placeholder-based decks, since every position is manual rather than
auto-fit. Check specifically for: text running past the panel edge,
image/panel seams misaligned, and body text overlapping the kicker or
headline. If the available toolchain has a render-to-PNG step, use it;
otherwise fall back to a structured text/outline read-back to at least
verify content, and say so rather than presenting an unverified layout as
finished.
