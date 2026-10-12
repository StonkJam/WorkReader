"""Real Chromium checks run on GitHub Actions, with synthetic private API data."""
import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aWQAAAABJRU5ErkJggg==')

def main():
    out = ROOT/'diagnostics/ui'; out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(viewport={'width':1440,'height':900})
        images = []; posts = []; errors = []
        context.route('https://raw.githubusercontent.com/**', lambda route: route.abort())
        def image(route):
            images.append(route.request.url)
            route.fulfill(body=PNG, content_type='image/png')
        context.route('https://images.example/**', image)
        def api(route):
            path = route.request.url.split('/rest/v1')[1]
            if path == '/collections':
                data={'result':True,'items':[{'_id':42,'title':'Travel','count':1}]}
            elif path == '/collections/childrens':
                data={'result':True,'items':[{'_id':43,'title':'Hotels','parent':{'$id':42}}]}
            elif path.startswith('/raindrops/'):
                data={'result':True,'items':[{'_id':999,'title':'Private test bookmark','link':'https://private.example/bookmark','created':'2026-10-12T00:00:00Z','cover':'https://images.example/private.png','collection':{'$id':42}}]}
            elif path == '/raindrop' and route.request.method == 'POST':
                posts.append(route.request.post_data_json)
                data={'result':True,'item':{'_id':1000}}
            else:
                raise AssertionError('Unexpected API call: '+path)
            route.fulfill(json=data, headers={'Access-Control-Allow-Origin':'*'})
        context.route('https://api.raindrop.io/**', api)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto((ROOT/'WorkReader.html').as_uri())
        page.wait_for_selector('.message')
        page.locator('.message').first.click()
        page.evaluate("state.images=false;state.previewed.clear();currentItem().attachments=[{url:'https://images.example/public.png',name:'public.png'}];currentItem().image='';renderReading()")
        assert page.locator('.preview-block img').count()==0 and not images
        page.screenshot(path=str(out/'outlook-light.png'))
        page.locator('#theme').click()
        assert page.locator('body').evaluate("e=>e.classList.contains('dark')")
        page.wait_for_function("getComputedStyle(document.querySelector('.folder.active')).backgroundColor==='rgb(56, 56, 56)'")
        page.screenshot(path=str(out/'outlook-dark.png'))
        page.get_by_text('Click to preview', exact=True).click()
        page.wait_for_selector('.preview-block img')
        page.wait_for_function("document.querySelector('.preview-block img').complete")
        assert images==['https://images.example/public.png']
        page.screenshot(path=str(out/'image-preview.png'))
        selected = page.evaluate('state.selected')
        page.locator('#reading').evaluate('e=>e.scrollTop=50')
        page.keyboard.press('Space')
        assert page.evaluate('state.coverMode'), 'Space works after clicking preview'
        assert page.locator('.preview-block img').count()==0
        assert page.locator('dialog[open]').count()==0
        assert not page.locator('#sources-tab').is_visible()
        assert not page.locator('#status-details').is_visible()
        assert 'OzBargain' not in page.locator('#sidebar').inner_text()
        assert 'Weekly planning notes' in page.locator('#list').inner_text()
        assert 'Gilligan' not in page.locator('#reading').inner_text()
        page.evaluate("render();renderStatus();toast('Background refresh')")
        assert page.locator('#toast').is_hidden()
        page.screenshot(path=str(out/'mail-cover-dark.png'))
        page.keyboard.press('Space')
        assert not page.evaluate('state.coverMode')
        assert page.evaluate('state.selected')==selected
        assert page.locator('.preview-block img').count()==0, 'Images remain hidden on return'
        # Spaces while typing are ordinary text; repeated keydown never flips twice.
        page.locator('#search').fill('first')
        page.locator('#search').press('Space')
        assert not page.evaluate('state.coverMode')
        assert page.locator('#search').input_value()=='first '
        page.locator('#search').fill('')
        page.locator('#settings-tab').click()
        page.locator('#idle-minutes').fill('0.5')
        page.locator('#save-view-settings').click()
        assert page.evaluate('state.idleMinutes')==0.5
        page.locator('#settings-dialog .close').click()
        # Use a short runtime-only interval to exercise the real timer without a long wait.
        page.evaluate('state.idleMinutes=.005;recordActivity()')
        page.locator('#reading').dispatch_event('scroll')
        page.wait_for_function('state.coverMode', timeout=3000)
        page.evaluate('state.idleMinutes=2')
        page.locator('#mail-return').click()
        assert not page.evaluate('state.coverMode')
        page.evaluate('state.idleMinutes=2;recordActivity()')
        page.locator('#search').fill('held query')
        page.locator('#settings-tab').click()
        page.evaluate('cover.lastActivity=Date.now()-120001;checkIdle()')
        assert page.locator('dialog[open]').count()==0, 'Idle closes an open dialog'
        page.locator('#mail-return').click()
        assert page.locator('#search').input_value()=='held query'
        page.locator('#search').fill('')
        # The email-style list shows subreddit/source subject above the post title.
        assert page.locator('.message .subject').first.inner_text()==page.evaluate('mailHeading(visibleItems()[0])')
        page.locator('#raindrop').click()
        page.locator('#rd-token').fill('SYNTHETIC-TEST-TOKEN')
        page.locator('#rd-connect').click()
        page.wait_for_selector('[data-item="raindrop:999"]')
        assert page.locator('#rd-token').input_value()==''
        page.locator('[data-item="raindrop:999"]').click()
        assert 'Private test bookmark' in page.locator('#reading').inner_text()
        page.evaluate('setCoverMode(true)')
        assert 'Private test bookmark' not in page.locator('#reading').inner_text()
        page.evaluate('setCoverMode(false)')
        assert 'Private test bookmark' in page.locator('#reading').inner_text()
        assert images==['https://images.example/public.png'], 'Private cover remains collapsed'
        assert 'private.example' not in page.evaluate('JSON.stringify(exportData())')
        assert 'SYNTHETIC' not in page.evaluate('JSON.stringify(localStorage)')
        assert 'raindrop:999' not in page.evaluate('JSON.stringify(localStorage)')
        page.locator('[data-folder="inbox"]').click()
        page.locator('.message').first.click()
        page.locator('#save-raindrop').click()
        page.locator('#rd-save-collection').select_option('42')
        page.locator('#rd-save-submit').click()
        page.wait_for_function("!document.getElementById('rd-save-dialog').open")
        assert len(posts)==1 and posts[0]['collection']['$id']==42
        page.locator('#raindrop').click()
        page.locator('#rd-disconnect').click()
        assert page.evaluate("rd.token===''&&rd.items.length===0")
        page.locator('#raindrop-dialog .close').click()
        page.locator('[data-folder="jetstar"]').click()
        assert 'Jetstar deals' in page.locator('#reading').inner_text()
        page.screenshot(path=str(out/'jetstar-status.png'))
        page.set_viewport_size({'width':700,'height':850})
        page.locator('[data-folder="ozbargain"]').click()
        page.locator('.message').first.click()
        assert page.locator('#reading').is_visible()
        page.screenshot(path=str(out/'compact.png'))
        assert not errors, errors
        browser.close()
        print('Browser checks passed: themes, attachment previews, Raindrop browse/save/privacy, Jetstar status and compact reading.')

if __name__=='__main__': main()
