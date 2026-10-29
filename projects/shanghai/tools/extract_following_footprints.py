"""Review three frozen candidate-map footprints offline.
Run at repository root with --repo . --out-dir /tmp/following-footprints.
Requires shapely and matplotlib. Original code MIT; three target OSM-derived
geometries retain ODbL-1.0. Neighbors/plot are private mixed-source research only.
"""
from pathlib import Path
import argparse,subprocess,os,json,math,hashlib,sys
import shapely
from shapely.geometry import shape
from shapely.ops import transform
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo',type=Path,default=Path('.'));parser.add_argument('--out-dir',type=Path,required=True);parser.add_argument('--commit',default='29059e3b8d131e7dadcf1d8e61c5335a88b4c30f');args=parser.parse_args();repo=args.repo.resolve();out=args.out_dir;out.mkdir(parents=True,exist_ok=True);env=dict(os.environ,GIT_NO_LAZY_FETCH='1');commit=subprocess.check_output(['git','rev-parse',args.commit],cwd=repo,text=True).strip();inputs={}
def read(path):
 b=subprocess.check_output(['git','show',commit+':'+path],cwd=repo,env=env);inputs[path]={'path':path,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return json.loads(b)
source_path='projects/shanghai/data/audit/landmark-candidate-features.geojson';source=read(source_path);features=source['features'];by_id={f['id']:f for f in features};refs=read('projects/shanghai/data/model-todo/heritage-following-building-references.json');names=read('projects/shanghai/data/model-todo/named-map-leads.json');name_by={r['id']:r for r in names['records']}
subjects=[(19,'huangpu-park-hotel','64ff37d4-ed69-464b-af4c-3ba55de36d38','Park Hotel'),(20,'huangpu-shanghai-race-club-east-building','9402a15a-c2dc-478e-87b5-3236bc4c0b8b','Shanghai Race Club'),(21,'huangpu-grand-theatre','b6b8b7dd-5999-4d4d-b1d1-29e282f7a73d','Grand Cinema')]
a=6378137.0;inverse_flattening=298.257223563;flattening=1/inverse_flattening;e2=flattening*(2-flattening)
def ecef(lon,lat):
 lo=math.radians(lon);la=math.radians(lat);N=a/math.sqrt(1-e2*math.sin(la)**2)
 return N*math.cos(la)*math.cos(lo),N*math.cos(la)*math.sin(lo),N*(1-e2)*math.sin(la)
def projector(lon0,lat0):
 x0,y0,z0=ecef(lon0,lat0);lo=math.radians(lon0);la=math.radians(lat0)
 def en(lon,lat,z=None):
  x,y,z=ecef(lon,lat);dx,dy,dz=x-x0,y-y0,z-z0
  return -math.sin(lo)*dx+math.cos(lo)*dy,-math.sin(la)*math.cos(lo)*dx-math.sin(la)*math.sin(lo)*dy+math.cos(la)*dz
 return en
# Precompute only centroids; final neighborhood inclusion uses polygon distances.
geoms={f['id']:shape(f['geometry']) for f in features};centroids={id_:(g.centroid.x,g.centroid.y) for id_,g in geoms.items()}
records=[];targets=[];fig,axes=plt.subplots(1,3,figsize=(18,7))
for (order,asset_id,id_,title),ax in zip(subjects,axes):
 feat=by_id[id_];props=feat['properties'];g=geoms[id_];lon0,lat0=centroids[id_];project=projector(lon0,lat0);metric=transform(project,g);rect=metric.minimum_rotated_rectangle;corners=list(rect.exterior.coords)[:-1];edges=[]
 for i in range(4):
  x1,y1=corners[i];x2,y2=corners[(i+1)%4];edges.append((math.hypot(x2-x1,y2-y1),math.degrees(math.atan2(x2-x1,y2-y1))%180))
 long_axis,bearing=max(edges);short_axis=min(x[0] for x in edges);minx,miny,maxx,maxy=metric.bounds;coords=list(metric.exterior.coords)
 areasum=abs(sum(coords[i][0]*coords[i+1][1]-coords[i+1][0]*coords[i][1] for i in range(len(coords)-1)))/2
 assert abs(areasum-metric.area)<1e-7 and g.is_valid
 original_osm_ids=[s['record_id'] for s in props.get('sources',[]) if s.get('provider')=='osm'];assert original_osm_ids and all(s.get('license')=='ODbL-1.0' for s in props['sources'])
 same_source=[];linked=[]
 for other in features:
  if other['id']==id_:continue
  op=other['properties'];oids={s.get('record_id') for s in op.get('sources',[]) if s.get('provider')=='osm'}
  if set(original_osm_ids)&oids:same_source.append({'id':other['id'],'source_layer':op.get('source_layer'),'building_id':op.get('building_id')})
  if op.get('building_id')==id_:linked.append({'id':other['id'],'source_layer':op.get('source_layer'),'sources':op.get('sources',[])})
 neighbors=[]
 for other in features:
  oid=other['id']
  if oid==id_:continue
  olon,olat=centroids[oid]
  if abs(olon-lon0)>.002 or abs(olat-lat0)>.002:continue
  om=transform(project,geoms[oid]);dist=metric.distance(om)
  if dist>=65:continue
  op=other['properties'];neighbors.append({'id':oid,'name':op.get('@name'),'source_layer':op.get('source_layer'),'building_id':op.get('building_id'),'sources':op.get('sources',[]),'distance_m':dist,'intersection_area_m2':metric.intersection(om).area,'area_m2':om.area,'note':'Local limited candidate index only; not complete neighboring-building or legal-boundary registry'})
  for poly in (list(om.geoms) if hasattr(om,'geoms') else [om]):
   if hasattr(poly,'exterior'):
    xx,yy=poly.exterior.xy;ax.plot(xx,yy,color='#aaa',linewidth=.8)
  if dist<20:ax.text(om.centroid.x,om.centroid.y,oid[:8],fontsize=6,color='#777')
 neighbors.sort(key=lambda n:(n['distance_m'],n['id']))
 rec={'queue_order':order,'proposed_asset_id':asset_id,'id':id_,'name':props.get('@name'),'map_identity_hint':name_by[id_],'original_properties':props,'original_geometry_path':'heritage-following-source-features.geojson','coordinate_status':'Exact coordinates of frozen derived audit index; direct original OSM response and preprocessing not independently recovered','geometry_type':g.geom_type,'polygon_valid':g.is_valid,'polygon_simple':g.is_simple,'interior_ring_count':len(g.interiors),'unique_exterior_vertices':len(g.exterior.coords)-1,'bbox_wgs84':list(g.bounds),'local_origin_wgs84':[lon0,lat0],'local_exterior_enu_m':[list(c) for c in coords],'local_aabb_east_north_m':[maxx-minx,maxy-miny],'local_area_m2':metric.area,'local_perimeter_m':metric.length,'minimum_rotated_rectangle':{'corners_enu_m':[list(c) for c in corners],'long_axis_m':long_axis,'short_axis_m':short_axis,'long_axis_bearing_clockwise_from_north_deg_mod180':bearing,'axis_is_not_verified_front_direction':True},'convex_hull_area_m2':metric.convex_hull.area,'convex_hull_area_difference_m2':metric.convex_hull.area-metric.area,'source_height_m':props.get('height'),'source_num_floors':props.get('num_floors'),'source_min_height_m':props.get('min_height'),'parent_part_review':{'source_layer':props.get('source_layer'),'building_id':props.get('building_id'),'has_parts':props.get('has_parts'),'linked_parts_found_in_this_index':linked,'other_features_with_same_osm_source_record':same_source,'limit':'No related part in this bounded audit index does not prove that original OSM or the real building has no parts'},'nearby_index_records_within_65m':neighbors,'historical_main_building_boundary_accepted':False,'geographic_registration_accepted':False}
 records.append(rec);targets.append(feat)
 xx,yy=metric.exterior.xy;ax.fill(xx,yy,color='#b95528',alpha=.55);ax.plot(xx,yy,color='#8b2516',linewidth=2);xx,yy=rect.exterior.xy;ax.plot(xx,yy,color='#276894',linestyle='--',linewidth=1);ax.set_title(title);ax.set_aspect('equal');ax.grid(alpha=.2);ax.set_xlabel('East from target centroid (m)');ax.set_ylabel('North from target centroid (m)');ax.set_xlim(-100,100);ax.set_ylim(-105,105)
notes={
19:{'status':'Coarse four-corner outline only; historical tower/lower-body and later rear-block boundary unresolved','reasons':['Source polygon is a simple four-corner footprint with no upper-level setback, tower or rear-block segmentation. No part, height or floor-count fields resolve the historical main building.','Reference sources distinguish historical site1179m2 and later site1827m2 after rear-block additions. Polygon area cannot by itself identify either site, historical main-wall line or time period.','The2007 photograph shows tower and an attached lower body, but not the full rear plan; same-frame pale Sports Building/Golden Gate hotel and a glass tower are separate until independently bound.','No neighbor polygons were unioned or substituted. Width/depth are map-outline measurements only, not historically surveyed dimensions.']},
20:{'status':'ROOF325 alias is a map identity lead, not an accepted east-main-building or clock-tower footprint','reasons':['Source is an eight-corner long stepped outline without separate clock-tower, east/west-building or courtyard parts. The alias and restaurant/roof name alone cannot allocate historical museum structures.','The2018 documentary complex includes east4/local5 floors, west3 floors and a courtyard basement. This map polygon has no height or floor count, so cannot select one documentary building or tower from those values.','The map minimum rotated long side is about98.45m, while secondary text describes the main body as over100m. Endpoints or building scope may differ but are unverified; do not rescale the map to reach100m or declare either source false.','The main tall clock tower and west-building/small-tower must remain independently scoped. Similar facade style and a same-frame curved ICBC neighbor/red-tile mass/white rear building do not establish membership.','Full-site footprint or historical outside-wall confirmation requires separate source/plan correspondence; no automatic city replacement based on this name.']},
21:{'status':'Six-corner irregular map outline only; cinema frontage, shops and rear auditorium separation unresolved','reasons':['Source outline has no independent entrance/light-column or auditorium part; no height/floor fields establish which mass has which source dimension.','Historical ground plan and text describe an approximately30deg relationship between frontage and auditorium axes. A six-corner outer map polygon alone neither reproduces nor independently verifies those two internal axes or modern facade boundary.','Source height claims30.5m and16m remain unresolved; map has no height field to decide them. Floor descriptions2/3/4 in different documentary scopes remain unresolved.','Do not include the entire street-shop strip or a rear tall neighbor automatically; current main-building and auditorium boundary needs photograph/plan binding.']}}
for r in records:r['interpretation']=notes[r['queue_order']]
fig.suptitle('Frozen audit footprints only; historical-building boundaries and floor assignments unverified');fig.tight_layout();plot='heritage-following-footprint-context.png';fig.savefig(out/plot,dpi=150)
target_name='heritage-following-source-features.geojson';(out/target_name).write_text(json.dumps({'type':'FeatureCollection','features':targets},ensure_ascii=False,indent=2)+'\n')
report={'schema':'heritage-following-footprint-review-v1','reviewed_utc':'2026-10-29','repository_commit':commit,'scope':'Local frozen map footprint review for queue19–21. Three map identity leads only; no historical-boundary, floor-level, model or geographic acceptance.','source':dict(inputs[source_path],git_commit=commit,feature_count=len(features),status='Derived candidate audit geometry, not direct original OSM response'),'reference_inputs':[v for k,v in inputs.items() if k!=source_path],'method':{'python':sys.version.split()[0],'shapely':shapely.__version__,'coordinate_transform':'WGS84 lon/lat at ellipsoid height0 to ECEF, then local east/north tangent plane at each polygon centroid; metres, not surveyed precision','wgs84_a_m':a,'wgs84_inverse_flattening':inverse_flattening,'dimensions':'ENU axis-aligned bounds and GEOS minimum rotated rectangle; bearing clockwise from north modulo180, not accepted facade orientation','neighbors':'Existing limited audit-index geometries within65m polygon distance; centroid prefilter within0.002degree, not a full nearby inventory; nothing unioned into targets','arithmetic_check':'Shoelace polygon area independently equals GEOS polygon area within1e-7m2'},'records':records,'rights':{'target_geometry_license':'ODbL-1.0','attribution':'© OpenStreetMap contributors; all three targets identify OpenStreetMap through source metadata','neighbor_context_note':'Neighbor metadata retains each source. Some sources identify Zenodo without a licence field; neighboring geometry and mixed-source context plot are local research aids only. No neighboring GeoJSON is published.','photo_pixels_redistributed':False},'artifacts':[{'file':n,'bytes':(out/n).stat().st_size,'sha256':hashlib.sha256((out/n).read_bytes()).hexdigest(),'published_candidate':n==target_name,'scope':'Exact three OSM-derived target features' if n==target_name else 'Local mixed-source research plot only; not for repository publication without source-license verification'} for n in [target_name,plot]],'reproduction':{'script':'extract_following_footprints.py','command':'python extract_following_footprints.py --repo . --out-dir /tmp/following-footprints --commit '+commit,'requirements':{'shapely':shapely.__version__,'matplotlib':matplotlib.__version__},'network':'None; existing Git objects only with GIT_NO_LAZY_FETCH=1','determinism':'Target GeoJSON and metric records deterministic for pinned inputs/dependencies; plot/environment metadata may vary.'},'next_action':'Use outlines only as labelled map context; bind historical main-wall boundaries and excluded later blocks before adopting dimensions or city replacement. Keep documentary and map measurements separate.'}
report['independent_shape_review']={'reviewed_by':'independent child split_notes','map_context_plot_actually_viewed':True,'published_reference_scope_and_cached_photos_reviewed':True,'observations':['Park rectangle cannot separate historical tower, lower body and later rear block; separate Sports Building remains separate.','Race stepped end does not locate clock-tower base or bind historical east-building parts;98.45m map extent and over100m text remain unresolved.','Grand irregular outline cannot by itself establish historical30deg entrance/auditorium relationship or split modern shop and theatre boundaries.'],'historical_boundary_or_geographic_acceptance':False}
(out/'heritage-following-footprint-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
for r in records:print(r['queue_order'],r['id'],r['local_area_m2'],r['minimum_rotated_rectangle']['long_axis_m'],r['minimum_rotated_rectangle']['short_axis_m'],len(r['nearby_index_records_within_65m']))
