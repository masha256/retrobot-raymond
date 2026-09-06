# Checking Reservation-System Availability Without Logging In

Companion to Fix 7 (rolling-window booking reminders). Before scheduling a
reminder for a future booking window, or when a user just wants current
availability, check whether the platform exposes a public, read-only
availability view separate from its login-gated booking flow. This is
faster and more reliable than driving the authenticated booking UI with
browser automation, and avoids bot-detection entirely.

## California State Parks / ReserveCalifornia

CA State Parks publishes live availability (refreshed every 15 min) on a
public page that needs no ReserveCalifornia account:

```
https://calparkspublicweb-staging.azurewebsites.net/AvailabilityInfo?page_id=<PAGE_ID>&arrival_date=<YYYY-MM-DD>&length=<NIGHTS>
```

- `page_id` is the park's ID on parks.ca.gov (visible in that park's own
  `?page_id=NNN` URL, e.g. Sonoma Coast State Park = 451). It is NOT the
  ReserveCalifornia park number shown on reservecalifornia.com/park/<id>
  (a different id for the same park, e.g. 718) — use the parks.ca.gov one
  for this endpoint.
- `arrival_date` + `length` return an 8-day rolling window starting at that
  date; each campground on the page gets its own `<table>`, one row per
  site, one column per date.
- Availability is encoded in a `<span>` icon class inside each cell, not in
  the cell's visible text (a naive `innerText` read returns blank cells):
  `fa-xmark` = unavailable, a class containing `check` = available. Extract
  with JS:

  ```js
  const table = document.querySelectorAll('table')[N]; // Nth campground table on the page
  const rows = table.querySelectorAll('tr');
  for (const row of rows) {
    const cells = row.querySelectorAll('td, th');
    const site = cells[0].innerText.trim();
    const statuses = Array.from(cells).slice(1).map(c => {
      const span = c.querySelector('span');
      const cls = span ? span.className : 'none';
      return cls.includes('xmark') ? 'X' : (cls.includes('check') ? 'OK' : cls);
    });
  }
  ```
- To scan several weekends/date ranges, re-navigate with a new
  `arrival_date` per call — the page returns a fresh 8-day window each
  time, which is simpler and more reliable than trying to paginate one
  loaded page.
- This is the same public data source linked from the official parks.ca.gov
  park page's own "Reservation Availability" section — it's the sanctioned
  read path, not a scraping workaround. Actual booking still requires an
  account and must be completed on reservecalifornia.com.
- California's rolling booking window is 6 months from today. Popular
  coastal/weekend sites can be fully booked solid for 10+ weeks straight
  even checking this far ahead, with occasional single-day gaps (e.g. major
  holidays, since regular travelers avoid them) opening up before demand
  resumes toward the 6-month edge. When checking for a specific day-of-week
  pattern (e.g. "next open Friday/Saturday"), scan several consecutive
  candidate weekends in one pass rather than stopping at the first miss.
