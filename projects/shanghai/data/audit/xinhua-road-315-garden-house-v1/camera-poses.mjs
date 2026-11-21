import fs from 'node:fs';
import {candidateOverviewCamera} from '../../../src/candidate-overview-camera.js';
const row=JSON.parse(fs.readFileSync(new URL('./final-placement-contract.json',import.meta.url)));
const cases=[];
for (const [width,height,left] of [[870,660,312],[390,844,16]]) {
  const insets={left,right:64,top:width>400?154:182,bottom:width>400?152:174};
  for (const bearing of [2,13,23,33,43,54]) for (const pitch of [35,42,47,51,55]) {
    const options={...row,city_integration:true,overviewBearing:bearing,overviewPitch:pitch};
    cases.push({width,height,camera:candidateOverviewCamera(options,{width,height,insets})});
  }
}
fs.writeFileSync(process.argv[2],JSON.stringify(cases));
