import fs from 'node:fs';
import {candidateOverviewCamera} from '../../../src/candidate-overview-camera.js';
const contract = new URL('./final-placement-contract.json', import.meta.url);
const row=JSON.parse(fs.readFileSync(contract));
const cases=[];
for(const [width,height,left] of [[870,660,312],[390,844,16]])for(const pitch of [37,43,50,55]){
 const cam=candidateOverviewCamera({...row,city_integration:true,overviewPitch:pitch},{width,height,insets:{left,right:64,top:width>400?154:182,bottom:width>400?152:174}});
 cases.push({width,height,camera:cam});
}
fs.writeFileSync(process.argv[2],JSON.stringify(cases));
