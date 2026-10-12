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
