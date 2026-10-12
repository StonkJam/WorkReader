#!/usr/bin/env python3
"""Collect public feed snapshots. Browser collectors are conservative, best effort.

No accounts, API secrets, CAPTCHA bypass, public proxies or network setting changes.
"""
import argparse
import hashlib
import html
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
NOW = lambda: datetime.now(timezone.utc).isoformat()


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []; self.hidden = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'): self.hidden += 1
        if tag in ('br', 'p', 'div', 'li'): self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script', 'style'): self.hidden = max(0, self.hidden - 1)
        if tag in ('p', 'div', 'li'): self.parts.append('\n')
    def handle_data(self, data):
        if not self.hidden: self.parts.append(data)


def plain(value):
    p = PlainText(); p.feed(value or '')
    return re.sub(r'\n\s*\n+', '\n\n', ''.join(p.parts)).strip()[:15000]


def safe_url(value):
    try:
        p = urlparse(value or '')
        return value if p.scheme in ('https', 'http') and p.netloc and not p.username and not p.password else ''
    except ValueError: return ''


class FeedImages(HTMLParser):
    """Collect supplied image addresses without downloading any image."""
    def __init__(self):
        super().__init__(); self.images = []; self.seen = set(); self.hidden = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'): self.hidden += 1
        if self.hidden: return
        attrs = dict(attrs)
        value = attrs.get('src') if tag == 'img' else attrs.get('href') if tag == 'a' else ''
        value = safe_url(value)
        if not value: return
        parsed = urlparse(value)
        if tag != 'img' and not re.search(r'\.(?:jpg|jpeg|png|gif|webp|avif)$', parsed.path, re.I): return
        if value not in self.seen:
            self.seen.add(value)
            self.images.append({'type':'image', 'url':value, 'name':parsed.path.rsplit('/',1)[-1][:100] or parsed.hostname + '.jpg'})
    def handle_endtag(self, tag):
        if tag in ('script', 'style'): self.hidden = max(0, self.hidden-1)


def feed_images(content):
    parser = FeedImages(); parser.feed(content or '')
    return parser.images[:12]



class FeedVideos(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.seen=set();self.hidden=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.hidden+=1
        if self.hidden:return
        attrs=dict(attrs)
        link=safe_url(attrs.get('href') if tag=='a' else attrs.get('src') if tag in ('video','source','iframe') else '')
        if not link:return
        u=urlparse(link)
        supported=bool(re.search(r'\.(?:mp4|webm|ogv|m4v)$',u.path,re.I)) or u.hostname in ('youtube.com','www.youtube.com','m.youtube.com','youtu.be','www.youtube-nocookie.com','vimeo.com','www.vimeo.com','player.vimeo.com','v.redd.it')
        if supported and link not in self.seen:
            self.seen.add(link);self.links.append({'url':link})
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.hidden=max(0,self.hidden-1)


def feed_videos(content):
    parser=FeedVideos();parser.feed(content or '');return parser.links[:6]


def price_in_title(title):
    # OzBargain titles often contain prices AND discounts; prefer an actual dollar price.
    m = re.search(r'(?<![\w])(?:AU\$|A\$|AUD\s*\$|\$)\s*(\d[\d,]*(?:\.\d{1,2})?)', title)
    return float(m.group(1).replace(',', '')) if m else None


def date_text(value):
    if not value: return None
    try: return parsedate_to_datetime(value).isoformat()
    except (ValueError, TypeError):
        try: return datetime.fromisoformat(value.replace('Z', '+00:00')).isoformat()
        except ValueError: return None


def key(item):
    u = urlparse(item['url'])
    suffix = item['title'].strip().lower() if item['group'] == 'jetstar' else ''
    return item['group'] + '|' + u.netloc.lower() + u.path.rstrip('/') + '|' + suffix


def identify(item):
    item['key'] = key(item)
    item['id'] = hashlib.sha256(item['key'].encode()).hexdigest()[:20]
    return item


def parse_feed(data, source, checked=None):
    checked = checked or NOW(); root = ET.fromstring(data)
    items = []
    if source['kind'] == 'rss':
        channel = root.find('channel')
        if channel is None: raise ValueError('Expected an RSS feed; got a different response')
        for node in channel.findall('item'):
            url = safe_url(node.findtext('link'))
            title = html.unescape(node.findtext('title') or '').strip()
            if not url or not title: continue
            meta = next((n for n in node if n.tag.endswith('}meta')), None)
            attrs = meta.attrib if meta is not None else {}
            author = node.findtext('{http://purl.org/dc/elements/1.1/}creator') or 'OzBargain'
            categories = [n.text for n in node.findall('category') if n.text]
            try: votes = int(attrs.get('votes-pos', 0)) - int(attrs.get('votes-neg', 0))
            except ValueError: votes = None
            try: comments = int(attrs['comment-count']) if 'comment-count' in attrs else None
            except ValueError: comments = None
            items.append(identify({'group':source['group'], 'source_ids':[source['id']], 'title':title,
                'url':url, 'store_url':safe_url(attrs.get('url')), 'image':safe_url(attrs.get('image')),
                'attachments':feed_images(node.findtext('description')), 'videos':feed_videos(node.findtext('description')),
                'author':author, 'text':plain(node.findtext('description')), 'tags':categories,
                'price':None if source.get('community') else price_in_title(title), 'currency':'AUD',
                'price_basis':'Community post may list several routes/prices; verify the original offer' if source.get('community') else 'Price parsed from title; check offer',
                'votes':votes, 'comments':comments, 'published':date_text(node.findtext('pubDate')),
                'checked_at':checked, 'kind':'deal', 'community':bool(source.get('community')),
                'evidence':'OzBargain community RSS · not a direct Jetstar scan' if source.get('community') else 'Official RSS · shortened description'}))
    else:
        ns = {'a':'http://www.w3.org/2005/Atom'}
        if root.tag != '{http://www.w3.org/2005/Atom}feed': raise ValueError('Expected a Reddit Atom feed')
        for node in root.findall('a:entry', ns):
            link = next((n.attrib.get('href') for n in node.findall('a:link', ns) if n.attrib.get('rel','alternate')=='alternate'), '')
            url = safe_url(link); title = node.findtext('a:title', '', ns)
            if not url or not title: continue
            author = node.findtext('a:author/a:name', 'Reddit', ns)
            items.append(identify({'group':'reddit', 'source_ids':[source['id']], 'title':title, 'url':url,
                'author':author, 'text':plain(node.findtext('a:content', '', ns)), 'tags':[source['name']],
                'attachments':feed_images(node.findtext('a:content', '', ns)), 'videos':feed_videos(node.findtext('a:content', '', ns)),
                'price':None, 'votes':None, 'comments':None, 'kind':'post',
                'published':date_text(node.findtext('a:updated', '', ns)), 'checked_at':checked,
                'evidence':'Reddit RSS · votes and comment threads not supplied'}))
    return items


def fetch_feed(source):
    req = urllib.request.Request(source['url'], headers={'User-Agent':'WorkReader/1.0 (personal RSS reader)', 'Accept':'application/rss+xml, application/atom+xml, application/xml'})
    with urllib.request.urlopen(req, timeout=25) as response:
        data = response.read(4_000_001)
        if len(data)>4_000_000: raise ValueError('Feed exceeds size limit')
    return parse_feed(data, source)


def browser_collect(browser, source):
    page = browser.new_page(viewport={'width':1440, 'height':1000}, locale='en-AU')
    network_errors = []
    page.on('requestfailed', lambda request: network_errors.append({'url':request.url[:500], 'error':request.failure}))
    try:
        try:
            response = page.goto(source['url'], wait_until='domcontentloaded', timeout=20000)
        except Exception as err:
            if source['group'] != 'jetstar' or 'ERR_HTTP2_PROTOCOL_ERROR' not in str(err): raise
            # Ordinary HTTP/1 transport fallback for a failed HTTP/2 connection.
            # Playwright's request client uses HTTP/1. No proxy, cookies from an
            # account, identity spoofing, or challenge handling is involved.
            def http1(route):
                if route.request.method != 'GET':
                    route.continue_(); return
                try:
                    result = page.request.get(route.request.url, timeout=12000)
                    route.fulfill(response=result)
                except Exception:
                    route.continue_()
            page.route('https://www.jetstar.com/**', http1)
            print(source['id'], 'retrying standard HTTP/1 transport')
            response = page.goto(source['url'], wait_until='domcontentloaded', timeout=25000)
        if response and response.status >= 400: raise ValueError('Website returned HTTP ' + str(response.status))
        for label in ('Accept all', 'Accept All', 'Accept cookies'):
            try:
                button = page.get_by_role('button', name=label, exact=True)
                if button.count(): button.first.click(timeout=1200)
            except Exception: pass
        # Retail listings and flight cards render asynchronously. Bounded scrolling loads visible cards.
        page.wait_for_timeout(6000)
        for _ in range(3):
            page.mouse.wheel(0, 900); page.wait_for_timeout(900)
        extractor = (ROOT/'scripts/extract-page.js').read_text()
        result = page.evaluate('(' + extractor + ')', {'source':source})
        if result.get('blocked'): raise ValueError(result['blocked'])
        if not result['items'] and source['group']=='jbhifi' and source.get('clearance_only'):
            # The supplied URL may render an unfiltered collection. Use JB's own clearance
            # collection, still requiring an explicit Clearance label and an iPad Pro title.
            response=page.goto('https://www.jbhifi.com.au/collections/computers-tablets/computer-clearance', wait_until='domcontentloaded', timeout=20000)
            if response and response.status>=400: raise ValueError('Clearance page returned HTTP '+str(response.status))
            page.wait_for_timeout(6000)
            for _ in range(3):
                page.mouse.wheel(0,900); page.wait_for_timeout(900)
            result=page.evaluate('('+extractor+')', {'source':source})
            if result.get('blocked'): raise ValueError(result['blocked'])
        if not result['items']:
            raise ValueError('No verified deal cards found. Open the source and use Capture deals; check whether the sale/filter is active.')
        checked = NOW()
        for item in result['items']:
            item.update(group=source['group'], source_ids=[source['id']], checked_at=checked, published=None)
            identify(item)
        return result['items']
    except Exception:
        # Public, anonymous-page diagnostics stay in workflow artifacts, not the published feed.
        diagnostic = {'source':source['id'], 'url':source['url'], 'checked_at':NOW(), 'network_errors':network_errors[:25]}
        try:
            diagnostic['title'] = page.title()
            diagnostic['visible_text'] = page.locator('body').inner_text(timeout=2000)[:8000]
            diagnostic['product_links'] = page.locator('a[href*="/products/"]').evaluate_all('(els) => els.slice(0,25).map(e => ({text:e.innerText, href:e.href, card:e.parentElement?.innerText?.slice(0,1200)}))')
        except Exception: pass
        target=ROOT/'diagnostics'; target.mkdir(exist_ok=True)
        (target/(source['id']+'.json')).write_text(json.dumps(diagnostic,ensure_ascii=False,indent=2))
        raise
    finally: page.close()


def merge(previous, observations, statuses, generated, retain_days=14):
    """Keep failure snapshots, but never refresh their checked_at or manufacture prices."""
    cutoff = datetime.fromisoformat(generated) - timedelta(days=retain_days)
    old_by = {i.get('key') or key(i):i for i in previous.get('items', [])}
    by = {}
    for item in observations:
        k = item.get('key') or key(item); old = old_by.get(k, {})
        if k in by:
            by[k]['source_ids'] = sorted(set(by[k]['source_ids'] + item['source_ids']))
            continue
        history = list(old.get('price_history', []))
        price = item.get('price'); oldprice = old.get('price')
        if price is not None and (not history or history[-1]['price'] != price):
            history.append({'at':generated, 'price':price})
        by[k] = {**item, 'first_seen':old.get('first_seen', generated), 'last_seen':generated,
                 'price_history':history[-50:], 'previous_price':oldprice if oldprice!=price else old.get('previous_price'), 'stale':False}
    successful = {s['id'] for s in statuses if s['status']=='ok'}
    for k, item in old_by.items():
        if k in by: continue
        try: last = datetime.fromisoformat(item.get('last_seen') or item['checked_at'])
        except (ValueError, KeyError): continue
        if last < cutoff: continue
        # Successful source no longer lists an item: retain for history, visibly mark it.
        by[k] = {**item, 'stale':True, 'stale_reason': 'No longer in latest listing' if successful.intersection(item.get('source_ids', [])) else 'Source has not been checked successfully'}
    return {'schema_version':1, 'generated_at':generated, 'sources':statuses, 'items':list(by.values())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['quick','full'], default='quick')
    parser.add_argument('--output', default=str(ROOT/'data/deals.json'))
    parser.add_argument('--only', help='Comma-separated source IDs')
    args = parser.parse_args()
    cfg = json.loads((ROOT/'config.json').read_text()); output = Path(args.output)
    previous = json.loads(output.read_text()) if output.exists() else {'items':[], 'sources':[]}
    prevstatus = {s['id']:s for s in previous.get('sources', [])}
    selected = set(args.only.split(',')) if args.only else None
    observations = []; statuses = []; browser = None; pw = None
    if args.mode=='full':
        try:
            from playwright.sync_api import sync_playwright
            pw = sync_playwright().start(); browser = pw.chromium.launch(headless=True)
        except Exception as err: print('Browser collection unavailable:', str(err)[:200], file=sys.stderr)
    try:
        for source in cfg['sources']:
            prior = prevstatus.get(source['id'], {})
            status = {**source, 'last_success':prior.get('last_success'), 'attempted_at':NOW()}
            if (selected and source['id'] not in selected) or (source['kind']=='browser' and args.mode!='full'):
                statuses.append({**status, 'status':prior.get('status','not_checked'), 'attempted_at':prior.get('attempted_at'), 'message':prior.get('message','Awaiting a full browser scan or manual capture')})
                # Sources deliberately not scanned keep their previous data; preserve freshness.
                observations.extend({**i, '_preserved':True} for i in previous.get('items',[]) if source['id'] in i.get('source_ids',[]) and not i.get('stale'))
                continue
            try:
                if source['kind']=='browser':
                    if not browser: raise ValueError('Playwright/Chromium unavailable. Run a full GitHub scan or use Capture deals.')
                    items = browser_collect(browser, source)
                else: items = fetch_feed(source)
                observations.extend(items[:cfg['max_items_per_source']])
                statuses.append({**status, 'status':'ok', 'last_success':NOW(), 'count':len(items), 'message':'Public listing collected'})
                print(source['id'], 'OK', len(items))
            except Exception as err:
                message = str(err)[:250]
                if source['group']=='jetstar' and 'ERR_HTTP2_PROTOCOL_ERROR' in str(err):
                    message = 'Jetstar connection failed (HTTP/2); standard HTTP/1 retry also failed. Open the page or use Capture page.'
                statuses.append({**status, 'status':'error', 'message':message})
                print(source['id'], 'ERROR', str(err)[:160])
            if source['group']=='reddit': time.sleep(2)
    finally:
        if browser: browser.close()
        if pw: pw.stop()
    result = merge(previous, observations, statuses, NOW(), cfg['retain_days'])
    # Preserved sources were not scanned: their observation times must remain unchanged.
    old_by = {i.get('key') or key(i):i for i in previous.get('items',[])}
    for item in result['items']:
        if item.pop('_preserved', False):
            old = old_by.get(item['key'], {})
            item['last_seen'] = old.get('last_seen', item['checked_at'])
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix('.tmp'); temp.write_text(json.dumps(result, ensure_ascii=False, indent=2)); temp.replace(output)
    if not any(s['status']=='ok' and s.get('attempted_at') for s in statuses):
        print('No successful sources. Snapshot retains previous data and errors.', file=sys.stderr)


if __name__=='__main__': main()
