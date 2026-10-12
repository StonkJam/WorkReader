# Validation of the initial build

Build date: 12 October 2026 (Sydney). Snapshot generated at 2026-10-12T00:13:40Z / 11:13 AEDT.

## Live collection

| Source | Result |
|---|---|
| OzBargain popular | 20 feed entries collected |
| OzBargain new | 30 feed entries collected |
| OzBargain freebies | 30 feed entries collected |
| Reddit All | 25 posts collected from public Atom feed |
| Reddit Australia | HTTP 429 rate limit; explicitly reported as a failed source |
| Jetstar five pages | Browser collection not run locally; awaiting first full GitHub run |
| JB iPad Pro clearance | Browser collection not run locally; awaiting first full GitHub run |

After deduplicating the OzBargain feeds, the initial snapshot contains **62 unique deals + 25 Reddit posts = 87 items**. These are genuine retrieved listings; there are no invented/sample deals.

Direct inspection of JB's HTML confirmed a dynamically populated collection page. The product grid was not available as a simple static list. Direct Jetstar retrieval returned gateway errors/timeouts in the build environment. Neither observation is proof that those sources will fail from a GitHub runner or an ordinary browser.

## Automated checks passed

10 Python checks cover RSS metadata, Atom posts, HTML block-page rejection, unsafe-link rejection, deduplication, stale-data retention after failure, observed price changes, unknown prices, disappeared listings and retention cutoff.

Node runtime checks execute the built reader's JavaScript against a minimal simulated document. They cover startup with embedded data, source folders, keyword search, saved/unread state, price filters, safe import handling, bookmarklet construction, watch searches, and refresh success/failure. They verify that failed refreshes preserve current data and that the HTML has no external script dependency.

Python modules compile, the embedded JavaScript and page extractor pass JavaScript syntax checks, and the HTML has no duplicate static element IDs. The ZIP includes the dot-prefixed workflow directory.

## Verification limits

No real-browser rendering or visual interaction test was available in this environment. The Node checks do not substitute for that. Before relying on the application, open the HTML in your actual Edge/Chrome browser and run the first full GitHub scan.

Jetstar/JB's conservative card extraction is **best effort and unverified against a rendered live page in this build**. If the first scan returns “No verified deal cards”, use the manual Capture deals bookmark and adjust source-specific selectors as needed. A successful workflow can contain source-level failures; inspect Source status.

This report records the initial local build. The project has subsequently been uploaded to https://github.com/StonkJam/WorkReader. Check Actions and the reader’s Source status for the latest runner results. GitHub Pages requires Settings → Pages → GitHub Actions to be selected before its publication workflow succeeds.
