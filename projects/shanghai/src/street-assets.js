import {createStreetGreenery} from './street-greenery.js';

const digest=async data=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',data))].map(v=>v.toString(16).padStart(2,'0')).join('');
async function bytes(url,timeout=35000) {
  const response=await fetch(url,{signal:AbortSignal.timeout(timeout)});
  if(!response.ok)throw new Error(`街景资源读取失败 (${response.status})`);
  return response.arrayBuffer();
}

/** One street owner: verified base GLB, matching interaction and local instances. */
export async function loadStreetAssets({THREE,loader,record,onWarning=()=>{}}) {
  const base=document.baseURI, modelURL=new URL(record.url,base).href;
  const [modelResult,interactionResult,greeneryResult]=await Promise.allSettled([
    bytes(modelURL),
    record.interaction_file?bytes(new URL(record.interaction_file,base)):Promise.resolve(null),
    bytes(new URL('../data/bund/greenery-v4.5.json',import.meta.url)),
  ]);
  if(modelResult.status!=='fulfilled')throw modelResult.reason;
  const modelSha256=await digest(modelResult.value);
  if(modelSha256!==record.web_sha256)throw new Error('街景模型校验值不符');
  const data=await loader.parseAsync(modelResult.value,new URL('.',modelURL).href);
  const assembly={modelSha256,interaction:null,greenery:null};
  if(interactionResult.status==='fulfilled'&&interactionResult.value) {
    try {
      if(await digest(interactionResult.value)!==record.interaction_sha256)throw new Error('街景地面数据校验值不符');
      const interaction=JSON.parse(new TextDecoder().decode(interactionResult.value));
      if(interaction.web_model_sha256!==modelSha256)throw new Error('街景地面与模型版本不一致');
      assembly.interaction=interaction;
    } catch(error){onWarning(error);}
  } else if(interactionResult.status==='rejected')onWarning(interactionResult.reason);
  if(greeneryResult.status==='fulfilled') {
    try {
      const source=JSON.parse(new TextDecoder().decode(greeneryResult.value));
      if(assembly.interaction?.greenery_data_sha256 && await digest(greeneryResult.value)!==assembly.interaction.greenery_data_sha256)throw new Error('绿化位置校验值不符');
      assembly.greenery=await createStreetGreenery({THREE,data:source,origin:[record.lng,record.lat]});
      assembly.greenery.locations=source.trees.map(tree=>({lng:tree.lng,lat:tree.lat}));
      data.scene.add(assembly.greenery.group);
    } catch(error){onWarning(error);}
  } else onWarning(greeneryResult.reason);
  if(!assembly.greenery && assembly.interaction) {
    assembly.interaction.local_obstacles=assembly.interaction.local_obstacles.filter(obstacle=>obstacle.kind!=='tree');
  }
  data.scene.userData.streetAssembly=assembly;
  return data;
}
