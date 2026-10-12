# Validation

Updated 12 October 2026 (Sydney).

14 Python checks cover feed metadata, unsafe URLs, Reddit image links, image deduplication, failed-scan retention and observed price history. Node runtime checks cover reader state and filters, refresh failure/success, collapsed attachments, Raindrop root/nested collection browsing, explicit bookmark saving and exclusion of private data from storage/export.

The GitHub Chromium check opens the generated HTML directly as a file, checks light/dark modes, verifies images make no request before preview, exercises Raindrop with synthetic API responses, checks compact reading layout, and retains screenshots as a workflow artifact. This Chromium workflow passed successfully, and its screenshots were reviewed. It does not verify a real Raindrop account.

## Source results

OzBargain feeds and Reddit All have returned live data from GitHub. Reddit Australia has returned HTTP 429. Jetstar's five pages have failed during HTTP/2 navigation. This revision adds a standard HTTP/1 request-client transport retry for that specific error, without a proxy or authenticated session; the live runner still failed on all five pages after the retry. A separately labelled OzBargain Jetstar RSS fallback returned 10 posts on direct verification; no single-route fare is inferred from a community headline. JB's pages have returned no explicitly verified iPad Pro clearance cards. Failed sources remain visibly failed and do not become empty successful scans.

The Jetstar reading pane shows source links, errors and capture instructions when there is no selected listing. Manual Capture page reads visible cards in an ordinary source-page tab and imports a local JSON capture. It remains dependent on the page layout and browser bookmarklet support.

GitHub Pages remains optional and requires Settings → Pages → GitHub Actions. The USB HTML is self-contained; remote snapshots, images and Raindrop require access to their respective sites.

## Mail-view update

Node checks also cover replacing panes with a separate sample mailbox, closing dialogs, suppressing source/status content during background renders, preserving search and scroll positions, keeping images collapsed after return, switching at the configured inactivity deadline, and disabling the timer. Chromium checks exercise the Space shortcut, normal spaces in search, the actual short-duration idle timer, idle while a dialog is open, and covering/restoring a private Raindrop bookmark. The runner retains a mail-cover screenshot.

## Content-only mode and message actions

Runtime checks verify unchanged fake subjects, sidebar and counts across mode changes; preserved pane positions; same-card image toggle; read/unread state; email draft URL construction; official GitHub API fallback after raw-file failure; Sydney-first fare parsing; separate destinations; and rejection of year numbers and ambiguous currencies as fares. Chromium checks compare the exact geometry of every message row and the unchanged sidebar/ribbon across Space, exercise right-click Bookmark/read/unread/Raindrop actions, confirm quiet startup failure and successful mocked API failover, and retain Jetstar-format screenshots. Live endpoints were separately observed: raw public JSON returned HTTP 200 with permissive CORS; Pages data URL remained HTTP 404 because hosting is not enabled. Work-browser connectivity cannot be verified from the runner.

## Source-label revision

Reading view now exposes actual source/subreddit subjects and real folder names. Mail view replaces labels with neutral subjects/folders. Tests verify these label substitutions and their restoration while comparing unchanged message and folder row geometry, selection, counts and ribbon.

## Mail-first startup

Startup now sets mail view before the initial render, with images collapsed and no idle timer running. Space enters reading view and starts the configured idle countdown. Mouse movement joins clicks, typing and scrolling as activity that resets the timer. Checks cover initial neutral subjects/folders, timer state, first-Space entry, mouse-move activity reset, idle return to mail view and no automatic reveal on mouse movement.

## Outlook scale match

Both supplied screenshots have the same image dimensions. Their pane proportions indicate approximately 140% relative scaling: the reader message pane spans about 200 screenshot pixels versus about 280 in Outlook. This revision defaults to 140%, uses 172/330 CSS-pixel folder/message panes, and adjusts ribbon/folder/message spacing. Browser checks verify viewport/footer fit, context-menu fit at the scaled coordinates, unchanged geometry across mail/reader mode, compact layout, ultrawide pane measurements and saved scale preferences.


## v8 layout and Raindrop save flow

The newer desktop Outlook reference was measured for pane positions and dominant dark colours. v8 keeps the 140% scale and 172/330 CSS-pixel panes, uses a #141414 folder background and #292929 ribbon/reading surfaces, lengthens the title-bar search box, adds the small blue Outlook wordmark, compresses message rows to 58 CSS pixels, and puts filters in an overlay menu. The sender and actions share a compact header. All toolbar commands are functional reader commands; this remains an independent reader, not an Outlook client.

Chromium run 38205309781 passed. Screenshots reviewed at 1440×900 and 3440×1440 in light/dark, with additional compact and Jetstar screenshots. Checks cover unchanged row/folder geometry across Space, idle timeout and mouse reset, image close/reopen, right-click bookmark/read actions, and snapshot failover.

The right-click Raindrop action was previously disabled in mail view and discarded the clicked item when connection was required. It now remains available in either view and carries that item into the save form after connection. Browser checks use synthetic API responses to verify a nonselected row, an initial 401 and retry, correct title and collection in the POST, unchanged current selection, connected saving, and private-data exclusion from storage/exports. The real user's account and work-network access have not been tested.


## v9 regression scope

Added checks for mail-mode refresh with one new item and an additional source, neutral labels after refresh, retained selection/scroll, same-snapshot feedback and failed-fetch connection details. Source tests cover subreddit ordering, category URL construction, duplicates, the 60-source limit, repository/owner validation and rejection of arbitrary URL or malformed-name requests. Video tests cover extraction of supplied feed links, supported-provider parsing, hidden/unsafe content rejection, no player before preview, repeated-card close, removing Vimeo/direct players on Space, clearing state and the local-file YouTube original-site option. Browser provider/refresh tests use synthetic responses; they do not verify real remote playback or an owner-submitted source request.
