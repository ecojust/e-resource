/* Capture the background actually used by the independent second keyboard run. */
const fs=require('node:fs'),{createHash}=require('node:crypto'),{chromium}=require('playwright');
(async()=>{const browser=await chromium.connectOverCDP('http://127.0.0.1:'+process.env.QA_CDP_PORT);
 const p=browser.contexts()[0].pages().find(q=>q.url().startsWith(process.env.MODEL_BASE_URL));
 const row=await p.evaluate(()=>{const app=window.__SHANGHAI_APP__,s=app.scene,t=s.getStreamingState(),asset=s.getLandmarkAssetState('jingan-bubbling-well-lane-gate');return {observed:new Date().toISOString(),route:location.href,mode:app.mode,position:app.controller.position,asset:{status:asset.status,visible:asset.visible,variant:asset.variant,sha256:asset.verifiedAsset.sha256,triangles:asset.triangles},background:{active:t.active.map(({id,sizeBytes,triangles})=>({id,sizeBytes,triangles})),detailParents:t.detail.parents,detailAvailable:t.detail.available,detailActive:t.detail.active.map(x=>x.id)}}});
 row.scriptSha256=createHash('sha256').update(fs.readFileSync(__filename)).digest('hex');
 fs.writeFileSync(process.argv[2],JSON.stringify(row,null,2)+'\n');console.log(row.background);
 await browser.close();
})().catch(e=>{console.error(e);process.exitCode=1;});
