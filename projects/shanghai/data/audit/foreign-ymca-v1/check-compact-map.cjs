/* Verify the 102nd real map marker at narrow-phone size with an existing long building title. */
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {createHash}=require('node:crypto');
const {chromium}=require('playwright');
const {PNG}=require('pngjs');
const id='huangpu-foreign-ymca';
const project=process.env.SHANGHAI_PROJECT_ROOT||path.resolve(__dirname,'../../..');
const base=process.env.MODEL_BASE_URL||'http://127.0.0.1:8956/';
const out=process.env.QA_OUTPUT_DIR||__dirname;
const hash=b=>createHash('sha256').update(b).digest('hex');
const read=f=>fs.readFileSync(path.join(project,f));
const inputs=['index.html','src/app.js','src/building-beacons.js','src/map-scene.js','data/candidate-city-integrations.json'];
const report={id,base,started:new Date().toISOString(),completed:false,viewport:[320,568],script_sha256:hash(fs.readFileSync(__filename)),bindings:Object.fromEntries(inputs.map(f=>[f,hash(read(f))])),layouts:[],errors:[]};

async function run(){
  fs.mkdirSync(out,{recursive:true});
  const catalog=JSON.parse(read(inputs[4]));assert.equal(catalog.resulting_city_count,102);
  assert(read('src/map-scene.js').toString().includes('building-beacons.js?v=jardine-matheson-v1'));
  const model=catalog.models.find(x=>x.id===id);assert(model);
  const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:320,height:568},hasTouch:true,isMobile:true,ignoreHTTPSErrors:true});
  const rows=['jingan-country-hospital','huangpu-shanghai-concert-hall','qingpu-beidajie-222','huangpu-baxianqiao-ymca'];
  report.browser=browser.version();page.on('pageerror',e=>report.errors.push(e.message));page.setDefaultTimeout(150000);
  const save=()=>fs.writeFileSync(path.join(out,'compact-browser.json'),JSON.stringify(report,null,2)+'\n');
  try{
    await page.goto(new URL('index.html#landmark='+rows[0]+'&mode=overview',base).href,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState));
    for(const previous of rows){
      await page.evaluate(async previous=>{const app=window.__SHANGHAI_APP__,prior=app.landmarks.find(m=>m.id===previous);if(!prior)throw Error('Missing registered control '+previous);await app.selectPlace(prior,{mode:'overview'});},previous);
      await page.evaluate(()=>{const s=window.__SHANGHAI_APP__.scene,m=s.map;m.setMaxBounds(null);m.setCenterClampedToGround(true);m.jumpTo({center:[121.45,31.2],zoom:8,pitch:0,bearing:0,elevation:0,padding:{top:0,left:0,bottom:0,right:0}});s.refreshBuildingBeacons();});
      await page.waitForFunction(()=>{const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState();return !s.map.isMoving()&&b.viewportLabelCount===102&&b.overlapFallbackCount===0&&b.sourceIds.every(k=>s.map.isSourceLoaded(k));},{},{timeout:210200,polling:500});
      const layout=await page.evaluate(id=>{
        const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState(),p=b.labelPositions;
        const safeRect=query=>document.querySelector(query).getBoundingClientRect().toJSON();
        let overlappingPairs=0;
        for(let i=0;i<p.length;i++)for(let j=i+1;j<p.length;j++)if(Math.abs(p[i].x-p[j].x)<(p[i].width+p[j].width)/2-.01&&Math.abs(p[i].y-p[j].y)<(p[i].height+p[j].height)/2-.01)overlappingPairs++;
        return {selection:location.hash,cardTitle:document.getElementById('location-name').textContent,card:safeRect('#location-card'),legend:safeRect('#building-beacon-legend'),tools:safeRect('.map-tools'),count:b.count,laidOut:p.length,distinctCentres:new Set(p.map(x=>x.x+','+x.y)).size,hitTests:p.filter(x=>s.pickBuildingBeacon(x)===x.id).length,overlapFallbacks:b.overlapFallbackCount,overlappingPairs,cellSizes:[...new Set(p.map(x=>x.width+'×'+x.height))],positions:p,target:p.find(x=>x.id===id)};
      },id);
      assert.equal(layout.count,102);assert.equal(layout.laidOut,102);assert.equal(layout.distinctCentres,102);assert.equal(layout.hitTests,102);assert.equal(layout.overlappingPairs,0);assert.equal(layout.overlapFallbacks,0);assert.equal(layout.target?.number,102);
      report.layouts.push(layout);save();
      if(layout.target.height===15){
        assert.equal(layout.target.width,26);
        const numberLayer='shanghai-building-beacons-labels-numbers';
        await page.waitForFunction(layer=>{
          const m=window.__SHANGHAI_APP__.scene.map;
          return m.isStyleLoaded()&&m.queryRenderedFeatures({layers:[layer]}).length>=1;
        },numberLayer,{polling:650,timeout:200000});
        // MapLibre may paint leaders before its glyph atlas/symbol texture is ready.
        // Count the actual dark-teal sprite fill and warm outline in every hit cell.
        let image,painted=[];const deadline=Date.now()+150000;
        do{
          image=await page.screenshot({timeout:110200});const png=PNG.sync.read(image);
          const sx=png.width/320,sy=png.height/568;
          painted=layout.positions.filter(r=>{
            const x0=Math.round((r.x-r.width/2)*sx),x1=Math.round((r.x+r.width/2)*sx);
            const y0=Math.round((r.y-r.height/2)*sy),y1=Math.round((r.y+r.height/2)*sy);
            let interior=0,edge=0;
            for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){
              const i=(y*png.width+x)*4,R=png.data[i],G=png.data[i+1],B=png.data[i+2];
              if(R<80&&G-R>=18&&B-R>=16&&Math.abs(B-G)<16)interior++;
              if(R>=175&&R-G>=15&&G-B>=21)edge++;
            }
            return interior>=16*sx*sy&&edge>=7*sx*sy;
          }).map(r=>r.number);
          if(painted.length<layout.count)await page.waitForTimeout(900);
        }while(painted.length<layout.count&&Date.now()<deadline);
        report.paintedNumbers=painted;assert.equal(painted.length,layout.count,'every physical badge must appear in the actual PNG');
        fs.writeFileSync(path.join(out,'map-102-markers.png'),image);report.screenshot={file:'map-102-markers.png',bytes:image.length,sha256:hash(image)};
        const png=PNG.sync.read(image),sign=layout.target,sx=png.width/320,sy=png.height/568;
        const x0=Math.round((sign.x-sign.width/2)*sx),x1=Math.round((sign.x+sign.width/2)*sx);
        const y0=Math.round((sign.y-sign.height/2)*sy),y1=Math.round((sign.y+sign.height/2)*sy);
        // The pale number is less saturated than the yellow stroke around the card.
        // Exclude the outer two CSS pixels to measure the actual rendered digit ink.
        const hits=[];
        for(let y=y0+Math.ceil(2*sy);y<y1-Math.ceil(2*sy);y++)for(let x=x0+Math.ceil(2*sx);x<x1-Math.ceil(2*sx);x++){
          const i=(y*png.width+x)*4,[r,g,b]=png.data.subarray(i,i+3);
          if(r>182&&g>171&&b>134&&Math.abs(r-g)<24&&r-b<69)hits.push([x,y]);
        }
        assert.ok(hits.length>=18, 'Three-digit marker must contain rendered number ink');
        const xs=hits.map(p=>p[0]),ys=hits.map(p=>p[1]);
        const xMin=Math.min(...xs),xMax=Math.max(...xs),yMin=Math.min(...ys),yMax=Math.max(...ys);
        report.glyphPixels={count:hits.length,cssScale:[sx,sy],width:(xMax-xMin+1)/sx,height:(yMax-yMin+1)/sy,
          paddingPx:{left:(xMin-x0)/sx,right:(x1-xMax-1)/sx,top:(yMin-y0)/sy,bottom:(y1-yMax-1)/sy}};
        assert.ok(report.glyphPixels.width>=14&&report.glyphPixels.width<=22);
        const crop=new PNG({width:x1-x0,height:y1-y0});PNG.bitblt(png,crop,x0,y0,crop.width,crop.height,0,0);
        fs.writeFileSync(path.join(out,'marker-102.png'),PNG.sync.write(crop));
        await page.touchscreen.tap(layout.target.x,layout.target.y);
        await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,id);
        await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__.scene.getLandmarkAssetState(id);return s.status==='loaded'&&s.visible;},id);
        report.touch=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene.getLandmarkAssetState(id);return {route:location.hash,name:document.querySelector('#location-name').textContent,triangles:s.triangles,role:s.variant,sha256:s.verifiedAsset.sha256};},id);
        assert.equal(report.touch.name,model.name);assert.equal(report.touch.sha256,model.assets[report.touch.role==='full'?'web':'lod'].sha256);break;
      }
    }
    assert.ok(report.touch,'A real long title must exercise the three-digit compact fallback and select #102');
    assert.deepEqual(report.errors,[]);report.completed=true;
  }catch(error){report.failure=error.stack;throw error;}
  finally{report.finished=new Date().toISOString();save();await browser.close();}
}
run().catch(error=>{console.error(error);process.exitCode=1;});
