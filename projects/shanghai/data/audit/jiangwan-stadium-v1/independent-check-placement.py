"""Review-only final placement and collision validation from independent GLB occupancy.
No mapper triangle payload or author build geometry is used. Only this candidate is checked.
"""
from pathlib import Path
import gzip,hashlib,json,math,sys
from shapely.geometry import shape,mapping,Polygon
from shapely.ops import transform,unary_union
R,M,C,O=map(Path,sys.argv[1:5])
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
contract=json.loads(C.read_text());report=json.loads((R/'independent-geometry-review.json').read_text());table=json.loads(gzip.decompress((M/'macro-feature-table.json.gz').read_bytes()));original=json.loads((R/'independent-original-city-projection.json').read_text())
assert contract['id']==report['modelId']=='yangpu-jiangwan-stadium'
assert contract['heading']==0 and contract['scale']==1 and contract['altitude']==0
assert [contract['lng'],contract['lat']]==[121.51109345895824,31.30841093103452]
assert contract['model_geometry_sha256']=={key:report['assets'][role]['sha256'] for key,role in [('raw','raw'),('web','full'),('lod','lod')]}
package=json.loads((R/'independent-packaging-binding.json').read_text());assert contract['model_manifest_sha256']==package['final_manifest']['sha256']
k=6371008.8*math.cos(math.radians(contract['lat']));psi=math.asinh(math.tan(math.radians(contract['lat'])))
def local(lng,lat,z=None):return k*math.radians(lng-contract['lng']),k*(math.asinh(math.tan(math.radians(lat)))-psi)
sources={row['localId']:transform(local,shape(row['geometry']))for row in table['features']}
assert len(sources)==2324
masks={1646:transform(local,shape(contract['replacement_geometry'])),1816:transform(local,shape(contract['site_replacement']['geometry']))}
clips=json.loads((M/'clip-preflight.json').read_text())
assert digest(M/'clip-preflight.json')==original['bindings']['clip_preflight_sha256']
for row in clips['rows']:assert masks[row['local_id']].symmetric_difference(shape(row['mask_geometry_local_enu'])).area<1e-5
collision_wgs=shape(contract['collision_geometry']);collision=transform(local,collision_wgs);assert collision_wgs.is_valid and collision.is_valid
parts=list(collision.geoms)if collision.geom_type=='MultiPolygon'else[collision]
counts=[[len(p.exterior.coords)]+[len(r.coords)for r in p.interiors]for p in parts]
assert len(parts)<=32 and max(map(len,counts))<=32 and max(n for r in counts for n in r)<=256 and sum(map(sum,counts))<=4096
main=unary_union([sources[1646],sources[1816]]);safe_field=main.convex_hull.difference(main).buffer(-12)
a=math.radians(26.56537);co,si=math.cos(a),math.sin(a)
def design(x,y):return(co*x-si*y,si*x+co*y)
corridors={name:Polygon([design(cx+dx,y)for dx,y in [(-2.3,y0),(2.3,y0),(2.3,y1),(-2.3,y1)]])for name,cx,y0,y1 in [('south',6.8,-180,-145),('north',1.45,154,183)]}
occupancies={};assetrows=[]
for role in ['raw','full','lod']:
 asset=report['assets'][role];p=R/'independent-occupancy'/(asset['sha256']+'.json');occ=json.loads(p.read_text());assert occ['asset_sha256']==asset['sha256'] and occ['triangle_payload_sha256']==asset['actualTrianglesENU']['sha256'];full=shape(occ['full_projection']['geometry_local_xy']);low=shape(occ['standing_slab']['geometry_local_xy']);assert full.is_valid and low.is_valid;occupancies[role]=(full,low)
 missed=low.difference(collision).area;field_full=full.intersection(safe_field).area;field_low=low.intersection(safe_field).area;assert missed<1e-5 and field_full<1e-5 and field_low<1e-5
 foreign=[{'source_local_id':i,'full_overlap_m2':full.intersection(s).area,'low_overlap_m2':low.intersection(s).area}for i,s in sources.items()if i not in (1646,1816)];bad=[r for r in foreign if r['full_overlap_m2']>1e-6 or r['low_overlap_m2']>1e-6];assert not bad,bad
 portals={n:low.intersection(p).area for n,p in corridors.items()};assert max(portals.values())<1e-6
 residuals={str(i):{'source_area_m2':sources[i].area,'source_not_covered_by_full_projection_m2':sources[i].difference(full).area,'full_projection_fraction_of_source':sources[i].intersection(full).area/sources[i].area}for i in (1646,1816)}
 assetrows.append({'role':role,'asset_sha256':asset['sha256'],'occupancy_sha256':digest(p),'full_projection_area_m2':full.area,'standing_slab_area_m2':low.area,'standing_slab_outside_collision_m2':missed,'field_full_overlap_m2':field_full,'field_low_overlap_m2':field_low,'short_end_corridor_low_overlaps_m2':portals,'other_original_sources_checked':len(foreign),'nonzero_foreign_overlap':bad,'source_projection_comparison':residuals})
lowunion=unary_union([r[1]for r in occupancies.values()]);extra=collision.difference(lowunion.buffer(.18,join_style=2)).area;assert extra<1e-5,extra
foreign_collision=[{'source_local_id':i,'overlap_m2':collision.intersection(s).area}for i,s in sources.items()if i not in (1646,1816)];bad=[r for r in foreign_collision if r['overlap_m2']>1e-6];assert not bad,bad
collision_corridors={n:collision.intersection(p).area for n,p in corridors.items()};assert max(collision_corridors.values())<1e-6;assert collision.intersection(safe_field).area<1e-6
near_neighbors=[]
for variant in original['actual_city_sources']:
 for comp in variant['components']:
  if comp['owner']in(1646,1816):continue
  g=shape(comp['geometry_local_xy']);row={'variant':variant['variant'],'source_local_id':comp['owner'],'collision_overlap_m2':g.intersection(collision).area,'full_model_overlap_m2':max(g.intersection(f).area for f,l in occupancies.values())};assert row['collision_overlap_m2']<1e-6 and row['full_model_overlap_m2']<1e-6;near_neighbors.append(row)
output={'schema':'jiangwan-stadium-independent-final-placement-v1','passed':True,'candidate_id':contract['id'],'scope':'Only this candidate, two original main stand sources, their exact near/far geometry and the other2322 original macro features; no historical asset matrix.','method':'Independent direct decoded indexed GLB triangles and independent z0..2 clipping/union; independent immutable feature-table projection. Display masks and low collision are separately validated.','bindings':{'contract_sha256':digest(C),'geometry_report_sha256':digest(R/'independent-geometry-review.json'),'packaging_binding_sha256':digest(R/'independent-packaging-binding.json'),'original_source_review_sha256':digest(R/'independent-original-city-projection.json'),'script_sha256':digest(Path(__file__))},'frame':{k:contract[k]for k in ['lng','lat','heading','scale','altitude']},'assets':assetrows,'collision':{'valid_wgs84_and_local':True,'polygons':len(parts),'ring_point_counts':counts,'total_ring_points':sum(map(sum,counts)),'area_m2':collision.area,'exact_all_role_low_union_area_m2':lowunion.area,'extra_area_beyond_union_buffer_018m':extra,'other_original_sources_checked':len(foreign_collision),'nonzero_foreign_overlap':bad,'safe_field_overlap_m2':collision.intersection(safe_field).area,'short_end_corridor_overlaps_m2':collision_corridors,'limits':{'max_polygons':32,'max_rings_per_polygon':32,'max_points_per_ring':256,'max_total_points':4096},'ground_does_not_fill_overhead_projection':True},'actual_foreign_native_projections':near_neighbors,'display_masks_unchanged_from_independently_reviewed_preflight':True,'display_mask_expected_triangles':45,'global_display_mask_capacity':192,'model_projection_differences_m2':{'raw_full':occupancies['raw'][0].symmetric_difference(occupancies['full'][0]).area,'raw_lod':occupancies['raw'][0].symmetric_difference(occupancies['lod'][0]).area},'limits':'Source coverage is explicitly reported, not assumed100%. Bounded unsurveyed footprint differences need source/visual review. No interior accessibility, public access or original1934state completeness is certified. Separate gym, pool and field sources are retained.'}
O.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({'passed':True,'assets':len(assetrows),'collision_polygons':len(parts),'collision_points':sum(map(sum,counts)),'source_projection_comparisons':[r['source_projection_comparison']for r in assetrows]}))
