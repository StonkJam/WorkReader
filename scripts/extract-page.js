function extractPage(options = {}) {
  // Runs on the source page, either via Playwright or a user-clicked bookmarklet.
  const source = options.source || {};
  const host = location.hostname.replace(/^www\./, '');
  const belongs = domain => host === domain || host.endsWith('.'+domain);
  const group = belongs('ozbargain.com.au') ? 'ozbargain' : belongs('jbhifi.com.au') ? 'jbhifi' : belongs('jetstar.com') ? 'jetstar' : belongs('reddit.com') ? 'reddit' : '';
  if (!group) return {items:[], blocked:'This page is not a supported source.'};
  const text = el => (el?.innerText || el?.textContent || '').replace(/[ \t]+/g,' ').trim();
  const body = text(document.body);
  if (/^(access denied|just a moment|verify you are human|502 bad gateway)/i.test(body.slice(0,200))) return {items:[],blocked:'The site is showing a block/error page.'};
  const url = v => {if(!v)return '';try {const u = new URL(v, location.href); return /^https?:$/.test(u.protocol)&&!u.username&&!u.password ? u.href : '';} catch {return '';}};
  const priceMatches = s => [...s.matchAll(/(?:AU\$|A\$|AUD\s*\$|\$)\s*(\d[\d,]*(?:\.\d{1,2})?)/g)].map(m=>({value:Number(m[1].replace(/,/g,'')),index:m.index}));
  const items = [], seen = new Set();
  const isJb = group === 'jbhifi', isJet = group === 'jetstar';
  const candidates = isJb ? document.querySelectorAll('a[href*="/products/"]') : isJet ? document.querySelectorAll('a[href], [class*="deal-card"], [class*="fare-card"], [class*="package-card"]') : document.querySelectorAll(group==='ozbargain'?'a[href*="/node/"]':'a[href*="/comments/"]');
  for (const anchor of candidates) {
    if (anchor.closest('header,footer,nav,[role="navigation"]')) continue;
    let card = anchor, raw = '', prices = [];
    for (let depth=0;card && depth<7;depth++,card=card.parentElement) {
      raw = text(card); prices = priceMatches(raw);
      if (raw.length>2500 || card.querySelectorAll('a[href]').length>16) {card=null;break;}
      if (raw.length>=15 && (prices.length || (!isJb&&!isJet&&raw.length>60))) break;
    }
    if (!card || ((isJb||isJet)&&!prices.length)) continue;
    const heading = card.querySelector('h1,h2,h3,h4,[class*="product-title"],[class*="productTitle"],[data-testid*="title"]');
    let title = text(heading) || anchor.getAttribute('title') || anchor.getAttribute('aria-label') || text(anchor);
    if (title.length<8 || /^(view|book|shop|learn|find|read|see|more|from|details)/i.test(title)) title = raw.split('\n').map(x=>x.trim()).find(x=>x.length>8&&!/^\$|^from\b|^book\b|^view\b/i.test(x)) || '';
    if (!title || title.length>260) continue;
    if (isJb && !/ipad\s*pro/i.test(title)) continue;
    // A URL query alone is not proof that a retailer applied its clearance filter.
    if (isJb && !/\bclearance\b/i.test(raw)) continue;
    if (isJet && /insurance|farecredit|gift card|payment fee/i.test(title)) continue;
    const link = anchor.getAttribute('href') || card.querySelector('a[href]')?.getAttribute('href');
    const itemUrl = url(link || location.href); if (!itemUrl) continue;
    const kind = isJet ? (source.deal_type || (location.pathname.includes('/holidays')?'package':'flight')) : group==='reddit'?'post':'deal';
    const currencyAmbiguous = /(?:NZ\$|US\$|USD|NZD|SGD|JPY|THB)/i.test(raw);
    // Prefer dedicated price elements. If multiple amounts remain, don't invent a sale price.
    const priceEl = card.querySelector('[data-testid="price"],[class*="sale-price"],[class*="salePrice"],[class*="current-price"],[class*="currentPrice"]');
    const explicit = priceMatches(text(priceEl));
    const unique = [...new Set(prices.map(p=>p.value))];
    const price = currencyAmbiguous ? null : explicit.length===1 ? explicit[0].value : unique.length===1 ? unique[0] : null;
    const k = group+'|'+new URL(itemUrl).hostname+new URL(itemUrl).pathname+'|'+(isJet?title.toLowerCase():'');
    if (seen.has(k)) continue; seen.add(k);
    const img = card.querySelector('img');
    items.push({group, title:title.trim(), url:itemUrl, author:isJet?'Jetstar':isJb?'JB Hi-Fi':group==='reddit'?'Reddit':'OzBargain', text:raw.slice(0,5000),
      image:url(img?.getAttribute('src')||''), price, currency:currencyAmbiguous?'Unknown':'AUD', kind,
      price_basis:kind==='flight'?'Advertised fare; confirm dates, direction and bags':kind==='package'?'Advertised package; confirm passengers, nights and inclusions':price===null?'Multiple/unclear prices; read original listing':'Displayed card price',
      tags:isJb?['Clearance']:[], clearance:isJb?true:null, votes:null, comments:null,
      origin:/\bSydney\b|\bSYD\b/i.test(raw)?'SYD':isJet&&new URL(location.href).searchParams.get('originCode')==='SYD'?'SYD':null,
      origin_evidence:isJet&&new URL(location.href).searchParams.get('originCode')==='SYD'?'Page requested for Sydney; confirm package':null,
      source_url:location.href, evidence:isJb?'Rendered card explicitly labelled Clearance':'Rendered page card · check full offer', key:k});
    if(items.length>=100) break;
  }
  return {items, blocked:null, page_url:location.href, title:document.title};
}
