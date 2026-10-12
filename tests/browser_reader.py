"""GitHub Chromium checks for stable chrome, actions and snapshot failover."""
import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aWQAAAABJRU5ErkJggg==')
def main():
    out=ROOT/'diagnostics/ui';out.mkdir(parents=True,exist_ok=True)
    snapshot=json.loads((ROOT/'data/deals.json').read_text())
    with sync_playwright() as pw:
        browser=pw.chromium.launch();context=browser.new_context(viewport={'width':1440,'height':900})
        images=[];posts=[];errors=[];network={'api':False}
        context.route('https://raw.githubusercontent.com/**',lambda route:route.abort())
        def github(route):
            if network['api']:route.fulfill(json=snapshot,headers={'Access-Control-Allow-Origin':'*'})
            else:route.abort()
        context.route('https://api.github.com/**',github)
        def image(route):images.append(route.request.url);route.fulfill(body=PNG,content_type='image/png')
        context.route('https://images.example/**',image)
        def raindrop(route):
            path=route.request.url.split('/rest/v1')[1]
            if path=='/collections':data={'result':True,'items':[{'_id':42,'title':'Travel','count':1}]}
            elif path=='/collections/childrens':data={'result':True,'items':[{'_id':43,'title':'Hotels','parent':{'$id':42}}]}
            elif path.startswith('/raindrops/'):data={'result':True,'items':[{'_id':999,'title':'Private test bookmark','link':'https://private.example/bookmark','created':'2026-10-12T00:00:00Z','cover':'https://images.example/private.png','collection':{'$id':42}}]}
            elif path=='/raindrop' and route.request.method=='POST':posts.append(route.request.post_data_json);data={'result':True,'item':{'_id':1000}}
            else:raise AssertionError(path)
            route.fulfill(json=data,headers={'Access-Control-Allow-Origin':'*'})
        context.route('https://api.raindrop.io/**',raindrop)
        page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto((ROOT/'WorkReader.html').as_uri());page.wait_for_function('!state.loading')
        assert page.locator('#app-name').inner_text()=='Outlook'
        assert page.title()=='Inbox — Outlook'
        assert page.locator('.brand .outlook-logo').count()==1
        assert page.locator('link[rel="icon"]').get_attribute('href').startswith('data:image/svg+xml,')
        assert page.locator('#toast').is_hidden(), 'Startup network failure is quiet'
        assert page.evaluate('!!state.syncError')
        assert page.evaluate('state.snapshot.items.length')==len(snapshot['items'])
        network['api']=True
        page.locator('#refresh').click();page.wait_for_function('!state.loading')
        assert page.evaluate('state.syncEndpoint')=='GitHub public API'
        assert not page.evaluate('state.syncError')
        page.evaluate("$('toast').classList.add('hidden')")
        refresh=page.locator('#refresh').bounding_box();glyph=page.locator('#refresh .oi').bounding_box();ribbon=page.locator('.ribbon').bounding_box()
        assert 22<=glyph['width']<=26 and refresh['y']+refresh['height']<=ribbon['y']+ribbon['height']
        page.locator('.message').first.click()
        page.evaluate("state.images=false;state.previewed.clear();currentItem().attachments=[{url:'https://images.example/public.png',name:'public.png'}];currentItem().image='';renderReading()")
        assert page.locator('.preview-block img').count()==0 and not images
        page.screenshot(path=str(out/'outlook-light.png'))
        page.locator('#theme').click();page.wait_for_function("getComputedStyle(document.querySelector('.folder.active')).backgroundColor==='rgb(56, 56, 56)'")
        page.get_by_text('Click to preview',exact=True).click();page.wait_for_selector('.preview-block img')
        page.get_by_text('Click to close',exact=True).click()
        assert page.locator('.preview-block img').count()==0, 'Same card closes image'
        page.get_by_text('Click to preview',exact=True).click();page.wait_for_selector('.preview-block img')
        selected=page.evaluate('state.selected');subject=page.locator('.read-head h2').inner_text()
        subjects=page.locator('.message .subject').all_text_contents();senders=page.locator('.message .sender').all_text_contents()
        sidebar=page.locator('#sidebar').inner_html();toolbar=page.locator('.ribbon').inner_html();count=page.locator('.message').count()
        rectangles=page.locator('.message').evaluate_all('(rows)=>rows.map(e=>{let r=e.getBoundingClientRect();return [r.x,r.y,r.width,r.height]})')
        page.screenshot(path=str(out/'subtle-reading.png'))
        page.keyboard.press('Space');assert page.evaluate('state.coverMode')
        assert page.locator('.preview-block img').count()==0
        assert page.locator('#sidebar').inner_html()==sidebar
        assert page.locator('.ribbon').inner_html()==toolbar
        assert page.locator('.message .subject').all_text_contents()==subjects
        assert page.locator('.message .sender').all_text_contents()==senders
        assert page.locator('.message').count()==count
        assert page.locator('.read-head h2').inner_text()==subject
        assert page.locator('.message').evaluate_all('(rows)=>rows.map(e=>{let r=e.getBoundingClientRect();return [r.x,r.y,r.width,r.height]})')==rectangles
        assert page.evaluate('state.selected')==selected
        page.screenshot(path=str(out/'subtle-mail.png'))
        page.keyboard.press('Space');assert not page.evaluate('state.coverMode')
        assert page.locator('.preview-block img').count()==0
        # Right-click operations use the clicked row, including a row that is not selected.
        row=page.locator('.message').nth(1);key=row.get_attribute('data-item');row.click(button='right')
        assert page.locator('#message-menu').is_visible()
        assert page.get_by_role('menuitem',name='Save to Raindrop').is_visible()
        assert page.get_by_role('menuitem',name='Email…').is_visible()
        page.get_by_role('menuitem',name='Bookmark',exact=True).click()
        assert page.evaluate('(key)=>state.saved.has(key)',key)
        row=page.locator('[data-item]').filter(has=page.locator('.subject')).nth(1)
        row.click(button='right');page.get_by_role('menuitem',name='Mark as read',exact=True).click()
        assert page.evaluate('(key)=>state.read.has(key)',key)
        page.locator('.message').nth(1).click(button='right');page.get_by_role('menuitem',name='Mark as unread',exact=True).click()
        assert not page.evaluate('(key)=>state.read.has(key)',key)
        page.locator('.message').first.click(button='right');page.keyboard.press('Escape');assert page.locator('#message-menu').is_hidden()
        assert page.evaluate("emailDraftLink(currentItem()).startsWith('mailto:?subject=')")
        page.locator('#search').fill('first');page.locator('#search').press('Space');assert page.locator('#search').input_value()=='first '
        assert not page.evaluate('state.coverMode');page.locator('#search').fill('')
        page.locator('#settings-tab').click();page.locator('#idle-minutes').fill('0.5');page.locator('#save-view-settings').click();assert page.evaluate('state.idleMinutes')==0.5
        page.locator('#settings-dialog .close').click();page.evaluate('state.idleMinutes=.005;recordActivity()');page.locator('#reading').dispatch_event('scroll');page.wait_for_function('state.coverMode',timeout=3000)
        page.evaluate('state.idleMinutes=2');page.locator('#cover-toggle').click();assert not page.evaluate('state.coverMode')
        page.locator('#search').fill('held query');page.locator('#settings-tab').click();page.evaluate('cover.lastActivity=Date.now()-120001;checkIdle()')
        assert page.locator('dialog[open]').count()==0
        page.locator('#cover-toggle').click();assert page.locator('#search').input_value()=='held query';page.locator('#search').fill('')
        page.locator('#raindrop').click();page.locator('#rd-token').fill('SYNTHETIC-TEST-TOKEN');page.locator('#rd-connect').click();page.wait_for_selector('[data-item="raindrop:999"]')
        assert page.locator('#rd-token').input_value()=='';page.locator('[data-item="raindrop:999"]').click()
        assert 'Private test bookmark' in page.locator('#reading').inner_text();page.evaluate('setCoverMode(true)');assert 'Private test bookmark' not in page.locator('#reading').inner_text();page.evaluate('setCoverMode(false)')
        assert 'Private test bookmark' in page.locator('#reading').inner_text();assert not any('private.png' in url for url in images)
        assert 'private.example' not in page.evaluate('JSON.stringify(exportData())');assert 'SYNTHETIC' not in page.evaluate('JSON.stringify(localStorage)');assert 'raindrop:999' not in page.evaluate('JSON.stringify(localStorage)')
        page.locator('[data-folder="inbox"]').click();page.locator('.message').first.click(button='right');page.get_by_role('menuitem',name='Save to Raindrop').click()
        page.locator('#rd-save-collection').select_option('42');page.locator('#rd-save-submit').click();page.wait_for_function("!document.getElementById('rd-save-dialog').open")
        assert len(posts)==1 and posts[0]['collection']['$id']==42
        page.locator('#raindrop').click();page.locator('#rd-disconnect').click();assert page.evaluate("rd.token===''&&rd.items.length===0");page.locator('#raindrop-dialog .close').click()
        page.locator('[data-folder="jetstar"]').click();page.locator('.message').filter(has_text='Bali Return').first.click()
        assert page.locator('.fare-table .sydney-row').inner_text().find('$459')>=0
        assert page.locator('.fare-table tr').nth(1).inner_text().startswith('Sydney')
        page.screenshot(path=str(out/'jetstar-offer.png'))
        page.set_viewport_size({'width':700,'height':850});page.locator('[data-folder="ozbargain"]').click();page.locator('.message').first.click();assert page.locator('#reading').is_visible();page.screenshot(path=str(out/'compact.png'))
        assert not errors,errors
        browser.close();print('Browser checks passed: stable chrome/row geometry, image toggle, context menu, idle timeout, official API failover, Raindrop privacy and Jetstar table.')
if __name__=='__main__':main()
