"""GitHub Chromium checks for stable chrome, actions and snapshot failover."""
import base64
import json
from pathlib import Path
from datetime import datetime,timezone,timedelta
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aWQAAAABJRU5ErkJggg==')
def main():
    out=ROOT/'diagnostics/ui';out.mkdir(parents=True,exist_ok=True)
    snapshot=json.loads((ROOT/'data/deals.json').read_text())
    remote=json.loads(json.dumps(snapshot));now=datetime.now(timezone.utc).isoformat()
    remote['generated_at']=now
    for source in remote['sources']:
        if source.get('status')=='ok':source['last_success']=now
    remote['items'].append({**snapshot['items'][0],'group':'reddit','kind':'post','url':'https://www.reddit.com/r/testreader/comments/refresh/','title':'Synthetic refresh post','image':'','videos':[],'attachments':[],'first_seen':now,'published':now,'source_ids':['reddit-custom']})
    remote['sources'].append({'id':'reddit-custom','group':'reddit','name':'r/testreader','url':'https://www.reddit.com/r/testreader/.rss','status':'ok','count':1})
    with sync_playwright() as pw:
        browser=pw.chromium.launch();context=browser.new_context(viewport={'width':1440,'height':900})
        images=[];posts=[];errors=[];video_requests=[];network={'api':False,'reject_token':False}
        context.route('https://raw.githubusercontent.com/**',lambda route:route.abort())
        def github(route):
            if network['api']:route.fulfill(json=remote,headers={'Access-Control-Allow-Origin':'*'})
            else:route.abort()
        context.route('https://api.github.com/**',github)
        def image(route):images.append(route.request.url);route.fulfill(body=PNG,content_type='image/png')
        context.route('https://images.example/**',image)
        def video(route):video_requests.append(route.request.url);route.fulfill(body=b'',content_type='video/mp4')
        context.route('https://video.example/**',video)
        context.route('https://embed.reddit.com/**',lambda route:route.fulfill(body='<html><body>Test Reddit player</body></html>',content_type='text/html'))
        context.route('https://player.vimeo.com/**',lambda route:(video_requests.append(route.request.url),route.fulfill(body='<html><body>Test player</body></html>',content_type='text/html'))[-1])
        def raindrop(route):
            if network['reject_token']:route.fulfill(status=401,json={'result':False});return
            path=route.request.url.split('/rest/v1')[1]
            if path=='/collections':data={'result':True,'items':[{'_id':42,'title':'Travel','count':1}]}
            elif path=='/collections/childrens':data={'result':True,'items':[{'_id':43,'title':'Hotels','parent':{'$id':42}}]}
            elif path.startswith('/raindrops/'):data={'result':True,'items':[{'_id':999,'title':'Private test bookmark','link':'https://private.example/bookmark','created':'2026-10-12T00:00:00Z','cover':'https://images.example/private.png','collection':{'$id':42}}]}
            elif path=='/raindrop' and route.request.method=='POST':posts.append(route.request.post_data_json);data={'result':True,'item':{'_id':1000}}
            else:raise AssertionError(path)
            route.fulfill(json=data,headers={'Access-Control-Allow-Origin':'*'})
        context.route('https://api.raindrop.io/**',raindrop)
        old_cache=json.loads(json.dumps(snapshot));old_cache['generated_at']='2000-01-01T00:00:00Z';old_cache['items']=[]
        context.add_init_script("localStorage.setItem('workreader:snapshot',"+json.dumps(json.dumps(old_cache))+");")
        page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto((ROOT/'WorkReader.html').as_uri());page.wait_for_function('!state.loading')
        assert page.evaluate('state.coverMode'), 'Startup is mail view'
        assert page.evaluate('state.snapshot.generated_at')==snapshot['generated_at'], 'New bundle overrides older local snapshot'
        assert page.evaluate('cover.timer===null'), 'No idle countdown in mail view'
        assert 'OzBargain' not in page.locator('#sidebar').inner_text()
        assert page.locator('.message .subject').all_text_contents()==page.evaluate('visibleItems().map(i=>mailFor(i).subject)')
        assert page.locator('.preview-block img').count()==0
        assert page.evaluate('!!state.selected'), 'Startup previews a fictional message without marking it read'
        assert page.locator('#filter-panel').is_hidden()
        page.locator('#filter-toggle').click();assert page.locator('#filter-panel').is_visible()
        page.locator('#filter-toggle').click();assert page.locator('#filter-panel').is_hidden()
        selected_at_refresh=page.evaluate('state.selected');initial_count=page.locator('.message').count()
        network['api']=True
        page.evaluate("$('list').scrollTop=50")
        page.locator('#refresh').click();page.wait_for_function('!state.loading')
        assert page.evaluate('state.coverMode') and page.evaluate('state.selected')==selected_at_refresh
        assert page.locator('.message').count()==initial_count+1, 'Refresh renders new rows in mail view'
        assert page.locator('#list').evaluate('(e)=>e.scrollTop')==50
        assert 'Synthetic refresh post' not in page.locator('#list').inner_text()
        assert 'r/testreader' not in page.locator('#sidebar').inner_text()
        assert '1 new messages' in page.locator('#status').inner_text()
        page.locator('#refresh').click();page.wait_for_function('!state.loading')
        assert 'No newer snapshot' in page.locator('#status').inner_text()
        assert 'Up to date' not in page.locator('#status').inner_text()
        remote['generated_at']='2000-01-01T00:00:00Z'
        page.locator('#refresh').click();page.wait_for_function('!state.loading')
        assert page.locator('.message').count()==initial_count+1
        assert 'kept newer' in page.locator('#status').inner_text()
        remote['generated_at']=now
        old_success=datetime.now(timezone.utc)-timedelta(hours=5)
        for source in remote['sources']:
            if source.get('status')=='ok':source['last_success']=old_success.isoformat()
        page.locator('#refresh').click();page.wait_for_function('!state.loading')
        assert 'Collection overdue' in page.locator('#status').inner_text()
        page.locator('#status-details').click()
        assert 'Collection overdue' in page.locator('#collection-status').inner_text()
        assert page.locator('#scan-link').get_attribute('href')=='https://github.com/StonkJam/WorkReader/actions/workflows/scan.yml'
        page.locator('#sources-dialog .close').click()
        for source in remote['sources']:
            if source.get('status')=='ok':source['last_success']=now
        page.locator('#refresh').click();page.wait_for_function('!state.loading')
        network['api']=False
        page.locator('#refresh').click();page.wait_for_function('!state.loading')
        assert page.locator('.message').count()==initial_count+1, 'Failed refresh preserves displayed cached rows'
        assert page.locator('#status-details').inner_text()=='Connection details'
        page.locator('#status-details').click();assert page.locator('#settings-dialog').is_visible()
        assert 'Could not update live messages' in page.locator('#sync-details').inner_text()
        page.locator('#settings-dialog .close').click()
        page.keyboard.press('Space')
        assert not page.evaluate('state.coverMode'), 'First Space opens reader'
        assert page.evaluate('cover.timer!==null'), 'Reader starts countdown'
        assert page.locator('#app-name').inner_text()=='Outlook'
        assert page.title()=='Inbox — Outlook'
        assert page.evaluate('uiScaleFactor()')==1.4
        assert page.locator('.statusbar').bounding_box()['y']+page.locator('.statusbar').bounding_box()['height']<=901
        assert page.locator('.brand .outlook-logo').count()==1
        assert page.locator('link[rel="icon"]').get_attribute('href').startswith('data:image/svg+xml,')
        assert page.locator('#toast').is_hidden(), 'Startup network failure is quiet'
        assert page.evaluate('!!state.syncError')
        assert page.evaluate('state.snapshot.items.length')==len(remote['items'])
        network['api']=True
        page.locator('#refresh').click();page.wait_for_function('!state.loading')
        assert page.evaluate('state.syncEndpoint')=='GitHub public API'
        assert not page.evaluate('state.syncError')
        page.evaluate("$('toast').classList.add('hidden')")
        page.locator('#sources-tab').click();page.locator('#add-source').click()
        page.locator('#source-subreddit').fill('r/AskReddit');page.locator('#source-order').select_option('new')
        page.locator('#prepare-source').click()
        request_url=page.locator('#source-request-link').get_attribute('href')
        assert request_url.startswith('https://github.com/StonkJam/WorkReader/issues/new?')
        assert 'askreddit' in request_url and 'new' in request_url
        page.locator('#source-subreddit').fill('../bad');page.locator('#prepare-source').click()
        assert page.locator('#source-request-link').is_hidden()
        page.locator('#source-kind').select_option('ozbargain');page.locator('#source-category').select_option('computing');page.locator('#prepare-source').click()
        assert 'computing' in page.locator('#source-request-link').get_attribute('href')
        page.locator('#add-source-dialog .close').click();page.locator('#sources-dialog .close').click()
        page.locator('.message').first.click()
        page.evaluate("currentItem().videos=[{url:'https://player.vimeo.com/video/123456789'},{url:'https://youtu.be/M7lc1UVf-VE'}];renderReading()")
        assert not video_requests and page.locator('.video-preview iframe').count()==0
        assert page.locator('[data-video-external]').inner_text().find('Open YouTube')>=0, 'USB YouTube opens original instead of broken embed'
        button=page.locator('[data-video-preview]').first;button.click()
        assert page.locator('.video-preview iframe').count()==1
        button=page.locator('[data-video-preview]').first;button.click();assert page.locator('.video-preview iframe').count()==0
        page.locator('[data-video-preview]').first.click();page.keyboard.press('Space')
        assert page.locator('.video-preview iframe').count()==0 and page.evaluate('videoPreviewed.size')==0
        page.keyboard.press('Space');assert page.locator('.video-preview iframe').count()==0
        page.evaluate("currentItem().videos=[{url:'https://video.example/file.mp4'}];renderReading()")
        before_video=len(video_requests);assert page.locator('.video-preview video').count()==0
        page.locator('[data-video-preview]').click()
        page.wait_for_function("document.querySelector('.video-preview')!==null")
        assert len(video_requests)>=before_video
        page.keyboard.press('Space');assert page.locator('.video-preview').count()==0
        page.keyboard.press('Space')
        page.evaluate("currentItem().videos=[{url:'https://v.redd.it/abcd'}];renderReading()")
        page.locator('[data-video-preview]').click()
        assert page.locator('.video-preview iframe').get_attribute('src').startswith('https://embed.reddit.com/r/testreader/comments/')
        page.keyboard.press('Space');assert page.locator('.video-preview iframe').count()==0
        page.keyboard.press('Space');page.evaluate('currentItem().videos=[];renderReading()')
        refresh=page.locator('#refresh').bounding_box();glyph=page.locator('#refresh .oi').bounding_box();ribbon=page.locator('.ribbon').bounding_box()
        assert 18<=glyph['width']/page.evaluate('uiScaleFactor()')<=22 and refresh['y']+refresh['height']<=ribbon['y']+ribbon['height']
        page.locator('.message').first.click()
        page.evaluate("state.images=false;state.previewed.clear();currentItem().attachments=[{url:'https://images.example/public.png',name:'public.png'}];currentItem().image='';renderReading()")
        assert page.locator('.preview-block img').count()==0 and not images
        page.screenshot(path=str(out/'outlook-light.png'))
        page.locator('#theme').click();page.wait_for_function("getComputedStyle(document.querySelector('.folder.active')).backgroundColor==='rgb(0, 0, 0)'")
        page.get_by_text('Click to preview',exact=True).click();page.wait_for_selector('.preview-block img')
        page.get_by_text('Click to close',exact=True).click()
        assert page.locator('.preview-block img').count()==0, 'Same card closes image'
        page.get_by_text('Click to preview',exact=True).click();page.wait_for_selector('.preview-block img')
        selected=page.evaluate('state.selected');subject=page.locator('.read-head h2').inner_text()
        subjects=page.locator('.message .subject').all_text_contents();senders=page.locator('.message .sender').all_text_contents()
        sidebar=page.locator('#sidebar').inner_html();toolbar=page.locator('.ribbon').inner_html();count=page.locator('.message').count()
        folder_rectangles=page.locator('.folder').evaluate_all('(rows)=>rows.map(e=>{let r=e.getBoundingClientRect();return [r.x,r.y,r.width,r.height]})')
        rectangles=page.locator('.message').evaluate_all('(rows)=>rows.map(e=>{let r=e.getBoundingClientRect();return [r.x,r.y,r.width,r.height]})')
        page.screenshot(path=str(out/'subtle-reading.png'))
        page.keyboard.press('Space');assert page.evaluate('state.coverMode')
        assert page.locator('.preview-block img').count()==0
        assert 'OzBargain' not in page.locator('#sidebar').inner_text()
        assert 'Team circulars' in page.locator('#sidebar').inner_text()
        assert page.locator('.ribbon').inner_html()==toolbar
        assert page.locator('.message .subject').all_text_contents()==page.evaluate('visibleItems().map(i=>mailFor(i).subject)')
        assert page.locator('.message .sender').all_text_contents()==senders
        assert page.locator('.message').count()==count
        assert page.locator('.read-head h2').inner_text()==page.evaluate('mailFor(currentItem()).subject')
        assert page.locator('.message').evaluate_all('(rows)=>rows.map(e=>{let r=e.getBoundingClientRect();return [r.x,r.y,r.width,r.height]})')==rectangles
        assert page.locator('.folder').evaluate_all('(rows)=>rows.map(e=>{let r=e.getBoundingClientRect();return [r.x,r.y,r.width,r.height]})')==folder_rectangles
        assert page.evaluate('state.selected')==selected
        page.screenshot(path=str(out/'subtle-mail.png'))
        page.keyboard.press('Space');assert not page.evaluate('state.coverMode')
        assert page.locator('#sidebar').inner_html()==sidebar
        assert page.locator('.message .subject').all_text_contents()==subjects
        assert page.locator('.read-head h2').inner_text()==subject
        assert page.locator('.preview-block img').count()==0
        # Right-click operations use the clicked row, including a row that is not selected.
        row=page.locator('.message').nth(1);key=row.get_attribute('data-item');row.click(button='right')
        assert page.locator('#message-menu').is_visible()
        menu=page.locator('#message-menu').bounding_box()
        assert menu['x']+menu['width']<=1441 and menu['y']+menu['height']<=901
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
        page.locator('#settings-dialog .close').click()
        page.evaluate('state.idleMinutes=.005;recordActivity()')
        page.evaluate('cover.lastActivity=Date.now()-1000')
        page.mouse.move(850,450)
        page.wait_for_function('Date.now()-cover.lastActivity<200')
        assert not page.evaluate('state.coverMode'), 'Mouse move resets activity without switching mode'
        page.wait_for_function('state.coverMode',timeout=3000)
        page.mouse.move(860,460)
        assert page.evaluate('state.coverMode'), 'Mouse move does not reveal reader from mail view'
        assert page.evaluate('cover.timer===null')
        page.evaluate('state.idleMinutes=2')
        page.locator('#cover-toggle').click();assert not page.evaluate('state.coverMode')
        page.locator('#search').fill('held query');page.locator('#settings-tab').click();page.evaluate('cover.lastActivity=Date.now()-120001;checkIdle()')
        assert page.locator('dialog[open]').count()==0
        page.locator('#cover-toggle').click();assert page.locator('#search').input_value()=='held query';page.locator('#search').fill('')
        page.evaluate('setCoverMode(true)')
        source_row=page.locator('.message').nth(2);pending_key=source_row.get_attribute('data-item')
        pending_title=page.evaluate('(key)=>state.snapshot.items.find(i=>i.key===key).title',pending_key)
        original_selected=page.evaluate('state.selected')
        source_row.click(button='right');page.get_by_role('menuitem',name='Save to Raindrop').click()
        assert page.locator('#raindrop-dialog').is_visible()
        network['reject_token']=True
        page.locator('#rd-token').fill('SYNTHETIC-INVALID');page.locator('#rd-connect').click()
        page.wait_for_function('!rd.token')
        assert 'rejected this token' in page.locator('#rd-state').inner_text()
        assert page.evaluate('!!rd.pendingSave'), 'Failed connection retains clicked item for retry'
        network['reject_token']=False
        page.locator('#rd-token').fill('SYNTHETIC-TEST-TOKEN');page.locator('#rd-connect').click()
        page.wait_for_selector('#rd-save-dialog[open]')
        assert page.locator('#rd-save-title').input_value()==pending_title
        assert page.evaluate('state.selected')==original_selected, 'Connecting to save does not change current selection'
        page.locator('#rd-save-collection').select_option('42');page.locator('#rd-save-submit').click()
        page.wait_for_function('!document.getElementById("rd-save-dialog").open')
        assert posts[-1]['title']==pending_title and posts[-1]['collection']['$id']==42
        page.evaluate('setCoverMode(false)')
        page.locator('#rail-raindrop').click();page.wait_for_selector('[data-item="raindrop:999"]')
        assert page.locator('#rd-token').input_value()=='';page.locator('[data-item="raindrop:999"]').click()
        assert 'Private test bookmark' in page.locator('#reading').inner_text();page.evaluate('setCoverMode(true)');assert 'Private test bookmark' not in page.locator('#reading').inner_text();page.evaluate('setCoverMode(false)')
        assert 'Private test bookmark' in page.locator('#reading').inner_text();assert not any('private.png' in url for url in images)
        assert 'private.example' not in page.evaluate('JSON.stringify(exportData())');assert 'SYNTHETIC' not in page.evaluate('JSON.stringify(localStorage)');assert 'raindrop:999' not in page.evaluate('JSON.stringify(localStorage)')
        page.locator('[data-folder="inbox"]').click();page.locator('.message').first.click(button='right');page.get_by_role('menuitem',name='Save to Raindrop').click()
        page.locator('#rd-save-collection').select_option('42');page.locator('#rd-save-submit').click();page.wait_for_function("!document.getElementById('rd-save-dialog').open")
        assert len(posts)==2 and posts[0]['collection']['$id']==42
        page.locator('#raindrop').click();page.locator('#rd-disconnect').click();assert page.evaluate("rd.token===''&&rd.items.length===0");page.locator('#raindrop-dialog .close').click()
        page.locator('[data-folder="jetstar"]').click();page.locator('.message').filter(has_text='Bali Return').first.click()
        assert page.locator('.fare-table .sydney-row').inner_text().find('$459')>=0
        assert page.locator('.fare-table tr').nth(1).inner_text().startswith('Sydney')
        page.screenshot(path=str(out/'jetstar-offer.png'))
        page.set_viewport_size({'width':700,'height':850});page.locator('[data-folder="ozbargain"]').click();page.locator('.message').first.click();assert page.locator('#reading').is_visible();page.screenshot(path=str(out/'compact.png'))
        page.set_viewport_size({'width':3440,'height':1440})
        page.evaluate('state.uiScale=140;applyUiScale()')
        assert 239<=page.locator('#sidebar').bounding_box()['width']<=243
        assert 461<=page.locator('.messages').bounding_box()['width']<=463
        assert page.locator('.statusbar').bounding_box()['y']+page.locator('.statusbar').bounding_box()['height']<=1441
        assert 80<=page.locator('.message').first.bounding_box()['height']<=82
        assert page.locator('#list').bounding_box()['y']-page.locator('.messages').bounding_box()['y']<48
        page.screenshot(path=str(out/'outlook-scale-ultrawide.png'))
        page.locator('#settings-tab').click();page.locator('#ui-scale').select_option('125')
        assert page.evaluate('uiScaleFactor()')==1.25
        assert page.evaluate("JSON.parse(localStorage.getItem('workreader:uiScale'))")==125
        assert page.evaluate('exportData().preferences.uiScale')==125
        page.locator('#settings-dialog .close').click()
        assert not errors,errors
        browser.close();print('Browser checks passed: stable chrome/row geometry, image toggle, context menu, idle timeout, official API failover, Raindrop privacy and Jetstar table.')
if __name__=='__main__':main()
