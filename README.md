# WorkReader

A self-contained Outlook-style reader for public deals and posts. Open **WorkReader.html** from a USB in Edge or Chrome. No installation is required on that computer.

This is an original implementation. It does not include code copied from msoutlookit. The interface uses an embedded SVG rendering of the familiar Outlook icon and the Outlook name. Microsoft Outlook branding belongs to Microsoft; WorkReader is an independent project, not Microsoft software or a Microsoft sign-in page.

## Start now

1. Open **WorkReader.html**. It includes a dated snapshot of the sources that could be collected during this build.
2. Browse the folders, search, flag items and add keyword watches.
3. Open **Sources** to see which collectors have succeeded, failed or have not run.
4. Use **Export** before moving to another computer. Import that JSON to restore saved items, watches and settings.

The HTML does not silently rewrite itself on the USB. Preferences and the latest downloaded snapshot are saved in that browser's local storage when available. Export is the portable backup. Browser policy may prevent local HTML, downloads, bookmarklets or access to GitHub; a USB does not alter those policies.

## Put the scanner on GitHub

Repository: https://github.com/StonkJam/WorkReader

The USB reader is preconfigured to load this repository's public data file. Open **WorkReader.html** and click **Refresh** to download the latest snapshot.

The initial source upload triggers a full collection job. Later source/configuration changes trigger it again. You can also run **Actions → Collect deal snapshots → Run workflow** and choose **full** or **quick**.

The scheduled workflow attempts a feed refresh about every 30 minutes. Rendered-page scans run roughly every four hours to avoid repeatedly loading the retailer/airline pages. GitHub may delay scheduled runs. Public repository schedules can be disabled after 60 days without repository activity; check Actions if updates stop. The schedule does not become active merely by opening the HTML.

### Optional hosted reader

1. In **Settings → Pages → Build and deployment → Source**, choose **GitHub Actions**.
2. Run **Actions → Publish reader on GitHub Pages → Run workflow**.
3. Open `https://StonkJam.github.io/WorkReader/`.

The scanner's completed workflow also triggers publication. The separate `workflow_run` trigger matters because commits made with GitHub's workflow token do not normally trigger another push workflow.

Public repository data and a normal GitHub Pages site are public. This project collects public offers/posts only; keep passwords, private documents, account cookies and API tokens out of the repository and HTML. No GitHub token is needed in the reader. Optional Raindrop integration uses a personal token entered at runtime.

## Sources and current limits

| Source | Method | What you get / limits |
|---|---|---|
| OzBargain | Official RSS | Titles, shortened text, authors, tags, votes, comment counts and links. Full description/comments stay on OzBargain. |
| Reddit | Public Atom/RSS | Posts if Reddit permits the runner to access the feed. No account login, full comment viewer or proxy workaround is included. |
| Jetstar community | OzBargain Jetstar RSS | Clearly labelled community posts, refreshed with feeds. Titles may list multiple routes/prices, so no single fare is inferred. These are not direct Jetstar scans. |
| Jetstar direct | Best-effort rendered-page cards | Your five sale/package pages. Flight and package types stay distinct. Cards with unclear multiple prices are left unpriced. Access and site layout can prevent collection. |
| JB Hi-Fi | Best-effort rendered-page cards | Your iPad Pro collection with the supplied clearance/newest query. Only cards explicitly labelled Clearance are accepted. A URL query alone is not treated as proof. Stock and ex-display condition must be checked on JB. |

**OzBargain and Reddit All have returned live data on GitHub. The direct Jetstar pages still failed after a standard HTTP/1 transport retry. The Jetstar community feed returned 10 posts during verification. JB has returned no explicitly verified iPad Pro clearance cards.** They are deliberately conservative rather than returning invented prices or claiming an empty scrape means no deals exist. The exact run results are in `VALIDATION.md`.

The page extractor works from recognised links/cards and their surrounding text. Site changes may require editing `scripts/extract-page.js`. It does not solve challenges, spoof authenticated sessions or circumvent access blocks.

### Page capture fallback (no server)

Open **Capture deals** in the reader. Drag its generated bookmark onto the bookmarks bar, or copy the code into a bookmark address. Open the source page normally, allow its listings to load, then click the bookmark. Import the downloaded `workreader-capture-*.json` into the reader.

The bookmark executes on the source page, where it can read the rendered cards. It downloads a capture locally; it does not upload it to GitHub. Imported captures merge into your current snapshot. A later refresh loads the repository snapshot; export captures you want to retain, and flag interesting items.

Bookmarklets may be blocked by a page or browser policy. The original source must itself be accessible. For JB, apply the Clearance filter and look for explicit Clearance labels. Reddit's capture is for visible posts, not a full comment-thread relay.

## Reader behaviour

- Inbox and per-source folders, unread tracking and saved items.
- Search within the selected folder; optional maximum price and deal-type filters.
- Watch searches match all supplied words, without sending notifications.
- Missing prices remain unknown and are excluded from maximum-price filters.
- Price history starts when this scanner first observes an item. It is not historical retailer data. Price drops only compare observed numeric amounts for the same item.
- Sources that fail retain older data with an older timestamp and stale label. Disappearing from a feed is not treated as proof that an offer expired.
- Images appear as attachment cards with “Click to preview”. No image is requested until clicked, or until Images on is enabled. Hide preview collapses it again. RSS image URLs are extracted when the feed supplies them; galleries and video are not guaranteed.
- Refresh downloads the latest JSON; it does not start an immediate collection job.
- Compact Outlook-inspired ribbon, app rail, folder pane and message list, with light/dark themes and responsive layout; J/K to move through messages, F to save, R to refresh. Shortcuts are inactive while typing or in dialogs.

Jetstar “from” fares may be one-way, per person, date-limited or subject to membership/baggage conditions. Package prices may use different passenger and night counts. The card text is retained and the booking page is the source of truth. Sydney is indicated when present on the card or requested by the package URL; it is not guaranteed simply because a query parameter says SYD. Flight sales are collected across origins from your supplied pages; search “Sydney” for explicit Sydney matches.

## Interface scale

The default **140%** interface scale matches the reference Outlook screenshot's larger panes and text. The desktop folder pane is about **241 px**, the message pane **462 px**, and the app rail **48 px** at this setting. Ribbon and message spacing are tuned separately so enlarging the text does not create oversized rows. The page compensates for scaling so the footer remains inside the viewport.

Choose **File → Reader settings → Interface scale** to use 100%, 110%, 125%, 140%, 150%, 175% or 200%. The choice persists in browser storage and exports. Responsive panes, dialogs and context menus account for the chosen scale. Browser zoom remains a separate setting.

## Reading/mail view, message actions and idle timeout

The file always opens in **mail view**, with image previews collapsed. Press **Space** to reveal the reader and start its idle timer. Press Space again to return to mail view. **Space** changes folder/subject labels and the message content without moving the interface. Both views keep the same senders, rows, timestamps, selected item, folder ordering, ribbon, filters, search query and pane positions. Reading view labels the folders and subjects with the actual source or subreddit; mail view substitutes neutral folder labels and fictional email subjects. The real source and title appear underneath in reading view; mail view uses neutral office text. Images collapse and stay collapsed until reopened. Space does not toggle while typing in a field or dialog. The ribbon button provides the same switch on touch devices.

In **File → Reader settings**, set the inactivity timeout in minutes (default **2**, **0** disables it). Mouse movement on the page, clicks, typing, scrolling and touch reset the timer. The timer runs only while reading; activity in mail view never reveals content. A visibility check catches elapsed time after returning from a background tab. Senders stay fictional; reading subjects identify the real subreddit/source.

Right-click a message row or the open message to **Save to Raindrop**, **Bookmark**, **Email…**, or **Mark as read/unread**. Email opens a draft in the computer's configured mail application containing the real title and link; it never sends automatically. Sharing and preview actions are unavailable in mail view. Right-click a folder to mark that folder as read. Space and Escape dismiss the context menu.

Click an image attachment card to preview it; click the same card again to close it. Attachment labels use generic filenames in both views.

Jetstar community offers render with a departure/fare table, with Sydney first. Prices must appear with an explicit dollar sign beside a recognised departure code. Semicolon-separated destinations remain distinct. Headline fares are not live quotes, and currency-ambiguous headlines are not converted into a table. Expand **Original offer text** to see the supplied description. Direct Jetstar scanning remains subject to source failures.

## Public snapshot connection

The reader first tries the configured public file. For a raw.githubusercontent.com address it can fall back to GitHub's official public Contents API for the same repository, branch and file. Neither transport uses a GitHub token or a third-party proxy. Failures retain cached posts and show a quiet status; **File → Reader settings** contains the actual connection details.

If both requests fail on your computer, use **Open public snapshot for manual import** in Settings, save that public JSON file, and choose **Import**. A connection that succeeds on the GitHub runner does not establish that the work browser can reach that endpoint.

## Raindrop.io

1. Open **Raindrop** in the ribbon. In [Raindrop integration settings](https://app.raindrop.io/settings/integrations), create a personal app and obtain its **Test token**.
2. Paste that token into the reader's password field and click **Connect**. Root and nested collections appear in the folder pane. Search queries use Raindrop's API; **Load more** fetches another page of bookmarks.
3. Select a public item and choose **Save to Raindrop**, then review its title, collection and tags before clicking **Save bookmark**.

The token, collection list and private bookmarks live only in JavaScript memory for the current session. They are not included in local storage, public snapshots, GitHub or exports. Closing/reloading the file requires reconnecting. Disconnect clears private data. The reader creates bookmarks only after an explicit save; it does not edit/delete existing bookmarks. Shared read-only collections are excluded from the save chooser.

Raindrop documents CORS support; its API's unauthenticated preflight accepts a file-origin request. Automated API tests use synthetic responses. A real account connection still requires your own token and network access to api.raindrop.io.

## Local development

Python 3.10+ is enough for feeds, building and tests; no Python installation is needed on the work computer.

```bash
python -m unittest discover -s tests -v
python scripts/collect.py --mode quick
python scripts/build.py
```

Full collection, on a computer where running a browser collector is permitted:

```bash
python -m pip install -r requirements-browser.txt
python -m playwright install chromium
python scripts/collect.py --mode full
python scripts/build.py
```

Edit `reader.template.html`, `styles/outlook.css` or `scripts/raindrop-client.js`, then run the builder to update both HTML files. Edit `config.json` to add/remove feed folders or change source URLs. Source files are plain text and the reader has no CDN dependency, analytics, third-party proxy or external JavaScript requirement.

## Files

- `WorkReader.html`: portable USB reader.
- `index.html`: identical reader for GitHub Pages.
- `data/deals.json`: public snapshot with independent source timestamps.
- `config.json`: watched sources.
- `scripts/collect.py`: collectors, deduplication, retention and observed price history.
- `scripts/extract-page.js`: rendered-page extractor, shared by the browser collector and capture bookmark.
- `scripts/build.py`: embeds data and bookmark code into the standalone reader.
- `.github/workflows/scan.yml`: collection schedule and manual scans.
- `.github/workflows/pages.yml`: optional Pages publishing.
- `tests/test_collect.py`: parser, failure-retention and price-history checks.

## Licence

The original code in this project is MIT licensed; see `LICENSE`. Public listing content and third-party brands remain owned by their respective owners. The licence covers this project's code, not rights to the source websites' content.

The v8 layout uses a compact filter menu (the sliders beside the folder heading or **Find → Filter**) instead of a permanent filter strip. Message rows are denser, the ribbon has familiar command groups, and the dark palette follows the supplied desktop Outlook reference. The first message is previewed at startup without marking it read.

Right-click **Save to Raindrop** is available in either view. If disconnected, connect with your personal Test token and the same clicked item opens in the save form; connecting does not change the selected message. Invalid tokens can be retried without losing that item. Closing the connection prompt cancels the pending save. No token or pending save is written to storage or exports.


## v9 Refresh, extra sources and video

Refresh redraws cached/live message rows in both mail and reader views, keeping the selected item and scroll positions where possible. The status bar distinguishes new messages, the same snapshot (Up to date), and a failed download. On failure, Connection details opens File settings with the actual transport errors. Refresh downloads GitHub's collected snapshot; it does not trigger a new scan. Sources are collected on the configured GitHub schedule, which can be delayed.

Choose **Sources → Add subreddit or category**. Enter a subreddit and Hot/New/Top this week, or choose an OzBargain category. Prepare request opens a prefilled GitHub issue. Submit it using the repository-owner account; **Add reader source** validates the request, updates config.json, scans that feed and commits its snapshot. Click Refresh once the action finishes. No GitHub token is embedded in the reader. Requests and source names are public. Unsupported/malformed requests and nonowner authors are rejected; URLs are constructed from the approved subreddit/category, not arbitrary request addresses. Duplicates are ignored and the configuration is limited to 60 sources. A failed source still appears with its scan status.

Video links supplied in feeds are retained without downloading media. Direct MP4/WebM/OGV/M4V links use the browser's video player; supplied Vimeo links use its official iframe. Click a video card to open/close it. Space or the idle timeout pauses direct players, removes all players, and clears preview state; returning to the reader leaves them closed. Clicking another message also clears video previews. YouTube uses its official player on an HTTPS-hosted page; the USB/local file offers **Open YouTube video** because local files cannot supply the required web-page referrer reliably. Native Reddit video links associated with a valid Reddit post use the official embed.reddit.com post player. If no valid post link is available, they offer Open Reddit video. No guessed DASH URLs or audio merging are used. Embedded players can capture keyboard focus: click outside the player before using Space; the ribbon switch and timeout still close it. Providers may refuse embedding or codecs, and original-site links are always available.
