import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
const sets=[];
for(const root of ['/tmp/shanghai-view-updates/gate300/stage64/projects/shanghai']){
 const {candidateOverviewCamera}=await import(pathToFileURL(root+'/src/candidate-overview-camera.js'));
 const row=JSON.parse(fs.readFileSync(root+'/data/candidate-city-integrations.json')).models.at(-1);row.city_integration=true;
 for(const [w,h,left] of [[870,660,312],[390,844,16]]){
  for(const bearingDelta of [0,-10,10,-20,20,-30,30,-40,40,-50,50,-60,60,-65,65,-70,70])for(const newPitch of [70,67,64,60,56,52,48,44,40]){const camera=candidateOverviewCamera({...row,overviewBearing:row.overviewBearing+bearingDelta,overviewPitch:newPitch},{width:w,height:h,insets:{left,right:64,top:w>400?154:182,bottom:w>400?152:174}});
  sets.push({w,h,id:row.id,root,bearingDelta,newPitch,cam:camera});}
 }
}
fs.writeFileSync('/tmp/dong64/camera/options.json',JSON.stringify(sets,null,2));
