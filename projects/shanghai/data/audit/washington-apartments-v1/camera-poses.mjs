import fs from 'node:fs';
import {candidateOverviewCamera} from '../../../src/candidate-overview-camera.js';
const row=JSON.parse(fs.readFileSync(process.argv[3] || new URL('./final-placement-contract.json',import.meta.url)));
const cases=[];
for (const [width,height,left] of [[870,660,312],[390,844,16]]) {
  const insets={left,right:64,top:width>400?154:182,bottom:width>400?152:174};
  for (const bearing of [175,190,205,218,231,242,253,264,279,295]) for (const pitch of [38,48,55,61]) {
    const options={...row,city_integration:true,overviewBearing:bearing,overviewPitch:pitch};
    cases.push({width,height,camera:candidateOverviewCamera(options,{width,height,insets})});
  }
}
fs.writeFileSync(process.argv[2],JSON.stringify(cases));
