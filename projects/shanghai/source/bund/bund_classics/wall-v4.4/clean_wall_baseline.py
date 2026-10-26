"""Union only axis-aligned 0.45 m limestone facade-wall boxes in frozen Bund2/3.

Blender invocation: blender -b -t 1 --python clean_wall_baseline.py -- \
  --id bund02 --input bund02.blend --output bund02-clean.blend --report wall-validation.json
The original disjoint box solids are replaced with a shared, conforming u/z
grid boundary. Occupied-neighbour faces are absent; actual opening reveals,
fronts, backs and outer boundary remain. Other geometry is copied exactly.
"""
import argparse, hashlib, json, sys
from pathlib import Path
from collections import defaultdict, Counter
import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
ap=argparse.ArgumentParser()
ap.add_argument('--id',choices=['bund02','bund03'],required=True)
ap.add_argument('--input',type=Path)
ap.add_argument('--raw',type=Path,required=True)
ap.add_argument('--output',type=Path,required=True)
ap.add_argument('--report',type=Path,required=True)
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
baseline_manifest=json.loads((HERE/'baseline-manifest.json').read_text())
baseline=baseline_manifest['models'][args.id]
args.input=args.input or HERE/baseline['file']
assert hashlib.sha256(args.input.read_bytes()).hexdigest()==baseline['sha256'],'Input must match frozen published native baseline.'
source=next(c for c in json.loads((HERE/'footprints.json').read_text()) if c['id']==args.id)
bpy.ops.wm.open_mainfile(filepath=str(args.input))
obj=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.name==args.id)
old=obj.data;old.update()
assert not old.uv_layers and not old.color_attributes and not old.shape_keys,'Unexpected attributes need explicit preservation support.'
stone=next(i for i,m in enumerate(old.materials) if m.name.split('.')[0]=='limestone')
parents=list(range(len(old.vertices)))
def find(i):
 while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
 return i
def union(a,b):
 a=find(a);b=find(b)
 if a!=b:parents[b]=a
for f in old.polygons:
 for i in f.vertices[1:]:union(f.vertices[0],i)
components={}
for f in old.polygons:
 c=components.setdefault(find(f.vertices[0]),{'v':set(),'f':[],'m':set()})
 c['v'].update(f.vertices);c['f'].append(f.index);c['m'].add(f.material_index)
poly=source['polygon_local_east_north'];bases=[]
for i,p in enumerate(poly):
 A=Vector((*p,0));B=Vector((*poly[(i+1)%len(poly)],0));T=(B-A).normalized();N=Vector((T.y,-T.x,0));C=(A+B)*.5
 bases.append((C,T,N))
groups=defaultdict(list);removed=set();tol=3e-5
for c in components.values():
 if c['m']!={stone} or len(c['v'])!=8 or len(c['f'])!=12:continue
 points=[old.vertices[i].co for i in c['v']]
 if max(p.z for p in points)> (26.50003 if args.id=='bund02' else 32.40003):continue
 for fi,(C,T,N) in enumerate(bases):
  coords=[((p-C).dot(T),(p-C).dot(N),p.z) for p in points]
  lo=[min(p[k] for p in coords) for k in range(3)];hi=[max(p[k] for p in coords) for k in range(3)]
  if abs(hi[1]-lo[1]-.45)>tol or hi[0]-lo[0]<.01 or hi[2]-lo[2]<.01:continue
  if any(min(abs(p[k]-lo[k]),abs(p[k]-hi[k]))>tol for p in coords for k in range(3)):continue
  # Only the documented Facade.box default structural layer. Other limestone
  # relief, rustication and roof solids are outside these depth-plane groups.
  allowed=[.025,-.625,-1.455] if args.id=='bund02' and fi==4 else [.025]
  front=min(allowed,key=lambda d:abs(d-hi[1]))
  if abs(front-hi[1])>tol:continue
  groups[(fi,front)].append({'rect':(lo[0],hi[0],lo[2],hi[2]),'faces':c['f'],'vertices':list(c['v']),'depth_error':max(abs(lo[1]-(front-.45)),abs(hi[1]-front))})
  removed.update(c['f']);break
assert sum(len(v) for v in groups.values())>100,[(k,len(v)) for k,v in groups.items()]
verts=[tuple(v.co) for v in old.vertices];faces=[];mats=[];smooth=[]
for f in old.polygons:
 if f.index not in removed:faces.append(tuple(f.vertices));mats.append(f.material_index);smooth.append(f.use_smooth)
def clusters(values):
 out=[]
 for v in sorted(values):
  if out and abs(v-out[-1][-1])<tol:out[-1].append(v)
  else:out.append([v])
 return [sum(c)/len(c) for c in out]
reports=[]
for (fi,front),boxes in sorted(groups.items()):
 C,T,N=bases[fi]
 us=clusters([x for b in boxes for x in b['rect'][:2]])
 zs=clusters([x for b in boxes for x in b['rect'][2:]])
 occupied=set();sum_area=0;max_snap=0
 for b in boxes:
  u0,u1,z0,z1=b['rect'];ii=[min(range(len(us)),key=lambda i:abs(us[i]-u)) for u in [u0,u1]];jj=[min(range(len(zs)),key=lambda j:abs(zs[j]-z)) for z in [z0,z1]]
  max_snap=max(max_snap,*[abs(a-b) for a,b in zip([u0,u1,z0,z1],[us[ii[0]],us[ii[1]],zs[jj[0]],zs[jj[1]]])])
  sum_area+=(us[ii[1]]-us[ii[0]])*(zs[jj[1]]-zs[jj[0]])
  for i in range(*ii):
   for j in range(*jj):occupied.add((i,j))
 indices={};group_faces=[]
 def v(i,j,k):
  key=(i,j,k)
  if key not in indices:
   indices[key]=len(verts);verts.append(tuple(C+T*us[i]+N*(front-.45*(1-k))+Vector((0,0,zs[j]))))
  return indices[key]
 def face(keys,normal):
  ids=tuple(v(*k) for k in keys);a,b,c=[Vector(verts[i]) for i in ids[:3]]
  if (b-a).cross(c-a).dot(normal)<0:ids=ids[:1]+tuple(reversed(ids[1:]))
  faces.append(ids);mats.append(stone);smooth.append(False);group_faces.append(ids)
 area=0;boundary=0
 for i,j in sorted(occupied):
  area+=(us[i+1]-us[i])*(zs[j+1]-zs[j])
  for k,normal in [(0,-N),(1,N)]:face([(i,j,k),(i+1,j,k),(i+1,j+1,k),(i,j+1,k)],normal)
  if (i-1,j) not in occupied:face([(i,j,0),(i,j,1),(i,j+1,1),(i,j+1,0)],-T);boundary+=zs[j+1]-zs[j]
  if (i+1,j) not in occupied:face([(i+1,j,0),(i+1,j,1),(i+1,j+1,1),(i+1,j+1,0)],T);boundary+=zs[j+1]-zs[j]
  if (i,j-1) not in occupied:face([(i,j,0),(i,j,1),(i+1,j,1),(i+1,j,0)],Vector((0,0,-1)));boundary+=us[i+1]-us[i]
  if (i,j+1) not in occupied:face([(i,j+1,0),(i,j+1,1),(i+1,j+1,1),(i+1,j+1,0)],Vector((0,0,1)));boundary+=us[i+1]-us[i]
 edges=Counter();balance=Counter();volume=0
 for f in group_faces:
  for a,b in zip(f,f[1:]+f[:1]):edges[tuple(sorted((a,b)))]+=1;balance[tuple(sorted((a,b)))]+=1 if a<b else -1
  a=verts[f[0]]
  for k in range(1,len(f)-1):
   b,c=verts[f[k]],verts[f[k+1]]
   volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
 assert all(n==2 for n in edges.values()),('nonmanifold',fi,front)
 assert all(n==0 for n in balance.values()),('winding mismatch',fi,front)
 assert abs(volume-area*.45)<.003,(fi,volume,area*.45)
 # No internal occupied/occupied side faces can be emitted by construction;
 # all front/back cells use the same global grid, so no T-junctions exist.
 box_perimeter=sum(2*((b['rect'][1]-b['rect'][0])+(b['rect'][3]-b['rect'][2])) for b in boxes)
 reports.append({'facade_index':fi,'front_d_m':front,'boxes':len(boxes),'rectangles_before_area_m2':sum_area,'union_area_m2':area,'old_internal_side_area_removed_m2':max(0,(box_perimeter-boundary)*.45),'new_boundary_side_area_m2':boundary*.45,'grid':[len(us)-1,len(zs)-1],'occupied_cells':len(occupied),'vertices':len(indices),'quads':len(group_faces),'signed_volume_m3':volume,'manifold_edges':True,'opposite_edge_orientations':True,'t_junctions':0,'max_coordinate_snap_m':max_snap,'max_depth_canonicalization_m':max(b['depth_error'] for b in boxes)})
mesh=bpy.data.meshes.new(args.id+' conforming union facade walls');mesh.from_pydata(verts,[],faces);mesh.update()
for m in old.materials:mesh.materials.append(m)
for f,mi,sm in zip(mesh.polygons,mats,smooth):f.material_index=mi;f.use_smooth=sm
obj.data=mesh;obj['wall_topology']='Union boundary of existing .45m limestone wall boxes; shared conforming grid; no internal coplanar wall-box faces.'
args.output.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(args.output))
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
args.raw.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(args.raw),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_materials='EXPORT',export_extras=True)
sys.path.insert(0,str(HERE))
from glb_provenance import retain_provenance
retain_provenance(args.raw,args.id)
report={'id':args.id,'raw':args.raw.name,'raw_bytes':args.raw.stat().st_size,'raw_sha256':hashlib.sha256(args.raw.read_bytes()).hexdigest(),'input':args.input.name,'input_sha256':hashlib.sha256(args.input.read_bytes()).hexdigest(),'output':args.output.name,'output_sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'scope':'Only original axis-aligned .45m structural limestone wall boxes. Glass, frames, carved trim, footprint, original roof and arch spandrel polygons copied exactly.','original_faces':len(old.polygons),'removed_box_triangles':len(removed),'retained_faces_exact':len(old.polygons)-len(removed),'original_vertex_coordinates_retained':True,'new_faces':len(faces),'new_vertices':len(verts),'groups':reports,'internal_side_surfaces_removed_m2':sum(r['old_internal_side_area_removed_m2'] for r in reports),'tolerance_m':tol}
# Independent retained-face proof before serialization: identical index tuples,
# material slot and smooth flags, and every old vertex coordinate retained.
retained_old=[f for f in old.polygons if f.index not in removed]
assert len(retained_old)==len(old.polygons)-len(removed)
for f,q in zip(retained_old,mesh.polygons):
 assert tuple(f.vertices)==tuple(q.vertices) and f.material_index==q.material_index and f.use_smooth==q.use_smooth
assert all(tuple(v.co)==tuple(mesh.vertices[i].co) for i,v in enumerate(old.vertices))
report['retained_face_attributes_exact']=True
report['non_wall_components_untouched']=True
report['unchanged_materials']=[{'name':m.name,'diffuse_color':list(m.diffuse_color)} for m in old.materials]
report['removed_faces']=sorted(removed)
assert args.raw.stat().st_size<100_000_000 and args.output.stat().st_size<100_000_000
args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('WALL_UNION_REPORT',json.dumps({k:v for k,v in report.items() if k not in ['groups','removed_faces','unchanged_materials']}))
