/* Rendered district directory, live destinations and mobile search. MIT. */
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),{createHash}=require('crypto');
const base=process.env.MODEL_BASE_URL||'http://127.0.0.1:8782/',output=process.env.QA_OUTPUT_DIR||__dirname;
const sha=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex');
(async()=>{const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});try{
 const page=await browser.newPage({viewport:{width:1280,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'landmarks.html');
 const cards=await page.locator('.landmark-card[data-landmark]').evaluateAll(nodes=>nodes.map(node=>({id:node.dataset.landmark,district:node.closest('.landmark-group').id,links:[...node.querySelectorAll('a')].map(a=>a.getAttribute('href')),name:node.querySelector('h3').textContent})));
 const city=cards.filter(r=>r.links.some(h=>h.startsWith('index.html#landmark=')));assert.equal(city.length,70);assert.equal(new Set(city.map(r=>r.id)).size,70);assert.equal(new Set(city.map(r=>r.district)).size,16);
 const inventory=JSON.parse(fs.readFileSync(path.join(__dirname,'inventory.json')));
 for(const row of inventory.records.filter(r=>!r.already_in_city)){const card=city.find(c=>c.id===row.id);assert.equal(card.district,'district-'+row.districtId);assert.ok(card.links.includes('index.html#landmark='+row.id+'&mode=overview'));assert.ok(card.links.includes(row.individual_page));}
 await page.screenshot({path:path.join(output,'browser-directory-desktop.png')});
 await page.setViewportSize({width:390,height:844});
 const layout=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth}));assert.equal(layout.width,390);assert.ok(layout.scrollWidth<=390);
 await page.fill('#landmark-search','崇明');
 const visible=await page.locator('.landmark-card[data-landmark]:visible').evaluateAll(nodes=>nodes.map(n=>n.dataset.landmark));assert.equal(visible.length,20);
 await page.screenshot({path:path.join(output,'browser-directory-mobile.png')});
 await page.fill('#landmark-search','永安');const wing=await page.locator('.landmark-card[data-landmark]:visible').evaluateAll(nodes=>nodes.map(n=>n.dataset.landmark));assert.deepEqual(wing,['huangpu-old-wing-on-company']);assert.deepEqual(errors,[]);
 const directory=path.resolve(__dirname,'../../../landmarks.html');
 fs.writeFileSync(path.join(output,'browser-directory.json'),JSON.stringify({generatedAt:new Date().toISOString(),browserVersion:browser.version(),base,html_sha256:sha(directory),cityCards:70,districts:16,cards:city,mobileViewport:[390,844],layout,chongmingSearch:visible,wingOnSearch:wing,errors},null,2)+'\n');
 console.log('PASS rendered 70 city links / 16 districts, 30 global + individual links, mobile and search');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
