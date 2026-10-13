// Runtime checks with a minimal simulated document; these are not browser/rendering QA.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../WorkReader.html'),'utf8');
const match=html.match(/<script>([\s\S]*?)<\/script>/);assert(match,'Reader has an inline script');
assert(!/<script[^>]+src=/i.test(html),'No external script dependency');
const elements=new Map();
function element(id){if(!elements.has(id))elements.set(id,{id,value:'',style:{},innerHTML:'',textContent:'',disabled:false,open:false,className:'',dataset:{},classList:{add(){},remove(){},toggle(){},contains(){return false;}},addEventListener(){},setAttribute(){},showModal(){this.open=true;},close(){this.open=false;},appendChild(){},select(){},click(){}});return elements.get(id);}
for(const m of html.matchAll(/id="([^"]+)"/g))element(m[1]);
element('sort').value='new';element('type').value='all';element('fresh').value='all';
const storage=new Map(),fakeFreshTime=new Date(Date.now()+1000).toISOString();let fetchMode='failure';const rdCalls=[],dataCalls=[],ghCalls=[];
const context=vm.createContext({console,Intl,Date,JSON,Math,Number,String,Set,Map,Array,Object,RegExp,URL,URLSearchParams,Blob,AbortController,Promise,
  localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)},
  document:{documentElement:{style:{setProperty(){}}},body:{classList:{toggle(){}}},getElementById:element,addEventListener(){},querySelector(){return null;},querySelectorAll(){return [];},createElement:()=>element('temporary')},
  window:{addEventListener(){},innerWidth:1440,innerHeight:900},location:{protocol:'file:',href:'file:///usb/WorkReader.html'},navigator:{},CSS:{escape:x=>x},
  setTimeout:()=>1,clearTimeout(){},setInterval:()=>1,
  fetch:async(url,options)=>{if(String(url).includes('/actions/')){ghCalls.push({url,options});let d=url.endsWith('/dispatches')?{workflow_run_id:700}:url.endsWith('/actions/runs/700')?{status:'queued'}:{id:381674250,state:'active'};return {ok:true,status:200,json:async()=>d};}if(String(url).startsWith('https://api.raindrop.io/rest/v1/')){rdCalls.push({url,options});let items=[];if(url.endsWith('/collections'))items=[{_id:42,title:'My collection'}];else if(url.endsWith('/collections/childrens'))items=[{_id:43,title:'Child collection',parent:{$id:42}}];else if(url.includes('/raindrops/'))items=[{_id:999,title:'Private test bookmark',link:'https://private.example/bookmark',created:'2026-10-12T00:00:00Z',cover:'https://private.example/cover.png',collection:{$id:42}}];return {ok:true,json:async()=>({result:true,items,item:{_id:1000}})};}dataCalls.push(String(url));if(fetchMode==='failure'||fetchMode==='api-only'&&!String(url).startsWith('https://api.github.com/'))throw Error('Network unavailable');return {ok:true,text:async()=>JSON.stringify({schema_version:1,generated_at:fetchMode==='older'?'2000-01-01T00:00:00Z':fakeFreshTime,sources:[],items:[]})};}
});
vm.runInContext(match[1],context,{timeout:3000});
const run=s=>vm.runInContext(s,context,{timeout:1000});
assert(run('state.snapshot.items.length')>0,'Bundled live snapshot loads');
assert.equal(run('uiScaleFactor()'),1.4,'Default matches Outlook scale');assert.equal(run('exportData().preferences.uiScale'),140);assert(run('state.coverMode'),'Startup uses mail view');assert.equal(run('cover.timer'),null,'Idle timer does not run in mail view');assert.equal(run('state.images'),false,'Startup images are collapsed');assert(element('sidebar').innerHTML.includes('Team circulars'));run('setCoverMode(false)');
assert(element('sidebar').innerHTML.includes('OzBargain'),'Source folders render');
assert(run('!!state.selected'),'Startup previews a message');assert(!run('state.read.has(state.selected)'),'Startup preview does not mark a message read');run('state.selected=null;renderReading()');assert(element('reading').innerHTML.includes('Select a message'),'Empty reading pane renders');
run("state.folder='ozbargain';render()");assert(run("visibleItems().every(i=>i.group==='ozbargain')"));
run("state.folder='reddit';render()");assert.equal(run('visibleItems().length'),run("state.snapshot.items.filter(i=>i.group==='reddit').length"));
run("state.folder='inbox';$('search').value='unlikely-keyword-abcdef';renderList()");assert.equal(run('visibleItems().length'),0);run("$('search').value=''");
const first=run('state.snapshot.items[0].key');
run(`selectItem(${JSON.stringify(first)})`);assert(run(`state.read.has(${JSON.stringify(first)})`));
run(`toggleSave(${JSON.stringify(first)});state.folder='saved';render()`);assert.equal(run('visibleItems().length'),1);
run("state.folder='inbox';$('max-price').value='0'");assert(run('visibleItems().every(i=>typeof i.price===\'number\'&&i.price<=0)'));run("$('max-price').value=''");
assert(run("escapeText('<img src=x onerror=alert(1)>').includes('&lt;img')"),'Unsafe markup displayed as text');
assert.throws(()=>run("normalise({schema_version:1,sources:[],items:[{group:'ozbargain',title:'X',url:'javascript:alert(1)'}]})"));
assert.throws(()=>run("normalise({schema_version:1,sources:[],items:[{group:'__proto__',title:'X',url:'https://example.com'}]})"));
assert(run("isOld({checked_at:'invalid'})"),'Invalid date does not imply fresh');
assert(run("makeBookmarklet().startsWith('javascript:')"),'Capture bookmark built');
assert(run("safeUrl('https://user:pass@example.com')===''") ,'Credential-bearing links rejected');
assert(run("watchMatch({title:'iPad Pro',text:'256GB',tags:[],price:800},{query:'ipad pro',max:900})"));
assert(!run("watchMatch({title:'iPad Pro',text:'',tags:[],price:null},{query:'ipad',max:900})"));
run("state.images=false;state.snapshot.items[0].attachments=[{url:'https://images.example/photo.jpg',name:'photo.jpg'}];state.selected=state.snapshot.items[0].key;renderReading()");
assert(!element('reading').innerHTML.includes('<img '),'No image request before preview');
assert(element('reading').innerHTML.includes('Click to preview'));
run("state.previewed.add('https://images.example/photo.jpg');renderReading()");
assert(element('reading').innerHTML.includes('src="https://images.example/photo.jpg"'),'Explicit preview renders image');
run("togglePreview('https://images.example/photo.jpg')");assert(!element('reading').innerHTML.includes('<img '),'Same attachment card closes its preview');
run("state.folder='inbox';state.selected=state.snapshot.items[0].key;state.images=true;$('search').value='';render();$('list').scrollTop=140;$('reading').scrollTop=80;$('settings-dialog').showModal()");
const oldSidebar=element('sidebar').innerHTML,oldSubjects=element('list').innerHTML.match(/<div class="subject">[^<]*/g),oldCount=element('item-count').textContent;
run('setCoverMode(true)');assert(run('state.coverMode'));assert.equal(element('settings-dialog').open,false);assert.equal(element('search').disabled,false);assert(element('sidebar').innerHTML.includes('Team circulars'));assert(!element('sidebar').innerHTML.includes('OzBargain'));assert.notDeepEqual(element('list').innerHTML.match(/<div class="subject">[^<]*/g),oldSubjects,'Cover substitutes subjects');assert.equal(element('item-count').textContent,oldCount,'Row count unchanged');assert(!element('reading').innerHTML.includes('<img '));
assert.equal(element('list').scrollTop,140);assert.equal(element('reading').scrollTop,80);
run('render()');assert(element('sidebar').innerHTML.includes('Team circulars'),'Background render preserves neutral labels');
run('setCoverMode(false)');assert.equal(element('sidebar').innerHTML,oldSidebar,'Real labels restored');assert.deepEqual(element('list').innerHTML.match(/<div class="subject">[^<]*/g),oldSubjects,'Source subjects restored');assert.equal(element('list').scrollTop,140);assert.equal(element('reading').scrollTop,80);assert.equal(run('state.images'),false);assert.equal(run('state.previewed.size'),0);
assert(run("emailDraftLink({title:'Hello world',url:'https://example.com/post'}).startsWith('mailto:?subject=Hello%20world')"));
run(`setRead(${JSON.stringify(first)},false)`);assert(!run(`state.read.has(${JSON.stringify(first)})`));run(`setRead(${JSON.stringify(first)},true)`);assert(run(`state.read.has(${JSON.stringify(first)})`));
assert.equal(run("jetstarFares({group:'jetstar',title:'Bali Return PER $247, SYD $459, BNE $447'})[0].code"),'SYD');assert.equal(run("jetstarFares({group:'jetstar',title:'Bali PER $300; Nadi PER $200'}).length"),2,'Separate destinations are preserved');assert.equal(run("jetstarFares({group:'jetstar',title:'Sale SYD 2027'}).length"),0,'Years are not fares');assert.equal(run("jetstarFares({group:'jetstar',title:'US$ price SYD $300'}).length"),0);
run("$('search').value='';state.idleMinutes=2;cover.lastActivity=1000;checkIdle(120999)");assert(!run('state.coverMode'),'Does not cover before timeout');run('checkIdle(121000)');assert(run('state.coverMode'),'Covers at configured idle deadline');run('setCoverMode(false);state.idleMinutes=0;cover.lastActivity=0;checkIdle(999999999)');assert(!run('state.coverMode'),'Zero disables timeout');run('state.idleMinutes=2');
assert.equal(run("videoLink('https://youtu.be/M7lc1UVf-VE').type"),'youtube');
assert.equal(run("videoLink('https://player.vimeo.com/video/123456789').type"),'vimeo');
assert.equal(run("videoLink('https://example.com/video.webm').type"),'file');
assert.equal(run("videoLink('https://youtube.com.evil.example/watch?v=M7lc1UVf-VE')"),null);
assert.equal(run("videoLink('javascript:alert(1)')"),null);assert(run("redditVideoEmbed({url:'https://www.reddit.com/r/australia/comments/abc123/post/' }).startsWith('https://embed.reddit.com/')"));assert.equal(run("redditVideoEmbed({url:'https://evil.example/r/australia/comments/abc123/'})"),'');
run("$('source-kind').value='subreddit';$('source-subreddit').value='r/AskReddit';$('source-order').value='new'");
assert.equal(run('sourceRequest().subreddit'),'askreddit');
assert(run("sourceRequestLink(sourceRequest(),'StonkJam/WorkReader').startsWith('https://github.com/StonkJam/WorkReader/issues/new?')"));
run("$('source-subreddit').value='../bad'");assert.throws(()=>run('sourceRequest()'));
run("$('source-kind').value='ozbargain';$('source-category').value='computing'");assert.equal(run('sourceRequest().category'),'computing');
assert.equal(run("initialSnapshot({...BUNDLED,generated_at:'2000-01-01T00:00:00Z',items:[]},BUNDLED).items.length"),run('BUNDLED.items.length'),'New downloaded bundle overrides stale local cache');
assert(run('dataFreshness(snapshotTime(state.snapshot)+7200000).overdue'),'Old source data is overdue');
const before=run('state.snapshot.items.length');
run("state.dataUrl='https://raw.githubusercontent.com/example/workreader/main/data/deals.json'");
(async()=>{for(let step=0;step<10;step++)await Promise.resolve();await run('loadRemote()');assert.equal(run('state.snapshot.items.length'),before,'Failed refresh retains data');assert.equal(run('state.loading'),false);
element('rd-token').value='TEST-SECRET-TOKEN';await run('rdConnect()');assert.equal(element('rd-token').value,'','Token input cleared');assert.equal(run('rd.collections.length'),2,'Root and nested collections loaded');assert.equal(run('rd.items.length'),1);run("selectItem('raindrop:999')");
assert.equal(run('visibleItems().length'),1,'Private bookmarks displayed');assert(!JSON.stringify([...storage]).includes('TEST-SECRET-TOKEN'));assert(!JSON.stringify([...storage]).includes('Private test bookmark'));assert(!run('JSON.stringify(exportData())').includes('private.example'));assert(!run('JSON.stringify(exportData())').includes('raindrop:999'));
run('state.folder="inbox";state.selected=state.snapshot.items[0].key;rdOpenSave()');element('rd-save-collection').value='42';await run('rdSave()');const post=rdCalls.find(c=>c.options.method==='POST');assert(post,'Save performs explicit API POST');assert.equal(JSON.parse(post.options.body).collection.$id,42);assert(rdCalls.every(c=>c.options.credentials==='omit'&&c.options.redirect==='error'&&c.options.headers.Authorization==='Bearer TEST-SECRET-TOKEN'));
run('rdDisconnect()');assert.equal(run('rd.items.length'),0);assert.equal(run('rd.token'),'');assert(!run('publicReadKeys().join()').includes('raindrop:'));
run('setCoverMode(true)');fetchMode='older';await run('loadRemote()');assert.equal(run('state.snapshot.items.length'),before,'Old server response cannot roll back newer cached data');assert(run("state.syncMessage.includes('kept newer')"));fetchMode='api-only';await run('loadRemote()');assert.equal(element('item-count').textContent,'0 in folder','Successful refresh updates mail-view rows and counts');assert(run('state.coverMode'),'Refresh preserves mail mode');assert.equal(run('state.syncEndpoint'),'GitHub public API','Official API fallback succeeds');assert(dataCalls.some(u=>u.includes('/repos/example/workreader/contents/data/deals.json?ref=main')));fetchMode='success';await run('loadRemote()');assert(run("state.syncMessage==='No newer snapshot'"),'Same snapshot is never called up to date');assert.equal(run('state.snapshot.items.length'),0,'Valid remote snapshot replaces data');run("state.dataUrl='https://raw.githubusercontent.com/StonkJam/WorkReader/main/data/deals.json';ghScan.token='GH-SESSION-SECRET';ghScan.repo='StonkJam/WorkReader'");await run('ghStartCollection()');assert.equal(ghCalls.find(c=>c.options.method==='POST').url,'https://api.github.com/repos/StonkJam/WorkReader/actions/workflows/scan.yml/dispatches');assert.equal(JSON.parse(ghCalls.find(c=>c.options.method==='POST').options.body).inputs.mode,'quick');assert(run('ghScan.active'),'Queued collection is still active');assert(!JSON.stringify([...storage]).includes('GH-SESSION-SECRET'));assert(!run('JSON.stringify(exportData())').includes('GH-SESSION-SECRET'));await assert.rejects(run("ghActions('/contents/config.json','POST',{})"));run('ghDisconnect()');assert.equal(run('ghScan.token'),'');assert.equal(run('ghScan.active'),false);assert.equal(run('collectionRun({collection_run:{id:700}}).id'),700);assert.equal(run("collectionRun({collection_run:{id:'700'}})"),null);console.log('Reader runtime checks passed, including image consent, Jetstar failure state, Raindrop browse/save and private-data isolation.');})().catch(e=>{console.error(e);process.exitCode=1;});
