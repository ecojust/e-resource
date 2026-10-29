"""Bind real map components, model obstacle and finite exterior navigation probes."""
import argparse,gzip,hashlib,json,math
from pathlib import Path
import numpy as np,trimesh
from shapely.geometry import shape,Polygon,Point,LineString,MultiPoint,mapping
from shapely.ops import transform,unary_union
p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--live',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--id',default='xuhui-zikawei-south-building');p.add_argument('--distance',type=float,default=35);p.add_argument('--convex-obstacle',action='store_true');a=p.parse_args();ID=a.id;P=a.project;g=json.loads((P/f'source/precise/{ID}/geometry-input.json').read_text());g.setdefault('source_owner','building:'+g['feature'].get('id',g['feature']['properties']['id']));anchor=g['anchor'];c=math.cos(math.radians(anchor[1]));R=6378137.;my=math.asinh(math.tan(math.radians(anchor[1])))
def local(lon,lat,z=None):return (R*np.radians(np.asarray(lon)-anchor[0])*c,R*(np.arcsinh(np.tan(np.radians(lat)))-my)*c)
def world(x,y,z=None):return (anchor[0]+np.degrees(np.asarray(x)/(R*c)),np.degrees(np.arctan(np.sinh(my+np.asarray(y)/(R*c)))))
source=transform(local,shape(g['feature']['geometry']));live=json.loads(a.live.read_text());matches=[];evidence=[];seen=set()
for f in live['features']:
 parts=f['geometry']['coordinates'] if f['geometry']['type']=='MultiPolygon' else [f['geometry']['coordinates']]
 for k,coords in enumerate(parts):
  component={'type':'Polygon','coordinates':coords};poly=transform(local,shape(component))
  if poly.intersection(source).area/source.area <.98:continue
  assert poly.symmetric_difference(source).area<.2,'Live component differs from frozen source'
  key=(f['source'],f['id'],json.dumps(component,sort_keys=True))
  if key in seen:continue
  seen.add(key);m={'source':f['source'],'source_layer':'building','native_id':f['id'],'component':component,'observed_component_index':k}
  if f['source']=='overture-buildings':assert f['id']==g['source_owner'].split(':')[1];m['property_id']=f['properties']['id']
  matches.append(m);evidence.append({'match':m,'properties':f['properties'],'original_component_count':len(parts),'symmetric_difference_m2':poly.symmetric_difference(source).area})
assert {m['source'] for m in matches}=={'openmaptiles','overture-buildings'}
asset=P/f'assets/models/candidates/{ID}/{ID}-raw.glb';scene=trimesh.load(asset,force='scene',process=False);verts=np.concatenate([m.vertices for m in scene.geometry.values()]);hull=MultiPoint(verts[:,[0,2]]*[1,-1]).convex_hull
low=[]
for mesh in scene.geometry.values():
 for tri in mesh.triangles:
  if tri[:,1].min()>2.3:continue
  poly=Polygon(tri[:,[0,2]]*[1,-1])
  if poly.area>1e-7:low.append(poly)
obstacle=unary_union(low)
if a.convex_obstacle:obstacle=obstacle.convex_hull
obstacle=obstacle.buffer(.02,join_style=2).simplify(.002,preserve_topology=True);assert obstacle.geom_type=='Polygon' and not obstacle.interiors
X=np.array(g['architecture_X_EN']);Y=np.array(g['architecture_Y_EN']);start=-a.distance*Y;forward=Y;end=start+5*forward;target=start+2.8*forward;eye=target-14*math.sin(math.radians(82))*forward
probes={'spawn':Point(start).buffer(.38),'first_5m':LineString([start,end]).buffer(.38),'camera':Point(eye).buffer(.12),'camera_boom':LineString([target,eye]).buffer(.12)}
assert all(not geom.intersects(obstacle) for geom in probes.values())
checks=[];inputs=[];owners=[]
_,mx,myz=map(int,g['macro'].split('-'))
for tx in [mx-1,mx,mx+1]:
 for ty in [myz-1,myz,myz+1]:
  macro=f'14-{tx}-{ty}';f=P/f'assets/city-detail/macros/{macro}/feature-table.json.gz';inputs.append({'file':str(f.relative_to(P)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()});table=json.loads(gzip.decompress(f.read_bytes()))
  for row in table['features']:
   geom=shape(row['geometry']);bounds=geom.bounds
   if bounds[2]<anchor[0]-.003 or bounds[0]>anchor[0]+.003 or bounds[3]<anchor[1]-.003 or bounds[1]>anchor[1]+.003:continue
   poly=transform(local,geom)
   if row['key']==g['source_owner']:owners.append([macro,row['localId']]);continue
   if poly.distance(source)>100:continue
   overlap=hull.intersection(poly).area
   hit={k:poly.intersection(v).area for k,v in probes.items()}
   checks.append({'macro':macro,'local_id':row['localId'],'key':row['key'],'hull_overlap_m2':overlap,'obstacle_overlap_m2':obstacle.intersection(poly).area,'probe_overlap_m2':hit})
assert owners==[[g['macro'],g['feature_local_id']]]
assert all(q['hull_overlap_m2']<1e-6 and q['obstacle_overlap_m2']<1e-6 and max(q['probe_overlap_m2'].values())<1e-6 for q in checks)
nav={'listed':True,'walkStart':list(world(*start)),'bearing':math.degrees(math.atan2(forward[0],forward[1]))%360,'overviewZoom':18}
report={'id':ID,'raw_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'anchor':anchor,'navigation':nav,'source_identity':g['source_owner'],'matches':matches,'live_source_evidence':evidence,'live_capture_sha256':hashlib.sha256(a.live.read_bytes()).hexdigest(),'collision_geometry':mapping(transform(world,obstacle)),'obstacle_area_m2':obstacle.area,'convex_obstacle':a.convex_obstacle,'source_tables':inputs,'neighbor_checks':checks,'finite_exterior_probes_clear':True,'probe_ground_scope':'Virtual flat ground at 0.075m; no measured terrain, indoor or veranda access. Actual movement and online water/road checks remain browser verification.','owner_count':len(owners)}
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'navigation':nav,'neighbors':len(checks),'matches':len(matches),'area':obstacle.area}))
