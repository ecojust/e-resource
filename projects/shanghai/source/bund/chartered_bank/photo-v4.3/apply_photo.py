"""Assign the unchanged, attributed photograph to selected existing 3-D faces.
No image is retouched or generated. Unknown/occluded surfaces keep the original
materials. This is a single-view reconstruction, not photogrammetry.
"""
import bpy,json,math,hashlib,argparse,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,default=ROOT/'geometry/chartered-bank.blend');ap.add_argument('--output',type=Path,default=ROOT/'textured');ap.add_argument('--photo',type=Path);ap.add_argument('--render',action='store_true')
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=args.output;OUT.mkdir(parents=True,exist_ok=True)
PHOTO=args.photo
if PHOTO is None:
 for ancestor in [ROOT,*ROOT.parents]:
  candidate=ancestor/'assets/references/bund/bund18.jpg'
  if candidate.exists():PHOTO=candidate;break
if PHOTO is None:raise FileNotFoundError('Specify --photo or place source within the Shanghai project.')
bpy.ops.wm.open_mainfile(filepath=str(args.input))
DATA_ROOT=ROOT if (ROOT/'building-source.json').exists() else ROOT.parent
source=json.loads((DATA_ROOT/'building-source.json').read_text())
A,B=map(Vector,source['streetfront']['candidate_edges'][0]['endpoints_local_east_north_m'])
T=(B-A).normalized();N=Vector((-T.y,T.x));C=(A+B)/2
image=bpy.data.images.load(str(PHOTO),check_existing=True);image.pack();image.filepath='//bund18.jpg'
original_sha=hashlib.sha256(PHOTO.read_bytes()).hexdigest()
# Pixel coordinates below use the explicitly recorded 1884 x 1344 reference
# display coordinate basis. UV normalization uses exactly that same basis.
width,height=1884,1344
centre_x,ground_y,px_per_m=941,1256,1060/29.973
occluders=[(485,705,555,1288),(1285,605,1403,1288),(1203,1185,1313,1290)]
# Photo's soffit shadow and carved relief sit on different depth planes; exclude
# them rather than duplicating geometry with a shifted dark photographic band.
projection_exclusions=[(0,0,1884,625),(390,535,1490,625),(615,440,694,542),(1189,440,1267,542)]
# Geometric frames remain independent and never receive photo mullions.
for cx in [541,762,941,1120,1341]:
 projection_exclusions.append((cx-34,450,cx+34,543))
for cx in [710,814,889,993,1068,1172]:
 projection_exclusions.append((cx-13,450,cx+13,543))
model=bpy.data.collections['MODEL_Bund18_Chartered_Bank']
counts={'texturedPolygons':0,'originalPolygons':0,'rejectedOccluded':0,'texturedTriangleCount':0,'photographicGlassPolygons':0}

# Conservative polygon/rectangle test. Over-omission is preferable to baking a
# traffic light, flower box or electrical cabinet onto the building.
def overlap(a,b):return a[0]<=b[2] and a[2]>=b[0] and a[1]<=b[3] and a[3]>=b[1]
def local(co):
 p=Vector((co.x,co.y))-C
 return p.dot(T),p.dot(N),co.z

def projected(co):
 x,y,z=local(co)
 return centre_x+x*px_per_m,ground_y-z*px_per_m

for obj in model.objects:
 if obj.type!='MESH':continue
 mesh=obj.data
 original=list(mesh.materials)
 mapping={}
 for i,mat in enumerate(original):
  new=mat.copy();new.name='PhotoFacade_'+mat.name
  bs=new.node_tree.nodes.get('Principled BSDF')
  tex=new.node_tree.nodes.new('ShaderNodeTexImage');tex.name='Unmodified attributed photograph';tex.image=image;tex.extension='EXTEND';tex.interpolation='Linear'
  new.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
  bs.inputs['Metallic'].default_value=0.0
  # Source contains cloudy-day shading; avoid shiny stone over that appearance.
  if 'glass' not in mat.name.lower():bs.inputs['Roughness'].default_value=.82
  new['license']='CC-BY-SA-4.0';new['photographer']='ScareCriterion12';new['image_sha256']=original_sha
  mesh.materials.append(new);mapping[i]=len(mesh.materials)-1
 uv=mesh.uv_layers.new(name='PhotoReferenceUV')
 for face in mesh.polygons:
  positions=[mesh.vertices[mesh.loops[i].vertex_index].co for i in face.loop_indices]
  local_coords=[local(p) for p in positions]
  pixels=[projected(p) for p in positions]
  for loop_index,p in zip(face.loop_indices,pixels):uv.data[loop_index].uv=(p[0]/width,1-p[1]/height)
  normal=face.normal
  front_facing=-(normal.x*N.x+normal.y*N.y)>.35 and abs(normal.z)<.65
  xs,ys,zs=zip(*local_coords)
  eligible=original[face.material_index].name.startswith('Limestone_') and front_facing and max(ys)<1.5 and min(ys)>-1.35 and max(map(abs,xs))<14.75 and min(zs)>1.72 and max(zs)<25.4
  bb=(min(p[0] for p in pixels),min(p[1] for p in pixels),max(p[0] for p in pixels),max(p[1] for p in pixels))
  if eligible and any(overlap(bb,o) for o in occluders+projection_exclusions):
   eligible=False;counts['rejectedOccluded']+=1
  # The six central panes have their own four-corner correspondence. A
  # facade-wide projection incorrectly puts the recessed frames in two places.
  glass_match=None
  if 'glass' in original[face.material_index].name.lower() and front_facing and min(ys)>1.14 and max(ys)<1.22:
   for cx,px0,px1 in [(-5.05,720,813),(0,893,990),(5.05,1070,1167)]:
    for cz,h,py0,py1 in [(14.97,2.60,666,746),(9.64,3.94,835,970)]:
     x0,x1=cx-(3.05-.08)/2,cx+(3.05-.08)/2
     z0,z1=(cz-(h-.08)/2)*1.037,(cz+(h-.08)/2)*1.037
     if min(xs)>=x0-.003 and max(xs)<=x1+.003 and min(zs)>=z0-.003 and max(zs)<=z1+.003:
      glass_match=(x0,x1,z0,z1,px0,px1,py0,py1)
   if glass_match:
    x0,x1,z0,z1,px0,px1,py0,py1=glass_match
    for li,co in zip(face.loop_indices,local_coords):
     px=px0+(co[0]-x0)/(x1-x0)*(px1-px0)
     py=py1-(co[2]-z0)/(z1-z0)*(py1-py0)
     uv.data[li].uv=(px/width,1-py/height)
    eligible=True;counts['photographicGlassPolygons']+=1
  if eligible:
   face.material_index=mapping[face.material_index];counts['texturedPolygons']+=1;counts['texturedTriangleCount']+=len(face.vertices)-2
  else:counts['originalPolygons']+=1
 obj['detail']='Preserved 3-D wall openings, columns, mouldings and side/back; selective photographic appearance'

scene=bpy.context.scene
scene['photo_source']='https://commons.wikimedia.org/wiki/File:上海外滩麦加利银行旧址2021.jpg';scene['photo_license_url']='https://creativecommons.org/licenses/by-sa/4.0/';scene['photo_author']='ScareCriterion12';scene['photo_license']='CC-BY-SA-4.0';scene['photo_sha256']=original_sha
scene['limitations']='Single view photographed 2021; front dimensions estimated; side/back inferred; selected obscured front faces retain procedural materials.'
bpy.ops.object.select_all(action='DESELECT')
for obj in model.objects:obj.select_set(True)
bpy.context.view_layer.objects.active=next(iter(model.objects))
bpy.ops.export_scene.gltf(filepath=str(OUT/'bund18-photo.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_materials='EXPORT',export_copyright='Facade photograph: ScareCriterion12, https://commons.wikimedia.org/wiki/File:上海外滩麦加利银行旧址2021.jpg; photograph and photographic model derivative: CC BY-SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/. Original modeling source: MIT; OSM footprint: © OpenStreetMap contributors, ODbL 1.0.')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'bund18-photo.blend'))
# Low-cost off-screen geometry previews; no browser session is opened.
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.12
scene.render.resolution_x=1000;scene.render.resolution_y=1100
for name,cam in ([('front',bpy.data.objects['Camera_front_elevation']),('oblique',bpy.data.objects['Camera_three_quarter'])] if args.render else []):
 scene.camera=cam;scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
counts.update({'photo_sha256':original_sha,'photo_bytes':PHOTO.stat().st_size,'photo_uv_basis':[width,height],'projection':{'centre_x':centre_x,'ground_y':ground_y,'pixels_per_metre':px_per_m},'occluder_rectangles':occluders,'projection_exclusions':projection_exclusions,'scope':'Selected lower front limestone wall faces and six independently mapped central glass panes; attic, frames, columns, cornices, relief and uncertain depth transitions retain geometric materials','glb_bytes':(OUT/'bund18-photo.glb').stat().st_size,'blend_bytes':(OUT/'bund18-photo.blend').stat().st_size,'license':'CC-BY-SA-4.0','photographer':'ScareCriterion12'})
(OUT/'validation.json').write_text(json.dumps(counts,indent=2));print(json.dumps(counts))
