import fs from 'node:fs';
import {candidateOverviewCamera} from '../../../src/candidate-overview-camera.js';
const row=JSON.parse(fs.readFileSync(process.argv[3] || new URL('./final-placement-contract.json',import.meta.url)));
const cases=[];
for (const [width,height,left] of [[870,660,312],[390,844,16]]) {
  const insets={left,right:64,top:width>400?154:182,bottom:width>400?152:174};
  for (const bearing of [-4,2,8,12,16,21,26,36,40,46,56,64,72]) for (const pitch of [31,37,42,49,55]) {
    const options={...row,city_integration:true,overviewBearing:bearing,overviewPitch:pitch};
    cases.push({width,height,camera:candidateOverviewCamera(options,{width,height,insets})});
  }
}
fs.writeFileSync(process.argv[2],JSON.stringify(cases));
