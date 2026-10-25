/** Minimal side-effect contract test; no browser or WebGL required. */
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const PROJECT=process.argv[2]?pathToFileURL(path.resolve(process.argv[2])+path.sep):new URL('../../../',import.meta.url);
const {createStreetBasemapReplacement}=await import(new URL('src/street-basemap.js',PROJECT));
const metadata=JSON.parse(fs.readFileSync(new URL('data/bund/basemap-road-remainders-v4.json',PROJECT),'utf8'));
const geometry=JSON.parse(fs.readFileSync(new URL('data/bund/basemap-road-remainders-v4.geojson',PROJECT),'utf8'));
const copy=value=>structuredClone(value);
const originals=metadata.layer_ids.map((id,index)=>({id,type:'line',source:'openfreemap','source-layer':'transportation',
 filter:['all',['==',['get','class'],'secondary'],['!=',['get','brunnel'],'tunnel']],
 paint:{'line-width':['interpolate',['linear'],['zoom'],16,8,22,300],'line-color':index?'#7b8788':'#c5cbc8','line-opacity':.95},
 layout:{'line-cap':'butt','line-join':'round'},minzoom:6,maxzoom:24}));
function mock(options={}) {
 const layers=[{id:'unrelated-background',type:'background'},...copy(originals)],sources=new Map(),calls=[];
 let layerAdds=0,filterWrites=0,failedOnce=false;
 const map={calls,getStyle:()=>({layers:copy(layers)}),getLayer:id=>layers.find(layer=>layer.id===id),getSource:id=>sources.get(id),
  getFilter:id=>copy(map.getLayer(id)?.filter),
  addSource(id,value){calls.push(['addSource',id]);sources.set(id,value);},
  removeSource(id){calls.push(['removeSource',id]);sources.delete(id);},
  addLayer(value,before){layerAdds++;if(options.failSecondLayer&&layerAdds===2)throw Error('mock addLayer failure');calls.push(['addLayer',value.id]);layers.splice(layers.findIndex(layer=>layer.id===before),0,copy(value));},
  removeLayer(id){calls.push(['removeLayer',id]);layers.splice(layers.findIndex(layer=>layer.id===id),1);},
  setFilter(id,value){filterWrites++;if(options.failSecondFilter&&filterWrites===2&&!failedOnce){failedOnce=true;throw Error('mock setFilter failure');}calls.push(['setFilter',id]);map.getLayer(id).filter=copy(value);},
  setLayoutProperty(id,key,value){calls.push(['setLayoutProperty',id,key,value]);const layer=map.getLayer(id);layer.layout={...layer.layout,[key]:value};},
 };
 return map;
}
const previousFetch=globalThis.fetch;
globalThis.fetch=async url=>({ok:true,json:async()=>copy(String(url).endsWith('.geojson')?geometry:metadata)});
let checks;
try {
 const map=mock(),handle=await createStreetBasemapReplacement(map);
 assert.equal(handle.getState().active,false);assert.equal(map.calls.filter(v=>v[0]==='setFilter').length,0);
 for(const original of originals){const layer=map.getLayer(`${original.id}-bund-outside-v4`);assert.deepEqual(layer.paint,original.paint);assert.equal(layer['source-layer'],undefined);assert.equal(layer.layout.visibility,'none');assert.deepEqual(layer.filter,original.filter);}
 handle.setActive(true);assert.equal(handle.getState().active,true);
 for(const original of originals){const filter=map.getFilter(original.id);assert.deepEqual(filter[1],original.filter);assert.deepEqual(filter[2],['!',['in',['id'],['literal',metadata.suppressed_feature_ids]]]);}
 const enabledWrites=map.calls.length;handle.setActive(true);handle.setActive(1);assert.equal(map.calls.length,enabledWrites);
 handle.setActive(false);for(const original of originals)assert.deepEqual(map.getFilter(original.id),original.filter);
 const disabledWrites=map.calls.length;handle.setActive(false);assert.equal(map.calls.length,disabledWrites);
 handle.setActive(true);handle.dispose();for(const original of originals){assert.deepEqual(map.getFilter(original.id),original.filter);assert.equal(map.getLayer(`${original.id}-bund-outside-v4`),undefined);}
 assert(map.getLayer('unrelated-background'));assert.equal(map.getSource('bund-road-remainders-v4'),undefined);
 const disposedWrites=map.calls.length;handle.dispose();handle.setActive(true);assert.equal(map.calls.length,disposedWrites);
 const addFailure=mock({failSecondLayer:true});await assert.rejects(createStreetBasemapReplacement(addFailure));
 assert.equal(addFailure.getSource('bund-road-remainders-v4'),undefined);assert.deepEqual(addFailure.getStyle().layers,[{id:'unrelated-background',type:'background'},...originals]);
 const filterFailure=mock({failSecondFilter:true}),failedHandle=await createStreetBasemapReplacement(filterFailure);assert.equal(failedHandle.setActive(true),false);assert.equal(failedHandle.getState().active,false);assert(failedHandle.getState().error);
 for(const original of originals){assert.deepEqual(filterFailure.getFilter(original.id),original.filter);assert.equal(filterFailure.getLayer(`${original.id}-bund-outside-v4`).layout.visibility,'none');}
 const failedWrites=filterFailure.calls.length;failedHandle.setActive(true);assert.equal(filterFailure.calls.length,failedWrites);failedHandle.dispose();
 globalThis.fetch=async()=>({ok:false});const missing=mock();await assert.rejects(createStreetBasemapReplacement(missing));assert.equal(missing.calls.length,0);
 checks={passed:true,complete_style_cloned:true,default_inactive_no_filter_mutation:true,enable_excludes_only_two_ids:true,disable_restores_exact_filters:true,repeated_active_calls_do_not_rewrite:true,dispose_restores_and_removes_only_owned_resources:true,dispose_idempotent:true,partial_install_failure_leaves_originals:true,partial_enable_failure_restores_originals:true,load_failure_keeps_original_layers:true,failed_enable_does_not_loop_style_writes:true};
} finally {globalThis.fetch=previousFetch;}
fs.writeFileSync(new URL('data/bund/validation/street-basemap-v4.json',PROJECT),JSON.stringify(checks,null,2)+'\n');console.log(JSON.stringify(checks));
