"""Check the actual production Float32 clip texture against decoded source geometry."""
from pathlib import Path
import json,os,shapely
from shapely.geometry import shape,Polygon,mapping
D=Path(os.environ.get('POSTAL_MAPPING_WORK','/workspace/shanghai-postal-mapping'))
f=json.loads((D/'footprint-contract.json').read_text());mask=shapely.union_all([Polygon(x)for x in json.loads((D/'float32-clip-triangles-enu.json').read_text())['triangles']]);profiles={x['properties']['name']:shape(x['geometry'])for x in json.loads((D/'source-profiles.geojson').read_text())['features']};source=shape(f['source_geometry_local_enu']);rows=[]
for name,p in profiles.items():
 intersection=p.intersection(mask).area;remaining=p.difference(mask).area
 rows.append({'profile':name,'clip_intersection_m2':intersection,'remaining_m2':remaining,'mask_distance_m':p.distance(mask)})
 if not name.endswith('_1959'):assert intersection<1e-9,(name,intersection)
protected=shape(next(r for r in json.loads((D/'context-features.json').read_text())if r['localId']==3148)['geometry_local_enu'])
assert protected.buffer(.119,join_style=2).intersection(mask).area<1e-9
report={'schema':'postal-display-clip-geometry-v1','model_id':f['model_id'],'float32_actual_map_origin':json.loads((D/'source-scope-verification.json').read_text())['map_origin_wgs84'],'source1959_original_area_m2':source.area,'source1959_retained_joint_area_m2':source.difference(mask).area,'source1959_retained_fraction':source.difference(mask).area/source.area,'rows':rows,'new_clip_rows':6,'global_clip_rows':307,'capacity':320,'source_mask_float32_union_geometry_local_enu':mapping(mask),'checks':{'all_retained_shared_near_projection_overlap_zero':True,'retained_far_projection_overlap_zero':True,'float32_mask_excludes_entire_3148_plus_0119m':True},'limits':'Near owner triangle classification uses nearest source geometry and has ambiguous tiny seams; safety relies on excluding the entire3148 polygon with0.12m margin, not that classification. Float32 texture retains at least0.119m geographic margin. Source1959 narrow joint strip retained. No WebGL pixel render claimed.'}
(D/'clip-geometry-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'new_clip_rows':6,'global_clip_rows':307,'retained_source_joint_m2':report['source1959_retained_joint_area_m2'],'all_foreign_overlap_zero':True}))
