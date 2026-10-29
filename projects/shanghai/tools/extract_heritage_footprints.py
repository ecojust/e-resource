"""Review locally frozen Broadway/Russian footprints without network access.
Requires Python3, shapely and matplotlib. Outputs research JSON/GeoJSON and a
local context plot; individual neighboring sources retain their own licenses.
The four target geometries identify OSM and retain ODbL-1.0 attribution.
Example from repository root:
  python extract_heritage_footprints.py --repo . --out-dir /tmp/heritage-review
"""
from pathlib import Path
import argparse,subprocess,os,json,math,hashlib,sys
from shapely.geometry import shape, mapping, Point
from shapely.ops import transform
import shapely
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo',type=Path,default=Path('.'));parser.add_argument('--out-dir',type=Path,required=True);parser.add_argument('--commit',default='610d3065f6e833fac5553a900033b9b951ea7a48');args=parser.parse_args();repo=args.repo.resolve();out_dir=args.out_dir;out_dir.mkdir(parents=True,exist_ok=True);source='projects/shanghai/data/audit/landmark-candidate-features.geojson';env=dict(os.environ,GIT_NO_LAZY_FETCH='1');commit=subprocess.check_output(['git','rev-parse',args.commit],cwd=repo,text=True).strip();raw=subprocess.check_output(['git','show',commit+':'+source],cwd=repo,env=env);features=json.loads(raw)['features'];by_id={f['id']:f for f in features}
ids=['8dff7d94-53d9-406e-b208-dd8562bbdafe','59962d89-0a7a-3c8b-823f-8f12a3d2c3fa','49f3a80d-d5c3-421a-904a-e17974063f73','582fd5f8-2a90-3eba-9fce-81b358492d0b']
a=6378137.0;f=1/298.257223563;e2=f*(2-f)
def ecef(lon,lat):
 lo=math.radians(lon);la=math.radians(lat);n=a/math.sqrt(1-e2*math.sin(la)**2)
 return ((n)*math.cos(la)*math.cos(lo),n*math.cos(la)*math.sin(lo),n*(1-e2)*math.sin(la))
def projector(lon0,lat0):
 x0,y0,z0=ecef(lon0,lat0);lo=math.radians(lon0);la=math.radians(lat0)
 def en(lon,lat,z=None):
  x,y,z=ecef(lon,lat);dx,dy,dz=x-x0,y-y0,z-z0
  return -math.sin(lo)*dx+math.cos(lo)*dy,-math.sin(la)*math.cos(lo)*dx-math.sin(la)*math.sin(lo)*dy+math.cos(la)*dz
 return en
records=[];neighbors_out=[];targets_out=[]
fig,axs=plt.subplots(1,2,figsize=(13,7))
for idx,target_id in enumerate(ids):
 feat=by_id[target_id];g=shape(feat['geometry']);lon0,lat0=g.centroid.x,g.centroid.y;project=projector(lon0,lat0);metric=transform(project,g);rect=metric.minimum_rotated_rectangle;corners=list(rect.exterior.coords)[:-1];edges=[]
 for j in range(4):
  x0,y0=corners[j];x1,y1=corners[(j+1)%4];dx,dy=x1-x0,y1-y0;edges.append({'length_m':math.hypot(dx,dy),'axis_bearing_clockwise_from_north_deg_mod180':math.degrees(math.atan2(dx,dy))%180})
 longest=max(edges,key=lambda e:e['length_m']);shortest=min(edges,key=lambda e:e['length_m']);minx,miny,maxx,maxy=metric.bounds
 neighbors=[]
 for other in features:
  if other['id'] in ids:continue
  og=shape(other['geometry'])
  if abs(og.centroid.x-lon0)>.002 or abs(og.centroid.y-lat0)>.002:continue
  om=transform(project,og);distance=metric.distance(om)
  if distance<65:
   props=other['properties'];inter=metric.intersection(om).area
   neighbors.append({'id':other['id'],'name':props.get('@name'),'source_layer':props.get('source_layer'),'building_id':props.get('building_id'),'sources':props.get('sources',[]),'renderable':props.get('renderable'),'distance_m':distance,'intersection_area_m2':inter,'area_m2':om.area,'note':'Candidate audit index only; neither nearby inventory completeness nor architectural identity verified'})
   if idx not in (1,3):
    neighbors_out.append(other)
    ax=axs[0 if idx==0 else 1]
    geoms=list(om.geoms) if hasattr(om,'geoms') else [om]
    for poly in geoms:
     if hasattr(poly,'exterior'):
      xx,yy=poly.exterior.xy;ax.plot(xx,yy,color='#aaa',linewidth=.8)
    if distance<20:ax.text(om.centroid.x,om.centroid.y,other['id'][:8],fontsize=7,color='#777')
 neighbors.sort(key=lambda z:(z['distance_m'],z['id']))
 coords=list(metric.exterior.coords)
 cross=[]
 for j in range(len(coords)-1):
  p=coords[j-1 if j>0 else len(coords)-2];q=coords[j];r=coords[(j+1)%(len(coords)-1)];cross.append((q[0]-p[0])*(r[1]-q[1])-(q[1]-p[1])*(r[0]-q[0]))
 num_positive=sum(c>1e-6 for c in cross);num_negative=sum(c< -1e-6 for c in cross)
 result={'id':target_id,'name':feat['properties'].get('@name'),'original_properties':feat['properties'],'original_geometry_path':'heritage-next-source-features.geojson','coordinate_status':'Coordinates exactly as frozen derived audit GeoJSON; original OSM geometry and preprocessing/fragment merge were not independently recovered or validated','geometry_type':g.geom_type,'polygon_valid':g.is_valid,'polygon_simple':g.is_simple,'interior_ring_count':len(g.interiors),'unique_exterior_vertices':len(g.exterior.coords)-1,'bbox_wgs84':list(g.bounds),'local_origin_wgs84':[lon0,lat0],'local_exterior_enu_m':[list(p) for p in coords],'local_aabb_east_north_m':[maxx-minx,maxy-miny],'local_area_m2':metric.area,'local_perimeter_m':metric.length,'minimum_rotated_rectangle':{'corners_enu_m':[list(p) for p in corners],'long_axis_m':longest['length_m'],'short_axis_m':shortest['length_m'],'long_axis_bearing_clockwise_from_north_deg_mod180':longest['axis_bearing_clockwise_from_north_deg_mod180'],'axis_is_not_verified_front_direction':True},'convex_hull_area_m2':metric.convex_hull.area,'convex_hull_area_difference_m2':metric.convex_hull.area-metric.area,'mixed_turn_signs':num_positive>0 and num_negative>0,'nearby_index_records_within_65m':neighbors}
 records.append(result);targets_out.append(feat)
 if idx not in (1,3):
  ax=axs[0 if idx==0 else 1];xx,yy=metric.exterior.xy;ax.fill(xx,yy,color='#b95528',alpha=.55);ax.plot(xx,yy,color='#8b2516',linewidth=2);xx,yy=rect.exterior.xy;ax.plot(xx,yy,color='#276894',linestyle='--',linewidth=1);ax.set_title(('Broadway Mansions' if idx==0 else 'Russian Consulate')+' candidate audit footprint');ax.set_aspect('equal');ax.set_xlim(-95,95);ax.set_ylim(-85,85);ax.grid(alpha=.2);ax.set_xlabel('East from target centroid (m)');ax.set_ylabel('North from target centroid (m)')
parent_geo=shape(by_id[ids[0]]['geometry']);parent_project=projector(parent_geo.centroid.x,parent_geo.centroid.y);linked_geo=transform(parent_project,shape(by_id[ids[3]]['geometry']));xx,yy=linked_geo.exterior.xy;axs[0].fill(xx,yy,facecolor='#4b8d65',edgecolor='#124c2a',alpha=.6,linewidth=2);axs[0].text(0,0,'Linked unnamed part\nw744512992@2',ha='center',va='center',fontsize=9);fig.suptitle('Frozen audit footprints only; not a survey or verified historical building outline',fontsize=12);fig.tight_layout();fig.savefig(out_dir/'heritage-next-footprint-context.png',dpi=150)
broad_equal=shape(by_id[ids[0]]['geometry']).equals(shape(by_id[ids[1]]['geometry']))
base_refs=[]
for name in ['heritage-next-building-references.json','heritage-first20-model-reconciliation.json']:
 p=repo/'projects/shanghai/data/model-todo'/name;b=subprocess.check_output(['git','show',commit+':'+str(p.relative_to(repo))],cwd=repo,env=env);base_refs.append({'path':str(p.relative_to(repo)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
out={'schema':'heritage-next-footprint-review-v1','reviewed_utc':'2026-10-29','repository_commit':commit,'scope':'Read-only local frozen map footprint evidence:4 source features for2 study subjects (production queue17 and18); no accepted registration, model replacement or historical footprint verification','source':{'path':source,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'git_commit':commit,'read_method':'git show from already-present object, GIT_NO_LAZY_FETCH=1; no network','feature_count':len(features),'status':'Derived candidate audit geometry, not direct original OSM response'},'reference_inputs':base_refs,'method':{'python':sys.version.split()[0],'shapely':shapely.__version__,'coordinate_transform':'WGS84 geodetic longitude/latitude at ellipsoid height0 to ECEF, then local east/north tangent plane at each polygon centroid; no pyproj or network','wgs84_a_m':a,'wgs84_inverse_flattening':298.257223563,'axes':'x east, y north, metres; origin stored per record. Small-footprint tangent-plane measures only, not survey precision','dimensions':'Axis-aligned east/north bounds plus GEOS minimum rotated rectangle long/short sides; long-axis bearing clockwise from north modulo180. No axis identified as building front.','neighbors':'Only features already in the limited candidate audit index whose polygon distance is under65m; not a comprehensive nearby-building inventory. Repeated parent/part neighbors not deduplicated.'},'records':records,'broadway_parent_part_check':{'parent_id':ids[0],'part_id':ids[1],'part_building_id_matches_parent':by_id[ids[1]]['properties']['building_id']==ids[0],'same_osm_record':'w488961017@7','topologically_equal_polygons':broad_equal,'coordinate_order_difference':'Same8 exterior vertices with rotated ring start order','conclusion':'One source footprint represented as a non-renderable parent and a renderable part; never two independent buildings or two different plan tiers'},'interpretation':{'broadway':{'status':'Coarse named outer envelope plus an additional linked concave unnamed part; historical plan and floor-level assignment remain provisional','reasons':['The two named features share a convex8-corner polygon with no inward recesses. A third unnamed building_part explicitly links to that parent and supplies a14-corner concave outline with wing-end/recess geometry; neither source defines which floor level the outline belongs to or which edges are historical external walls.','num_floors19 in both map features conflicts with22 floors in the gazetteer and21 in Wikipedia. Do not silently choose or average; floor-count conventions and scope unverified.','Documentary site area6600m2 is a site quantity, not the map polygon area or main-building footprint.','No adjacent geometry was unioned into the target, but no aerial/registration source binds every polygon boundary to the main historical building. Cannot certify exclusion of podium/site coverage merely from the map name.','Photo-reviewed separate pale Jahwa tower must remain outside the historical model; this small convex polygon has no independently validated mass assignment.']},'russian':{'status':'Irregular elongated map polygon may guide provisional extents only; historical main-building boundary not independently established','reasons':['The audit polygon has no holes and10 unique exterior vertices; the source index records fragment_count2, with a short stepped segment on the south edge. This is not evidence of two physical buildings.','Map num_floors5 conflicts with documentary4 floors. No height field establishes roof or tower height.','Documentary site1700/1700-plus m2 and gross floor area3264m2 cannot be used to derive or validate this polygon by division.','A separate low green garden pavilion, high roof tower and modern rear/curved neighbor appear in the reference photo; this map polygon alone does not locate their individual bases or establish inclusion/exclusion.','No complete historical site boundary, back wall or outbuilding registry is available in this extraction of4 source features for2 study subjects.'] }},'rights':{'target_geometry_license':'ODbL-1.0','attribution':'© OpenStreetMap contributors; all4 target features identify OpenStreetMap via Overture-style building/building_part records','neighbor_context_license_note':'Nearby record references retain their own per-record source; some identify Zenodo doi:10.5281/zenodo.8174931 without a license field. Neighbor plot/geometry is a local research aid only; do not redistribute without separately verifying applicable source license.','coordinate_data_derived':True,'photo_pixels_redistributed':False},'next_action':'Keep map and documentary dimensions separately labeled. Review aerial or source geometry against documented main-building boundaries before using the outlines to cut/reposition or accept a model. No new model or queue state changed.'}
out['broadway_additional_linked_part']={'id':ids[3],'source_record':'w744512992@2','building_id':ids[0],'all_linked_part_ids_found_in_audit':[x['id'] for x in features if x['properties'].get('building_id')==ids[0]],'topologically_covered_by_named_parent':shape(by_id[ids[0]]['geometry']).covers(shape(by_id[ids[3]]['geometry'])),'part_to_parent_area_ratio':records[3]['local_area_m2']/records[0]['local_area_m2'],'height_or_floors_in_part_record':False,'interpretation':'Explicit source parent/part relation is stronger than a name-only association. Concave plan is usable as a separately labeled map-based shape lead, not as a verified historical main-wall line or a specific setback floor.'};out['photo_scope_crosscheck']={'reviewed_by':'independent child photo_scope','broadway':'Photo shows brown stepped body and wing-end forms but not complete four-wing plan; pale Jahwa neighbor separate','russian':'Photo shows historical pale body/red roof/high green tower and separate low green pavilion; modern rear/curved neighbor excluded pending identity','limit':'Uncalibrated oblique photographs do not accept map boundaries'};(out_dir/'heritage-next-footprint-review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
(out_dir/'heritage-next-source-features.geojson').write_text(json.dumps({'type':'FeatureCollection','features':targets_out},ensure_ascii=False,indent=2)+'\n')
seen=set();neighbors_clean=[]
for feat in neighbors_out:
 if feat['id'] not in seen:seen.add(feat['id']);neighbors_clean.append(feat)
(out_dir/'heritage-next-neighbor-features.geojson').write_text(json.dumps({'type':'FeatureCollection','features':neighbors_clean},ensure_ascii=False,indent=2)+'\n')
for r in records:print(r['name'],r['id'],r['local_area_m2'],r['local_aabb_east_north_m'],r['minimum_rotated_rectangle'],len(r['nearby_index_records_within_65m']))
print('parent_part_equal',broad_equal,'files complete')

# Independent arithmetic and structural checks keep dimensions tied to source coordinates.
for row in records:
    coords=row['local_exterior_enu_m'];area=abs(sum(coords[i][0]*coords[i+1][1]-coords[i+1][0]*coords[i][1] for i in range(len(coords)-1)))/2
    assert abs(area-row['local_area_m2'])<1e-7
    assert row['polygon_valid'] and row['interior_ring_count']==0
assert broad_equal and out['broadway_additional_linked_part']['topologically_covered_by_named_parent']
assert set(out['broadway_additional_linked_part']['all_linked_part_ids_found_in_audit'])=={ids[1],ids[3]}
out['artifacts']=[{'file':name,'bytes':(out_dir/name).stat().st_size,'sha256':hashlib.sha256((out_dir/name).read_bytes()).hexdigest(),'scope':scope} for name,scope in [('heritage-next-source-features.geojson','Four exact target features, OSM-derived geometry with source metadata'),('heritage-next-neighbor-features.geojson','Local research only; mixed neighboring sources, license recheck before redistribution'),('heritage-next-footprint-context.png','Local research plot only; mixed neighboring sources, license recheck before redistribution')]]
out['reproduction']={'script':'extract_heritage_footprints.py','command':'python extract_heritage_footprints.py --repo . --out-dir /tmp/heritage-review --commit '+commit,'requirements':{'shapely':shapely.__version__,'matplotlib':matplotlib.__version__},'network':'None; existing Git objects only, lazy fetch disabled','determinism':'Target geometry and metric records are deterministic for pinned inputs and dependency versions. Plot and environment metadata may vary.'}
(out_dir/'heritage-next-footprint-review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
