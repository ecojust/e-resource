"""Fill unintended through-joints in Bund 18 without touching original meshes.

Run in Blender 4.3. The current published v4.3 native/raw pair is the baseline.
The two new backing solids have conforming front/back grids and boundary sides
only: occupied cells never generate coincident internal side walls.
"""
import argparse,bpy,json,math,sys,hashlib,struct
from pathlib import Path
from collections import Counter
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--input-native',type=Path,required=True);ap.add_argument('--input-raw',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--spec',type=Path,default=ROOT/'wall-core-input.json')
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
spec=json.loads(a.spec.read_text());a.output.mkdir(parents=True,exist_ok=True)
for path,key in [(a.input_native,'assets/native/bund/bund18.blend'),(a.input_raw,'assets/models/bund/bund18.glb')]:
 actual=hashlib.sha256(path.read_bytes()).hexdigest()
 if actual!=spec['baseline'][key]['sha256']:raise ValueError(f'Unexpected baseline {path.name}: {actual}')
bpy.ops.wm.open_mainfile(filepath=str(a.input_native))
model=bpy.data.collections['MODEL_Bund18_Chartered_Bank']
if any(o.name.startswith('Bund18_WallCore_') for o in model.objects):raise ValueError('Already patched; supply the frozen v4.3 baseline.')

def signature(obj):
 m=obj.data
 blob={'vertices':[list(v.co) for v in m.vertices],'polygons':[(list(p.vertices),p.material_index,p.use_smooth) for p in m.polygons],
  'uv':{uv.name:[list(x.uv) for x in uv.data] for uv in m.uv_layers},'materials':[x.name for x in m.materials],
  'transform':[list(x) for x in obj.matrix_world]}
 return hashlib.sha256(json.dumps(blob,separators=(',',':')).encode()).hexdigest()
original={o.name:signature(o) for o in model.objects if o.type=='MESH'}
A,B=map(Vector,spec['coordinate_basis']['front_edge']);T=(B-A).normalized();N=Vector((-T.y,T.x));C=(A+B)/2
scale=spec['coordinate_basis']['vertical_scale'];front=spec['mortar']['front_recess_m'];back=spec['mortar']['back_depth_m']
mat=bpy.data.materials.new('Bund18_Recessed_LimeMortar');mat.use_nodes=True;mat.diffuse_color=(*spec['mortar']['base_color_linear'],1)
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=mat.diffuse_color;bs.inputs['Roughness'].default_value=spec['mortar']['roughness'];bs.inputs['Metallic'].default_value=0
mat['reconstruction_estimate']='Lime mortar/backing inferred; exact depth and colour not surveyed.'
reports=[]
for wall in spec['walls']:
 x0,x1,z0,z1=wall['rectangle'];holes=wall['holes'];offset=wall['depth_offset']
 xs=sorted(set([x0,x1]+[max(x0,min(x1,v)) for h in holes for v in h[:2]]));zs=sorted(set([z0,z1]+[max(z0,min(z1,v)) for h in holes for v in h[2:]]))
 occupied=set()
 for ix,(lo,hi) in enumerate(zip(xs,xs[1:])):
  for iz,(bot,top) in enumerate(zip(zs,zs[1:])):
   if hi-lo<.01 or top-bot<.01:continue
   if any(h[0]<(lo+hi)/2<h[1] and h[2]<(bot+top)/2<h[3] for h in holes):continue
   occupied.add((ix,iz))
 vertices=[];faces=[];indices={};boundary_sides=0;area=0;stone_area=0
 def vertex(ix,iz,layer):
  key=(ix,iz,layer)
  if key not in indices:
   x,z=xs[ix],zs[iz]*scale;y=offset+(front if layer==0 else back)
   indices[key]=len(vertices);vertices.append((C.x+T.x*x+N.x*y,C.y+T.y*x+N.y*y,z))
  return indices[key]
 def face(keys):faces.append(tuple(vertex(*k) for k in keys))
 for ix,iz in sorted(occupied):
  # Front (-N) and back (+N), common vertices across every complete grid edge.
  face([(ix,iz,0),(ix+1,iz,0),(ix+1,iz+1,0),(ix,iz+1,0)])
  face([(ix,iz+1,1),(ix+1,iz+1,1),(ix+1,iz,1),(ix,iz,1)])
  # Wall/void interfaces only. No face is generated between occupied cells.
  if (ix-1,iz) not in occupied:
   face([(ix,iz,1),(ix,iz,0),(ix,iz+1,0),(ix,iz+1,1)]);boundary_sides+=1
  if (ix+1,iz) not in occupied:
   face([(ix+1,iz,0),(ix+1,iz,1),(ix+1,iz+1,1),(ix+1,iz+1,0)]);boundary_sides+=1
  if (ix,iz-1) not in occupied:
   face([(ix,iz,1),(ix+1,iz,1),(ix+1,iz,0),(ix,iz,0)]);boundary_sides+=1
  if (ix,iz+1) not in occupied:
   face([(ix,iz+1,0),(ix+1,iz+1,0),(ix+1,iz+1,1),(ix,iz+1,1)]);boundary_sides+=1
  width,height=xs[ix+1]-xs[ix],zs[iz+1]-zs[iz];area+=width*height*scale
  columns=max(1,math.ceil(width/1.15));rows=max(1,math.ceil(height/.55))
  stone_area+=columns*rows*(width/columns-.012)*(height/rows-.014)*scale
 edges=Counter(tuple(sorted((p[i],p[(i+1)%len(p)]))) for p in faces for i in range(len(p)))
 assert set(edges.values())=={2},Counter(edges.values())
 assert len(set(tuple(sorted(p)) for p in faces))==len(faces)
 mesh=bpy.data.meshes.new('Bund18_WallCore_'+wall['id']);mesh.from_pydata(vertices,[],faces);mesh.materials.append(mat);mesh.update();mesh.calc_loop_triangles()
 obj=bpy.data.objects.new(mesh.name,mesh);model.objects.link(obj)
 obj['purpose']='Recessed continuous backing prevents daylight through 12/14mm masonry joints; holes unchanged.'
 obj['source']='wall-core-input.json';obj['reconstruction_estimate']='18mm front recess; .525m back depth; shade estimated.'
 # All added faces lie within the occupied 2-D wall union. The declared hole
 # centres and their safe interior corner offsets must all remain outside it.
 hole_points=0
 for h in holes:
  for px,pz in [((h[0]+h[1])/2,(h[2]+h[3])/2),*( (h[i]+(.001 if i==0 else -.001),h[j]+(.001 if j==2 else -.001)) for i in (0,1) for j in (2,3))]:
   assert not any(xs[ix]<px<xs[ix+1] and zs[iz]<pz<zs[iz+1] for ix,iz in occupied);hole_points+=1
 reports.append({'wall':wall['id'],'occupied_grid_cells':len(occupied),'vertices':len(vertices),'quads':len(faces),'triangles':len(mesh.loop_triangles),'boundary_side_quads':boundary_sides,'internal_side_faces':0,'undirected_edge_incidence':dict(Counter(edges.values())),'duplicate_faces':0,'front_union_area_m2':area,'nominal_open_joint_area_before_repair_m2':area-stone_area,'joint_area_note':'Upper bound before overlying trims/columns; not exact screen-visible area.','hole_interior_points_clear':hole_points,'volume_m3':area*(back-front)})
assert {o.name:signature(o) for o in model.objects if o.name in original}==original
bpy.ops.object.select_all(action='DESELECT')
for obj in model.objects:obj.select_set(True)
bpy.context.view_layer.objects.active=next(iter(model.objects))
raw=a.input_raw.read_bytes();n,_=struct.unpack_from('<II',raw,12);copyright=json.loads(raw[20:20+n])['asset']['copyright']
bpy.ops.export_scene.gltf(filepath=str(a.output/'bund18-wall-core.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_materials='EXPORT',export_copyright=copyright)
bpy.context.scene['wall_core_repair']='Two conforming backing solids; original meshes and photo UV unchanged; 18mm mortar recess estimated.'
bpy.ops.wm.save_as_mainfile(filepath=str(a.output/'bund18-wall-core.blend'))
report={'baseline':spec['baseline'],'original_mesh_count':len(original),'original_native_mesh_signatures_unchanged':True,'original_mesh_signatures':original,'mortar':spec['mortar'],'walls':reports,'added_triangles':sum(w['triangles'] for w in reports),'asset_bytes':{p.name:p.stat().st_size for p in [a.output/'bund18-wall-core.glb',a.output/'bund18-wall-core.blend']}}
for v in report['asset_bytes'].values():assert v<100_000_000
(a.output/'wall-core-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
