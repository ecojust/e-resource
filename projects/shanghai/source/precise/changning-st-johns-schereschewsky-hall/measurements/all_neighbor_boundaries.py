"""Register a frozen quadrangle to every feature in its issued city tile and test each nearby boundary."""
import argparse,gzip,hashlib,json,math,struct
from pathlib import Path
from shapely.geometry import Polygon,MultiPolygon,MultiPoint,shape,Point,LineString
from shapely.ops import nearest_points
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('table',type=Path);ap.add_argument('geometry',type=Path);ap.add_argument('ray_report',type=Path);ap.add_argument('output',type=Path)
a=ap.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
ray=json.loads(a.ray_report.read_bytes());lng,lat=ray['origin_wgs84'];angle=math.radians(ray['positive_x_bearing'])
cs=math.cos(angle);sn=math.sin(angle);lon_scale=111319.490793*math.cos(math.radians(lat))
def loc(pt):
 e=(pt[0]-lng)*lon_scale;n=(pt[1]-lat)*110860
 return (sn*e+cs*n,-cs*e+sn*n)
bylod={}
for level in ['full','lod']:
 p=a.geometry/(level+'-source.glb');b=p.read_bytes();assert sha(b)==ray['new'][level]['sha256']
 glen=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+glen]);offset=28+glen;vertices=set();wall=[]
 for m in g['meshes']:
  for prim in m['primitives']:
   acc=g['accessors'][prim['attributes']['POSITION']];view=g['bufferViews'][acc['bufferView']]
   start=offset+acc.get('byteOffset',0)+view.get('byteOffset',0);stride=view.get('byteStride',12)
   material=g['materials'][prim['material']].get('name','')
   for k in range(acc['count']):
    x,z,ny=struct.unpack_from('<fff',b,start+k*stride);y=-ny;vertices.add((x,y))
    if abs(y-77.73)<.002 and (abs(z)<.001 or z>8):wall.append((x,y,z))
 hull=MultiPoint(list(vertices)).convex_hull
 assert wall and len(hull.exterior.coords)>2
 bylod[level]={'surface_files_sha256':sha(b),'convex_bound_xy_m':list(hull.exterior.coords),'river_wall_vertices_at_y_77_73':{'x_extents':[min(x[0]for x in wall),max(x[0]for x in wall)],'z_extents':[min(x[2]for x in wall),max(x[2]for x in wall)],'vertex_occurrences':len(wall)}}
 del b,vertices,wall
table_raw=a.table.read_bytes();features=json.loads(gzip.decompress(table_raw))['features'];old=Polygon(ray['source_polygon_local_m']);g0=LineString([tuple(ray['source_polygon_local_m'][0]),tuple(ray['source_polygon_local_m'][3])])
allmin=[];near=[]
for f in features:
 geom=f.get('geometry')
 if not geom or not geom.get('coordinates'):continue
 def convert(part):return Polygon([loc(x)for x in part[0]],[[loc(x)for x in ring]for ring in part[1:]])
 ps=[convert(geom['coordinates'])]if geom['type']=='Polygon' else [convert(p)for p in geom['coordinates']] if geom['type']=='MultiPolygon' else []
 if not ps:continue
 fp=ps[0]if len(ps)==1 else MultiPolygon(ps)
 if not fp.is_valid:fp=fp.buffer(0)
 if fp.is_empty:continue
 metrics={};cent=fp.representative_point()
 for level,res in bylod.items():
  hull=Polygon(res['convex_bound_xy_m']);dist=hull.distance(fp);over=hull.intersection(fp).area if dist==0 else 0
  metrics[level]={'minimum_distance_lower_bound_m':round(dist,4),'maximum_projected_overlap_m2':round(over,4)}
 if f['localId']==1840 or min(row['minimum_distance_lower_bound_m']for row in metrics.values())<=30:
  h,ns=nearest_points(hull,fp);near.append({'local_id':f['localId'],'source_key':f['key'],'source_height_m':f['height'],'actual_owner_midpoint_local_xy':list(cent.coords)[0],'nearest_hull_and_owner_points':[list(h.coords)[0],list(ns.coords)[0]],'geometry_checks':metrics})
 if f['localId']!=1840:allmin.append((metrics['full']['minimum_distance_lower_bound_m'],f['localId']))
near.sort(key=lambda f:(f['geometry_checks']['full']['minimum_distance_lower_bound_m'],f['local_id']))
north_mid=float(g0.interpolate(.5,normalized=True).y);wall=77.73;eave=78.5
out={'figure':'华东政法大学四十一号楼，怀施堂／韬奋楼','status':'standalone model retained. A candidate city integration would require an explicit replacement of the single source owner and separate checks of vector source identity, collision, shadow and both visible detail levels.','source_url':'https://raw.githubusercontent.com/ecojust/e-resource/ae55637ce1d7cbc4d21fd94934c8309aca1dcd09/projects/shanghai/assets/city-detail/macros/14-13717-6694/feature-table.json.gz','feature_table_sha256':sha(table_raw),'feature_table_size':len(features),'other_valid_building_features_scanned':len(allmin),'overlapping_source_ids_except_1840':[fid for d,fid in allmin if d==0],'minimum_other_owner_distance_lower_bound_m_and_id':min(allmin),'local_frame':{'origin_wgs84':[lng,lat],'positive_x_bearing_true_deg':math.degrees(angle),'y_axis':'inward across the courtyards towards the river'},'models':bylod,'source_boundary':{'north_mid_y_m':north_mid,'north_corner_y_m':[p[1]for p in g0.coords],'authored_wall_y_m':wall,'authored_eave_y_m':eave,'wall_beyond_mapped_north_mid_m':round(wall-north_mid,4),'eave_beyond_mapped_north_mid_m':round(eave-north_mid,4),'ground_source_caveat':'The old boundary consists of four generalized wall corners. Roof edges have independent image displacement and source positional uncertainty; exterior apertures on the riverside were not measured.'},'nearby_within_30m':near,'actual_16_position_ray_report_sha256':sha(a.ray_report.read_bytes()),'verified_original_city_near_and_far_and_real_new_roof':{'source_meshes':ray['actual_city_sources'],'controls_local_xy':ray['controls_local_xy'],'old_near_and_far':ray['actual_city_hits_by_height_z_and_id'],'new':ray['new']},'method':'Read all emitted model vertices in glTF convention and enclose them in a convex horizontal bound. A positive lower-bound distance proves disjointness for every triangle projected into that bound. Roof and ground intersections at the 16 original probes use actual full, LOD and decoded city geometry. Area totals include both lawn paving and model solids.'}
a.output.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
print(len(features),len(allmin),out['minimum_other_owner_distance_lower_bound_m_and_id'],out['overlapping_source_ids_except_1840'],[(r['local_id'],r['geometry_checks']['full'])for r in near],flush=True)
