/**
 * Replace only the modeled portions of two verified basemap road features.
 * The owner enables this solely while the local street GLB is visible in walk
 * mode at zoom >= 18. This module never changes road widths or model geometry.
 */
const SOURCE_ID='bund-road-remainders-v4';
const clone=value=>value===undefined ? undefined : structuredClone(value);

export async function createStreetBasemapReplacement(map) {
  const [metadataResponse,geometryResponse]=await Promise.all([
    fetch(new URL('../data/bund/basemap-road-remainders-v4.json',import.meta.url)),
    fetch(new URL('../data/bund/basemap-road-remainders-v4.geojson',import.meta.url)),
  ]);
  if (!metadataResponse.ok || !geometryResponse.ok) {
    throw new Error('Bund road replacement data is unavailable; original road layers retained.');
  }
  const [metadata,geometry]=await Promise.all([metadataResponse.json(),geometryResponse.json()]);
  const ids=metadata.suppressed_feature_ids;
  if (!metadata.coverage_validation?.passed || geometry.type!=='FeatureCollection'
    || !Array.isArray(ids) || ids.length!==2 || !ids.every(Number.isSafeInteger)
    || !Array.isArray(metadata.layer_ids) || metadata.layer_ids.length!==2
    || !geometry.features.every(feature=>ids.includes(feature.properties?.source_mvt_id))) {
    throw new Error('Invalid Bund road replacement data; original road layers retained.');
  }
  const styleLayers=map.getStyle().layers;
  const original=metadata.layer_ids.map(id=>{
    const layer=styleLayers.find(layer=>layer.id===id);
    if (!layer || layer.type!=='line' || layer['source-layer']!=='transportation') {
      throw new Error(`Bund road source layer is unavailable: ${id}`);
    }
    return {id,style:clone(layer),filter:clone(map.getFilter(id)),
      remainderId:`${id}-bund-outside-v4`,visibility:layer.layout?.visibility || 'visible'};
  });
  if (map.getSource(SOURCE_ID) || original.some(record=>map.getLayer(record.remainderId))) {
    throw new Error('Bund road replacement is already installed.');
  }
  let active=false,disposed=false,failed=false,error=null,filtersApplied=false,sourceAdded=false;
  const installedLayers=[];
  function safely(operation) {try {operation();} catch {} }
  function restoreOriginalFilters() {
    if (!filtersApplied) return;
    for (const record of original) safely(()=>{
      if (map.getLayer(record.id)) map.setFilter(record.id,clone(record.filter) ?? null);
    });
    filtersApplied=false;
  }
  function hideRemainders() {
    for (const record of original) safely(()=>{
      if (map.getLayer(record.remainderId)) map.setLayoutProperty(record.remainderId,'visibility','none');
    });
  }
  function removeOwnResources() {
    for (const id of [...installedLayers].reverse()) safely(()=>{
      if (map.getLayer(id)) map.removeLayer(id);
    });
    if (sourceAdded) safely(()=>{if (map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID);});
  }
  try {
    map.addSource(SOURCE_ID,{type:'geojson',data:geometry});sourceAdded=true;
    for (const record of original) {
      const layer=clone(record.style);
      layer.id=record.remainderId;layer.source=SOURCE_ID;delete layer['source-layer'];
      layer.layout={...layer.layout,visibility:'none'};
      // Same complete paint/filter/layout and same relative rendering order.
      map.addLayer(layer,record.id);installedLayers.push(layer.id);
    }
  } catch (failure) {
    removeOwnResources();
    throw new Error(`Bund road replacement was not installed; original layers retained: ${failure.message}`);
  }
  function setActive(value) {
    const requested=Boolean(value);
    if (disposed || failed || requested===active) return active;
    try {
      if (!map.getSource(SOURCE_ID) || original.some(record=>!map.getLayer(record.id) || !map.getLayer(record.remainderId))) {
        throw new Error('A road replacement layer or source was removed.');
      }
      if (requested) {
        const exclusion=['!', ['in',['id'],['literal',ids]]];
        // Mark before the first write so partial failure restores both layers.
        filtersApplied=true;
        for (const record of original) {
          const filter=record.filter ? ['all',clone(record.filter),clone(exclusion)] : clone(exclusion);
          map.setFilter(record.id,filter);
          map.setLayoutProperty(record.remainderId,'visibility',record.visibility);
        }
      } else {
        restoreOriginalFilters();hideRemainders();
      }
      active=requested;return active;
    } catch (failure) {
      restoreOriginalFilters();hideRemainders();active=false;failed=true;error=failure.message;
      return false;
    }
  }
  function getState() {
    return {ready:!disposed&&!failed,active,disposed,error,sourceId:SOURCE_ID,
      originalLayerIds:original.map(record=>record.id),remainderLayerIds:original.map(record=>record.remainderId),
      suppressedFeatureIds:[...ids],retainedFragments:geometry.features.length,
      retainedLengthMetres:metadata.totals.retained_outside_crop_length_m};
  }
  function dispose() {
    if (disposed) return;
    disposed=true;
    restoreOriginalFilters();active=false;removeOwnResources();
  }
  return {setActive,getState,dispose};
}
