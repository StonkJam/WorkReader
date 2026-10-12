// Runtime checks with a minimal simulated document; these are not browser/rendering QA.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../WorkReader.html'),'utf8');
const match=html.match(/<script>([\s\S]*?)<\/script>/);assert(match,'Reader has an inline script');
assert(!/<script[^>]+src=/i.test(html),'No external script dependency');
const elements=new Map();
function element(id){if(!elements.has(id))elements.set(id,{id,value:'',innerHTML:'',textContent:'',disabled:false,open:false,className:'',dataset:{},classList:{add(){},remove(){},toggle(){}},addEventListener(){},setAttribute(){},showModal(){this.open=true;},close(){this.open=false;},appendChild(){},select(){},click(){}});return elements.get(id);}
for(const m of html.matchAll(/id="([^"]+)"/g))element(m[1]);
element('sort').value='new';element('type').value='all';element('fresh').value='all';
const storage=new Map();let fetchMode='failure';
const context=vm.createContext({console,Intl,Date,JSON,Math,Number,String,Set,Map,Array,Object,RegExp,URL,Blob,AbortController,Promise,
  localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)},
  document:{body:{classList:{toggle(){}}},getElementById:element,addEventListener(){},querySelector(){return null;},createElement:()=>element('temporary')},
  location:{protocol:'file:',href:'file:///usb/WorkReader.html'},navigator:{},CSS:{escape:x=>x},
  setTimeout:()=>1,clearTimeout(){},setInterval:()=>1,
  fetch:async()=>{if(fetchMode==='failure')throw Error('Network blocked');return {ok:true,text:async()=>JSON.stringify({schema_version:1,generated_at:'2026-10-12T00:00:00Z',sources:[],items:[]})};}
});
vm.runInContext(match[1],context,{timeout:3000});
const run=s=>vm.runInContext(s,context,{timeout:1000});
assert(run('state.snapshot.items.length')>0,'Bundled live snapshot loads');
assert(element('sidebar').innerHTML.includes('OzBargain'),'Source folders render');
assert(element('reading').innerHTML.includes('Your deal inbox'),'Empty reading pane renders');
run("state.folder='ozbargain';render()");assert(run("visibleItems().every(i=>i.group==='ozbargain')"));
run("state.folder='reddit';render()");assert.equal(run('visibleItems().length'),25);
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
const before=run('state.snapshot.items.length');
run("state.dataUrl='https://raw.githubusercontent.com/example/workreader/main/data/deals.json'");
(async()=>{await run('loadRemote()');assert.equal(run('state.snapshot.items.length'),before,'Failed refresh retains data');assert.equal(run('state.loading'),false);fetchMode='success';await run('loadRemote()');assert.equal(run('state.snapshot.items.length'),0,'Valid remote snapshot replaces data');console.log('Reader runtime checks passed: startup, folders, search, saved/unread, prices, import safety, bookmarklet, watches, refresh failure/success.');})().catch(e=>{console.error(e);process.exitCode=1;});
