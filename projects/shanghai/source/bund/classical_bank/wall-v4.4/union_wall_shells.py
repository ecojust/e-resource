"""Union captured coplanar wall shells and extrude only actual boundary edges.

No whole-building Boolean. Each group has its original oriented plane and depth.
Constrained Delaunay front/back triangles share all vertices. Hole and exterior
side walls are generated from triangle boundary edges, never from cell seams.
"""
from pathlib import Path
from collections import defaultdict,Counter
import argparse,json,math,hashlib,numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union
P=Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,default=P/'captured-wall-shells.json');ap.add_argument('--output',type=Path,default=P/'wall-union-mesh.json');args=ap.parse_args();D=json.loads(args.capture.read_text());groups=defaultdict(list)
for shell in D['shells']:
 key=(*[round(v,9) for v in shell['u']],*[round(v,9) for v in shell['v']],round(shell['front_plane_offset'],8),round(shell['depth'],8));groups[key].append(shell)
PREC=1e-8;U=np.array(D['world_basis_u']);V=np.array(D['world_basis_v']);verts=[];faces=[];reports=[]
def bake(p):
 x,y,z=np.array(p,dtype=np.float32);return [float(c) for c in np.array((U[0]*float(x)+V[0]*float(y),U[1]*float(x)+V[1]*float(y),z),dtype=np.float32)]
for gi,(key,shells) in enumerate(sorted(groups.items())):
 sh=shells[0];u=np.array(sh['u']);v=np.array(sh['v']);offset=sh['front_plane_offset'];depth=sh['depth'];polys=[Polygon(p) for sh in shells for p in sh['front_polygons']];assert all(p.is_valid and p.area>1e-12 for p in polys)
 original=unary_union(polys);region=shapely.set_precision(original,PREC);assert region.is_valid and not region.is_empty
 triangles=shapely.constrained_delaunay_triangles(region);ts=list(triangles.geoms);assert all(t.geom_type=='Polygon' for t in ts)
 union=unary_union(ts);difference=float(region.symmetric_difference(union).area);assert difference<1e-7,(gi,difference)
 snap_difference=float(original.symmetric_difference(region).area);assert snap_difference<.001,(gi,snap_difference)
 local_vertices=[];indices={};f2=[]
 def vertex2(p):
  k=(round(p[0],8),round(p[1],8))
  if k not in indices:indices[k]=len(local_vertices);local_vertices.append(k)
  return indices[k]
 for t in ts:
  q=list(t.exterior.coords)[:-1];assert len(q)==3
  if np.cross(np.array(q[1])-q[0],np.array(q[2])-q[0])<0:q.reverse()
  f2.append(tuple(vertex2(p) for p in q))
 edge_counts=Counter();directed={}
 for f in f2:
  for a,b in zip(f,f[1:]+f[:1]):k=tuple(sorted((a,b)));edge_counts[k]+=1;directed[k]=(a,b)
 assert all(n in(1,2) for n in edge_counts.values())
 boundary=[directed[k] for k,n in edge_counts.items() if n==1];o=len(verts);n=len(local_vertices)
 for d in[0,depth]:
  for s,z in local_vertices:
   xy=u*s+v*(offset+d);verts.append(bake((xy[0],xy[1],z)))
 gf=[]
 for a,b,c in f2:gf.append((o+a,o+b,o+c));gf.append((o+n+c,o+n+b,o+n+a))
 for a,b in boundary:gf.append((o+b,o+a,o+n+a,o+n+b))
 # Every new closed shell edge occurs exactly twice, with opposite direction.
 edges=Counter();balance=Counter();volume=0
 for f in gf:
  for a,b in zip(f,f[1:]+f[:1]):k=tuple(sorted((a,b)));edges[k]+=1;balance[k]+=1 if a<b else-1
  a=np.array(verts[f[0]])
  for i in range(1,len(f)-1):volume+=float(a@np.cross(verts[f[i]],verts[f[i+1]]))/6
 assert all(c==2 for c in edges.values()),(gi,'nonmanifold')
 assert all(c==0 for c in balance.values()),(gi,'inconsistent winding')
 assert volume>0,(gi,'inside out',volume)
 expected_volume=region.area*depth;assert abs(volume-expected_volume)<max(.003,expected_volume*2e-6),(gi,volume,expected_volume)
 fs=len(faces);faces.extend(gf);components=list(region.geoms) if region.geom_type=='MultiPolygon' else[region];holes=sum(len(p.interiors) for p in components)
 perimeter=sum(float(np.linalg.norm(np.array(local_vertices[a])-local_vertices[b])) for a,b in boundary)
 reports.append({'group':gi,'source_bays':[s['source_bay'] for s in shells],'u':u.tolist(),'v':v.tolist(),'front_plane_offset':offset,'depth_m':depth,'source_front_patches':len(polys),'source_patch_area_sum_m2':sum(p.area for p in polys),'union_front_area_m2':region.area,'source_union_symmetric_difference_m2':snap_difference,'triangulation_symmetric_difference_m2':difference,'components':len(components),'holes':holes,'boundary_edges':len(boundary),'boundary_perimeter_m':perimeter,'new_vertices':n*2,'new_faces':len(gf),'new_triangle_count':len(f2)*2+len(boundary)*2,'face_range':[fs,len(faces)],'closed_manifold_edges':True,'opposite_edge_directions':True,'t_junctions':0,'signed_volume_m3':volume,'expected_volume_m3':expected_volume})
result={'schema_version':'coplanar-wall-boundary-union-v1','capture_file':args.capture.name,'capture_sha256':hashlib.sha256(args.capture.read_bytes()).hexdigest(),'input_native_sha256':D['input_native_sha256'],'precision_grid_m':PREC,'method':'Per original oriented front plane and thickness, union only captured source structural front polygons; constrained Delaunay front/back with shared nodes; extrude only true polygon boundary edges.','vertices_blender_world':verts,'faces':faces,'removed_native_face_ids':sorted({i for sh in D['shells'] for i in sh['old_face_ids']}),'groups':reports}
args.output.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n');summary={'groups':len(reports),'source_bays':len(D['shells']),'original_wall_faces_replaced':len(result['removed_native_face_ids']),'new_wall_faces':len(faces),'new_vertices':len(verts),'new_triangles':sum(r['new_triangle_count'] for r in reports),'holes':sum(r['holes'] for r in reports),'max_source_union_difference_m2':max(r['source_union_symmetric_difference_m2'] for r in reports),'all_manifold_and_oriented':True};print(json.dumps(summary,indent=2))
