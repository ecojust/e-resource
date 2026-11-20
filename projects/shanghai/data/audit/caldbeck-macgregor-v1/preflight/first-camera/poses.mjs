import fs from 'node:fs';
import {candidateOverviewCamera} from '/workspace/e-resource/projects/shanghai/src/candidate-overview-camera.js';
const row=JSON.parse(fs.readFileSync('/workspace/e-resource/projects/shanghai/data/audit/caldbeck-macgregor-v1/final-placement-contract.json'));row.city_integration=true;const set=[];
for (const [width,height,left] of [[870,660,312],[390,844,16]])for(const pitch of [53,49,45,41,37,33,32,31,30])for(const delta of [-15,0,15]){
 const camera=candidateOverviewCamera({...row,overviewPitch:pitch,overviewBearing:-13+delta},{width,height,insets:{left,right:64,top:width>400?154:182,bottom:width>400?152:174}});set.push({width,height,camera});
}fs.writeFileSync('/tmp/caldbeck91/camera/poses.json',JSON.stringify(set));
