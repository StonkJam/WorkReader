# WorkReader

A self-contained Outlook-style reader for public deals and posts. Open **WorkReader.html** from a USB in Edge or Chrome. No installation is required on that computer.

This is an original implementation. It does not include code, branding or assets copied from msoutlookit, Microsoft Outlook, Jetstar or JB Hi-Fi.

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

## Quick mail view and idle timeout

Press **Space** while reading to switch to a fictional mailbox with neutral office emails. Press it again, or use **Reading view**, to return. Spaces in text fields and dialogs work normally. A **Mail view · Space** ribbon button is also available.

Mail view replaces the visible folder list, message list and reading pane; hides source controls and source status; closes dialogs; clears the token input; collapses image previews; and suppresses background toasts. Your folder, selected item, search query and pane positions are restored on return. Images stay collapsed until explicitly reopened. The fictional messages are separate from real data and never enter your snapshot or export. The sample mailbox has no send/reply capability.

In **File → Reader settings**, set the inactivity timeout in minutes (default **2**, **0** disables it), then choose **Save view settings**. Clicks, typing, scrolling and touch reset it; pointer movement alone does not. Returning from another tab checks elapsed wall-clock time, since browsers may delay timers in background tabs. A timed switch stays in mail view until you explicitly return.

The same settings include **Email-style reader headings**: neutral sender above the subreddit/source subject, with the real post title beneath. Turn this off to restore the original source/author list. These preferences are saved in the browser and included in exports; the current mail-view state is temporary.

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
