# Validation

Updated 12 October 2026 (Sydney).

13 Python checks cover feed metadata, unsafe URLs, Reddit image links, image deduplication, failed-scan retention and observed price history. Node runtime checks cover reader state and filters, refresh failure/success, collapsed attachments, Raindrop root/nested collection browsing, explicit bookmark saving and exclusion of private data from storage/export.

The GitHub Chromium check opens the generated HTML directly as a file, checks light/dark modes, verifies images make no request before preview, exercises Raindrop with synthetic API responses, checks compact reading layout, and retains screenshots as a workflow artifact. It does not verify a real Raindrop account.

## Source results

OzBargain feeds and Reddit All have returned live data from GitHub. Reddit Australia has returned HTTP 429. Jetstar's five pages have failed during HTTP/2 navigation. This revision adds a standard HTTP/1 request-client transport retry for that specific error, without a proxy or authenticated session; its live outcome must be read from Source status. JB's pages have returned no explicitly verified iPad Pro clearance cards. Failed sources remain visibly failed and do not become empty successful scans.

The Jetstar reading pane shows source links, errors and capture instructions when there is no selected listing. Manual Capture page reads visible cards in an ordinary source-page tab and imports a local JSON capture. It remains dependent on the page layout and browser bookmarklet support.

GitHub Pages remains optional and requires Settings → Pages → GitHub Actions. The USB HTML is self-contained; remote snapshots, images and Raindrop require access to their respective sites.
