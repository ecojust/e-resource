/** Historic site markers have a verified viewer and no present-day scene geometry. */
const fields = ['id','name','kind','districtId','district_name','lng','lat','individual_page','candidate_manifest',
  'historical_view','assets','navigation','collision_geometry','replacement_geometry','source_feature_ids'];
export function validHistoricalSite(row) {
  const view=row.historical_view, years=view?.evidence_years, sourceIds=row.source_feature_ids;
  const exact=(object,keys)=>object && Object.keys(object).length===keys.length && keys.every(key=>Object.hasOwn(object,key));
  return typeof row.id==='string' && row.candidate_manifest===`assets/models/candidates/${row.id}/manifest.json`
    && row.kind==='historical-site' && exact(row,fields) && typeof row.name==='string' && row.name.length>0
    && /^[a-z0-9]+(?:-[a-z0-9]+)*-history\.html$/.test(row.individual_page)
    && exact(view,['kind','building_year','evidence_years']) && view.kind==='archival-facade'
    && Number.isInteger(view.building_year) && view.building_year>=1500
    && Array.isArray(years) && years.length===2 && years.every(Number.isInteger)
    && view.building_year<=years[0] && years[0]<=years[1] && years[1]<=new Date().getUTCFullYear()
    && exact(row.navigation,['listed']) && row.navigation.listed===false
    && row.collision_geometry===null && row.replacement_geometry===null
    && exact(sourceIds,['building','building_part']) && Object.values(sourceIds).every(v=>Array.isArray(v)&&v.length===0)
    && exact(row.assets,['web','lod']) && ['web','lod'].every(variant=>{
      const asset=row.assets[variant];
      return asset?.file===`assets/models/candidates/${row.id}/${row.id}-${variant}.glb`
        && Number.isInteger(asset.bytes) && asset.bytes>0 && asset.bytes<100_000_000
        && /^[a-f0-9]{64}$/.test(asset.sha256);
    });
}

export function setupHistoricalView({dialog,button,frame,title,closeButton,onModalChange}) {
  let active=null;
  function close() { if(dialog.open) dialog.close(); }
  function reset() {
    // A new site cannot inherit a still-loading frame from a closed dialog.
    if(dialog.open) return;
    frame.removeAttribute('src');
    onModalChange(false);
    if(active && button.isConnected) button.focus({preventScroll:true});
  }
  function select(place) {
    if(active?.id!==place.id) close();
    active=place.kind==='historical-site'?place:null;
    button.hidden=!active;
  }
  function open() {
    if(!active || dialog.open) return;
    const [first,last]=active.historical_view.evidence_years;
    // These two dates identify publication and archival accessions. The photographs are undated.
    const period=first===last ? String(first) : `${first}—${last}`;
    const dates=active.id==='xuhui-huaihai-1469-garden-front'
      ? `影像资料年份 ${first}—${last}`
      : `${period}年照片`;
    title.textContent=`${active.name} · ${dates}`;
    frame.title=active.name;
    frame.src=active.individual_page+'?embed=history';
    dialog.showModal();
    onModalChange(true);
    closeButton.focus();
  }
  button.addEventListener('click',open);
  closeButton.addEventListener('click',close);
  dialog.addEventListener('close',reset);
  dialog.addEventListener('click',event=>{if(event.target===dialog) close();});
  window.addEventListener('message',event=>{
    if(dialog.open && event.origin===location.origin && event.source===frame.contentWindow
       && event.data==='close-historical-view') close();
  });
  return {select};
}
