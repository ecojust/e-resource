import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile, stat, mkdtemp, mkdir, writeFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
import {walkingPose} from '../src/precise-registration-ui.js';

const root=new URL('../',import.meta.url),metadataCache=new Map();
const metadataReads=[];
// Sparse checkouts may omit older viewer pages/manifests. Inspect only small
// text metadata from Git, without materializing or reading any GLB/Blender file.
async function metadata(path){
  assert(/\.(?:html|json|js|css|md)$/.test(path)&&!path.startsWith('/')&&!path.split('/').includes('..'),path);
  if(!metadataCache.has(path))metadataCache.set(path,(async()=>{
    try{const value=await readFile(new URL(path,root),'utf8');metadataReads.push({path,source:'worktree'});return value;}
    catch(error){
      if(error.code!=='ENOENT')throw error;
      const value=execFileSync('git',['show',`HEAD:projects/shanghai/${path}`],{
        cwd:root,encoding:'utf8',maxBuffer:5_000_000,env:{...process.env,GIT_NO_LAZY_FETCH:'1'}});
      metadataReads.push({path,source:'local Git HEAD metadata'});return value;
    }
  })());
  return metadataCache.get(path);
}
async function sourceDocumentExists(path){
  assert(/^source\/[^?#]+\/README\.md$/.test(path)&&!path.split('/').includes('..'),path);
  try{return (await stat(new URL(path,root))).isFile();}
  catch(error){
    if(error.code!=='ENOENT')throw error;
    // Link reachability needs the tracked path, not a download of old prose.
    const entry=execFileSync('git',['ls-tree','HEAD','--',`projects/shanghai/${path}`],{
      cwd:new URL('../../',root),encoding:'utf8',env:{...process.env,GIT_NO_LAZY_FETCH:'1'}});
    return /^100\d{3} blob [a-f0-9]+\t/.test(entry);
  }
}
const legacy=JSON.parse(await metadata('data/landmarks.json'));
const integration=JSON.parse(await metadata('data/candidate-city-integrations.json'));
const candidates=integration.models,records=[...legacy,...candidates],candidateIds=new Set(candidates.map(row=>row.id));
const directory=await metadata('landmarks.html');
const viewers=JSON.parse(await metadata('data/model-viewers.json'));
const decode=value=>value.replaceAll('&amp;','&').replaceAll('&lt;','<').replaceAll('&gt;','>').replaceAll('&#x27;',"'").replaceAll('&#39;',"'").replaceAll('&quot;','"');
const cardsIn=html=>[...html.matchAll(/<article\b[^>]*data-landmark="([^"]+)"[^>]*>([\s\S]*?)<\/article>/g)]
  .map(row=>({id:decode(row[1]),body:row[2],html:row[0]}));
const cards=cardsIn(directory),byId=new Map(cards.map(card=>[card.id,card]));

test('current model articles, district totals and primary routes match the complete shared catalogue',async()=>{
  assert.equal(legacy.length,integration.existing_city_count);
  assert.equal(candidates.length,integration.new_city_model_count);
  assert.equal(records.length,integration.resulting_city_count);
  assert.equal(cards.length,records.length);assert.equal(byId.size,records.length);
  assert.deepEqual([...byId.keys()].sort(),records.map(row=>row.id).sort());
  for(const record of records){
    const card=byId.get(record.id),heading=card.body.match(/<h3><a href="([^"]+)">([\s\S]*?)<\/a><\/h3>/);
    assert(heading,record.id);assert.equal(decode(heading[2]),record.name);
    const url=new URL(decode(heading[1]),'https://example.test/projects/shanghai/landmarks.html');
    assert.equal(url.pathname,'/projects/shanghai/index.html');
    const hash=new URLSearchParams(url.hash.slice(1));assert.equal(hash.get('landmark'),record.id);
    assert.equal(hash.get('mode'),candidateIds.has(record.id)?'overview':'walk');
    const foot=card.body.match(/<div class="card-foot">([\s\S]*?)<\/div>/)[1];
    assert(foot.includes(`href="${heading[1]}"`),`${record.id} title and action must share their global destination`);
    if(candidateIds.has(record.id)){
      assert.match(card.body,/近似定位/);
      if(!record.navigation?.listed){assert.equal(walkingPose(record),null);assert.doesNotMatch(foot,/mode=walk/);}
    }else{
      const pose=walkingPose(record);assert(pose&&Object.values(pose).every(Number.isFinite),record.id);
      assert(pose.lng>120&&pose.lng<123&&pose.lat>30&&pose.lat<33,record.id);
    }
  }
  const districts=JSON.parse(await metadata('data/districts.json')).districts;
  const groups=[...directory.matchAll(/<section class="landmark-group" id="district-(\d+)"[^>]*>([\s\S]*?)<\/section>/g)];
  const expectedGroups=districts.filter(district=>records.some(record=>String(record.districtId)===String(district.id)));
  assert.equal(groups.length,expectedGroups.length);assert.equal(new Set(groups.map(group=>group[1])).size,groups.length);
  let total=0;
  for(const [,id,body]of groups){
    const expected=records.filter(record=>String(record.districtId)===id).map(record=>record.id).sort();
    const ids=cardsIn(body).map(card=>card.id).sort();assert.deepEqual(ids,expected);
    const heading=body.match(/<h2\b[^>]*>([\s\S]*?)<\/h2>/)[1];
    assert.equal(Number(heading.match(/<span>(\d+)<\/span>/)[1]),expected.length);total+=ids.length;
  }
  assert.equal(total,records.length);assert(directory.includes(`${records.length} 处建筑与构件 · ${groups.length} 个行政区`));
});

test('the published directory is reproducible from the current base and candidate metadata',()=>{
  execFileSync('python',[new URL('tools/build_landmark_directory.py',root).pathname,'--check'],{cwd:root});
});

test('global model cards retain auxiliary previews, source documentation and asset download metadata',async t=>{
  const auxiliary=new Map(candidates.map(row=>[row.id,{id:row.id,page:row.individual_page,manifest:row.candidate_manifest}]));
  for(const viewer of viewers.filter(row=>row.kind==='candidate')){
    assert(byId.has(viewer.id),`${viewer.id} must remain a global model card`);
    auxiliary.set(viewer.id,{id:viewer.id,page:viewer.page,manifest:viewer.manifest});
  }
  for(const item of auxiliary.values()){
    assert.match(item.page,/^[^/]+\.html$/);assert(byId.get(item.id).body.includes(`href="${item.page}"`),item.id);
    const page=await metadata(item.page),manifest=JSON.parse(await metadata(item.manifest));
    assert.equal(manifest.id,item.id);assert.match(page,/id="downloads"/);
    const sources=[...page.matchAll(/href="(source\/[^"#]+\/README\.md)"/g)].map(row=>row[1]);
    assert(sources.length>0,`${item.id} source explanation is reachable`);
    for(const path of sources)assert(await sourceDocumentExists(path),path);
    const scripts=[...page.matchAll(/<script\b[^>]*src="(src\/[^"?]+\.js)"/g)].map(row=>row[1]);
    assert(scripts.length>0,item.id);
    const implementation=(await Promise.all(scripts.map(metadata))).join('\n');
    assert.match(implementation,/\.download\s*=/,`${item.id} keeps its download action`);
    for(const role of ['raw','native','full','lod']){
      const asset=manifest.assets[role];assert(asset&&typeof asset.file==='string',`${item.id}/${role}`);
      assert(!asset.file.startsWith('/')&&!asset.file.split('/').includes('..'));
      assert(Number.isSafeInteger(asset.bytes)&&asset.bytes>0);assert.match(asset.sha256,/^[a-f0-9]{64}$/);
    }
  }
  for(const viewer of viewers.filter(row=>row.kind==='surface')){
    assert(directory.includes(`data-viewer="${viewer.id}" href="${viewer.page}"`));
    assert((await metadata(viewer.page)).trim().length>0);assert(JSON.parse(await metadata(viewer.manifest)));
  }
  t.diagnostic(`${auxiliary.size} building previews retain source/download metadata; no GLB or Blender bytes were read`);
});

test('lightweight directory resources and loading-screen entry remain available without starting WebGL',async()=>{
  for(const path of ['src/landmark-directory.css','src/landmark-directory.js','src/landmark-entry.css'])assert((await metadata(path)).trim().length>0,path);
  const index=await metadata('index.html');
  assert.match(index,/class="landmark-directory-link" href="landmarks\.html"/);
  assert.match(index,/class="loading-directory-link" href="landmarks\.html"/);
  assert.match(index,/href="src\/landmark-entry\.css"/);
  assert.doesNotMatch(directory,/(?:three\.module|maplibre-gl|src\/app\.js)/);
});

test('a new delivered candidate appears as the latest overview destination from a complete metadata fixture',async()=>{
  const temporary=await mkdtemp(join(tmpdir(),'shanghai-directory-next-')),project=join(temporary,'projects/shanghai');
  try{
    await mkdir(join(project,'data/model-todo'),{recursive:true});
    const next={...candidates.at(-1),id:'huangpu-next-delivered-building',name:'下一栋已交付建筑',individual_page:'next-delivered-building.html',navigation:{listed:false}};
    const queue=JSON.parse(await metadata('data/model-todo/queue.json'));
    queue.production_queue.push({id:next.id,name:next.name,district:'黄浦区',order:Math.max(...queue.production_queue.map(row=>row.order))+1,
      status:'candidate_delivered',preview_source:next.individual_page});
    const fixtureViewers=[...viewers,{id:next.id,name:next.name,district:'黄浦区',kind:'candidate',page:next.individual_page,description:'增量目录测试'}];
    const fixtureCatalog={...integration,models:[...candidates,next],new_city_model_count:candidates.length+1,resulting_city_count:records.length+1};
    await Promise.all([
      writeFile(join(project,'data/landmarks.json'),JSON.stringify(legacy)),
      writeFile(join(project,'data/candidate-city-integrations.json'),JSON.stringify(fixtureCatalog)),
      writeFile(join(project,'data/districts.json'),await metadata('data/districts.json')),
      writeFile(join(project,'data/model-viewers.json'),JSON.stringify(fixtureViewers)),
      writeFile(join(project,'data/model-todo/queue.json'),JSON.stringify(queue)),
    ]);
    const rendered=execFileSync('python',['-c',`import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import build_landmark_directory as directory
import sync_readme_districts as metadata
metadata.ROOT = Path(sys.argv[2])
metadata.DATA = metadata.ROOT / 'projects/shanghai/data/model-todo'
metadata.INTEGRATIONS = metadata.ROOT / 'projects/shanghai/data/candidate-city-integrations.json'
print(directory.render(metadata.ROOT / 'projects/shanghai'))`,new URL('tools/',root).pathname,temporary],{encoding:'utf8'});
    assert(rendered.includes(`href="#building-${next.id}">最近接入：${next.name}`));
    const nextCard=cardsIn(rendered).find(card=>card.id===next.id);assert(nextCard);
    assert.match(nextCard.html,/class="landmark-card featured"/);assert.doesNotMatch(nextCard.body,/mode=walk/);
    assert(nextCard.body.includes(`index.html#landmark=${next.id}&amp;mode=overview`));
    assert.equal((rendered.match(/class="new-tag"/g)||[]).length,1);assert.equal(cardsIn(rendered).length,records.length+1);
  }finally{await rm(temporary,{recursive:true,force:true});}
});

test.after(()=>{assert(metadataReads.every(row=>/\.(?:html|json|js|css|md)$/.test(row.path)));});
