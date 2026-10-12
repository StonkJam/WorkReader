// Runtime checks with a minimal simulated document; these are not browser/rendering QA.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../WorkReader.html'),'utf8');
const match=html.match(/<script>([\s\S]*?)<\/script>/);assert(match,'Reader has an inline script');
assert(!/<script[^>]+src=/i.test(html),'No external script dependency');
const elements=new Map();
function element(id){if(!elements.has(id))elements.set(id,{id,value:'',innerHTML:'',textContent:'',disabled:false,open:false,className:'',dataset:{},classList:{add(){},remove(){},toggle(){},contains(){return false;}},addEventListener(){},setAttribute(){},showModal(){this.open=true;},close(){this.open=false;},appendChild(){},select(){},click(){}});return elements.get(id);}
for(const m of html.matchAll(/id="([^"]+)"/g))element(m[1]);
element('sort').value='new';element('type').value='all';element('fresh').value='all';
const storage=new Map();let fetchMode='failure';const rdCalls=[];
const context=vm.createContext({console,Intl,Date,JSON,Math,Number,String,Set,Map,Array,Object,RegExp,URL,URLSearchParams,Blob,AbortController,Promise,
  localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)},
  document:{body:{classList:{toggle(){}}},getElementById:element,addEventListener(){},querySelector(){return null;},createElement:()=>element('temporary')},
  location:{protocol:'file:',href:'file:///usb/WorkReader.html'},navigator:{},CSS:{escape:x=>x},
  setTimeout:()=>1,clearTimeout(){},setInterval:()=>1,
  fetch:async(url,options)=>{if(String(url).startsWith('https://api.raindrop.io/rest/v1/')){rdCalls.push({url,options});let items=[];if(url.endsWith('/collections'))items=[{_id:42,title:'My collection'}];else if(url.endsWith('/collections/childrens'))items=[{_id:43,title:'Child collection',parent:{$id:42}}];else if(url.includes('/raindrops/'))items=[{_id:999,title:'Private test bookmark',link:'https://private.example/bookmark',created:'2026-10-12T00:00:00Z',cover:'https://private.example/cover.png',collection:{$id:42}}];return {ok:true,json:async()=>({result:true,items,item:{_id:1000}})};}if(fetchMode==='failure')throw Error('Network blocked');return {ok:true,text:async()=>JSON.stringify({schema_version:1,generated_at:'2026-10-12T00:00:00Z',sources:[],items:[]})};}
});
vm.runInContext(match[1],context,{timeout:3000});
const run=s=>vm.runInContext(s,context,{timeout:1000});
assert(run('state.snapshot.items.length')>0,'Bundled live snapshot loads');
assert(element('sidebar').innerHTML.includes('OzBargain'),'Source folders render');
assert(element('reading').innerHTML.includes('Your deal inbox'),'Empty reading pane renders');
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
run("state.previewed.clear();state.folder='jetstar';state.selected=null;renderReading()");
assert(element('reading').innerHTML.includes('Automatic scan unavailable'),'Failed Jetstar scan is explained');
run("state.folder='inbox';state.selected=state.snapshot.items[0].key;state.images=true;$('search').value='remember-search';$('list').scrollTop=140;$('reading').scrollTop=80;$('settings-dialog').showModal();setCoverMode(true)");
assert(run('state.coverMode'));assert.equal(element('settings-dialog').open,false,'Cover closes dialogs');assert.equal(element('search').value,'');assert.equal(element('search').disabled,true);assert(!element('reading').innerHTML.includes('images.example'));assert(!element('sidebar').innerHTML.includes('OzBargain'));assert(element('list').innerHTML.includes('Weekly planning notes'));assert(!run('JSON.stringify(exportData())').includes('SAMPLE_MAIL'),'Fictional mailbox never exported');
run("render();renderList();renderReading();renderStatus();toast('Potentially revealing status')");assert.equal(element('status').textContent,'All folders are up to date','Background renders keep cover');
run('setCoverMode(false)');assert.equal(element('search').value,'remember-search');assert.equal(element('list').scrollTop,140);assert.equal(element('reading').scrollTop,80);assert.equal(run('state.images'),false);assert.equal(run('state.previewed.size'),0,'Previews remain collapsed on return');
run("$('search').value='';state.idleMinutes=2;cover.lastActivity=1000;checkIdle(120999)");assert(!run('state.coverMode'),'Does not cover before timeout');run('checkIdle(121000)');assert(run('state.coverMode'),'Covers at configured idle deadline');run('setCoverMode(false);state.idleMinutes=0;cover.lastActivity=0;checkIdle(999999999)');assert(!run('state.coverMode'),'Zero disables timeout');run('state.idleMinutes=2');
const before=run('state.snapshot.items.length');
run("state.dataUrl='https://raw.githubusercontent.com/example/workreader/main/data/deals.json'");
(async()=>{await run('loadRemote()');assert.equal(run('state.snapshot.items.length'),before,'Failed refresh retains data');assert.equal(run('state.loading'),false);
element('rd-token').value='TEST-SECRET-TOKEN';await run('rdConnect()');assert.equal(element('rd-token').value,'','Token input cleared');assert.equal(run('rd.collections.length'),2,'Root and nested collections loaded');assert.equal(run('rd.items.length'),1);run("selectItem('raindrop:999')");
assert.equal(run('visibleItems().length'),1,'Private bookmarks displayed');assert(!JSON.stringify([...storage]).includes('TEST-SECRET-TOKEN'));assert(!JSON.stringify([...storage]).includes('Private test bookmark'));assert(!run('JSON.stringify(exportData())').includes('private.example'));assert(!run('JSON.stringify(exportData())').includes('raindrop:999'));
run('state.folder="inbox";state.selected=state.snapshot.items[0].key;rdOpenSave()');element('rd-save-collection').value='42';await run('rdSave()');const post=rdCalls.find(c=>c.options.method==='POST');assert(post,'Save performs explicit API POST');assert.equal(JSON.parse(post.options.body).collection.$id,42);assert(rdCalls.every(c=>c.options.credentials==='omit'&&c.options.redirect==='error'&&c.options.headers.Authorization==='Bearer TEST-SECRET-TOKEN'));
run('rdDisconnect()');assert.equal(run('rd.items.length'),0);assert.equal(run('rd.token'),'');assert(!run('publicReadKeys().join()').includes('raindrop:'));
fetchMode='success';await run('loadRemote()');assert.equal(run('state.snapshot.items.length'),0,'Valid remote snapshot replaces data');console.log('Reader runtime checks passed, including image consent, Jetstar failure state, Raindrop browse/save and private-data isolation.');})().catch(e=>{console.error(e);process.exitCode=1;});
