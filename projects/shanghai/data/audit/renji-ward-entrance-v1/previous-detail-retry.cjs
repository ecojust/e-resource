/* Recover the actual city detail index when its first detailed parents yield no near records. */
const fs=require('node:fs');
const {chromium}=require('playwright');
(async()=>{
 const [port,cameraFile,report]=process.argv.slice(2);
 const b=await chromium.connectOverCDP('http://127.0.0.1:'+port);
 const p=b.contexts()[0].pages().find(p=>p.url().includes('15079'));const camera=JSON.parse(fs.readFileSync(cameraFile));
 const result=await p.evaluate(async c=>{const a=window.__SHANGHAI_APP__,s=a.scene,m=s.map;const old=s.getStreamingState(),before=old.detail;
   const result={before:{parents:before.parents,available:before.available,requests:before.requests,active:before.active},mode:a.mode};
   a.controller.teleport({lng:c.center[0],lat:c.center[1],bearing:c.bearing});
   if(!before.available){const x=await s.setCityManifest('assets/city-detail/manifest.json');result.recovery={fallback:Boolean(x.fallback),error:x.error||null};}
   m.stop();m.setCenterClampedToGround(false);m.jumpTo({center:c.center,padding:c.padding,elevation:c.elevation,zoom:c.zoom,bearing:c.bearing,pitch:c.pitch});m.fire('moveend');
   return {...result,center:m.getCenter().toArray(),end:new Date().toISOString()};
 },camera);
 fs.writeFileSync(report,JSON.stringify(result,null,2)+'\n');process.exit(0);
})().catch(e=>{console.error(e);process.exit(1)});
