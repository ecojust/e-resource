import fs from 'node:fs';
import {candidateOverviewCamera} from '../../../src/candidate-overview-camera.js';
const row=JSON.parse(fs.readFileSync(process.argv[3] || new URL('./final-placement-contract.json',import.meta.url)));
const cases=[];
for (const [width,height,left] of [[870,660,312],[390,844,16]]) {
  const insets={left,right:64,top:width>400?154:182,bottom:width>400?152:174};
  for (const bearing of [-24,-14,-5,2,13,22,32]) for (const pitch of [40,52,58,64,67,70]) {
    const options={...row,city_integration:true,overviewBearing:bearing,overviewPitch:pitch};
    cases.push({width,height,camera:candidateOverviewCamera(options,{width,height,insets})});
  }
}
fs.writeFileSync(process.argv[2],JSON.stringify(cases));
