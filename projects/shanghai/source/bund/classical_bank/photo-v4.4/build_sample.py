#!/usr/bin/env python3
"""Blender staging-only Bund12 photographic six-window sample, original JPEG unchanged."""
import bpy,json,math,hashlib,struct,sys,argparse,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--project',required=True);ap.add_argument('--baseline-native');ap.add_argument('--baseline-raw');ap.add_argument('--photo');ap.add_argument('--render',action='store_true');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else[])
ROOT=Path(args.project).resolve();BASE=json.loads((P/'baseline-source.json').read_text());native_path=Path(args.baseline_native) if args.baseline_native else ROOT/'assets/native/bund/bund12.blend';raw_path=Path(args.baseline_raw) if args.baseline_raw else ROOT/'assets/models/bund/bund12.glb';photo_path=Path(args.photo) if args.photo else (ROOT/'assets/references/bund/hsbc-20250501-original.jpg' if (ROOT/'assets/references/bund/hsbc-20250501-original.jpg').exists() else P/'hsbc-20250501-original.jpg');G=json.loads((ROOT/'source/bund/classical_bank/geometry-input.json').read_text())['bund12'];C=json.loads((P/'calibration.json').read_text()); U=G['world_basis_u'];V=G['world_basis_v'];FC=G['front_center']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def world(p):
 x,y,z=p;x+=FC[0];y+=FC[1];return(U[0]*x+V[0]*y,U[1]*x+V[1]*y,z)
def local(p):return(p[0]*U[0]+p[1]*U[1]-FC[0],p[0]*V[0]+p[1]*V[1]-FC[1],p[2])
def homo(q):
 A=[];b=[]
 for (s,t),(x,y) in zip([(0,0),(1,0),(1,1),(0,1)],q):A.extend([[s,t,1,0,0,0,-s*x,-t*x],[0,0,0,s,t,1,-s*y,-t*y]]);b.extend([x,y])
 return np.r_[np.linalg.solve(A,b),1].reshape(3,3)
def hp(H,s,t):q=H@np.array([s,t,1]);return(q[0]/q[2],q[1]/q[2])
def mat(name,col,rough=.7,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*col,1);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*col,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal;return m
assert sha(native_path)==BASE['assets']['native']['sha256'], 'Native baseline differs; download pinned baseline in baseline-source.json and use --baseline-native'
assert sha(raw_path)==BASE['assets']['raw']['sha256'], 'Raw baseline differs; download pinned baseline in baseline-source.json and use --baseline-raw'
assert sha(photo_path)==json.loads((P/'photo-source.json').read_text())['sha256'], 'Original photograph bytes do not match frozen source'
bpy.ops.wm.open_mainfile(filepath=str(native_path));O=bpy.data.objects['HSBC Bund 12'];M=O.data
verts=[tuple(v.co) for v in M.vertices]; loc=np.array([local(v) for v in verts]); faces=[];mi=[];smooth=[];removed=[];ranges=[]
for w in C['windows']:
 x=12.7+(w['bay']+.5)*(G['front_width']-25.4)/14
 z0,z1,width=(19.6,22.7,1.95) if w['level']==3 else(13.8,17.9,2.2)
 w.update(center_x=x,z0=z0,z1=z1,width=width)
 ranges.append((w,x-width/2,x+width/2,z0,z1))
for p in M.polygons:
 vs=list(p.vertices);v=loc[vs];hit=None
 if p.material_index in (3,4):
  for w,x0,x1,z0,z1 in ranges:
   if np.all(v[:,0]>=x0-1e-4) and np.all(v[:,0]<=x1+1e-4) and np.all(v[:,2]>=z0-1e-4) and np.all(v[:,2]<=z1+1e-4) and np.all(v[:,1]>.2) and np.all(v[:,1]<.65):hit=w['id'];break
 if hit:removed.append({'face':p.index,'window':hit,'material_index':p.material_index})
 else:faces.append(vs);mi.append(p.material_index);smooth.append(p.use_smooth)
assert len(removed)==6*56,(len(removed),'Unexpected original face selection; fail closed')
origmats=list(M.materials);new=bpy.data.meshes.new('HSBC unchanged structure with six glazing/frame replacements');new.from_pydata(verts,[],faces)
for m in origmats:new.materials.append(m)
for p,i,s in zip(new.polygons,mi,smooth):p.material_index=i;p.use_smooth=s
O.data=new
im=bpy.data.images.load(str(photo_path),check_existing=True);im.name='Bund12 original CC0 Suicasmo 2025-05-01';im.pack()
photo=mat('PhotoFacade_Bund12_Glazing_OriginalPhoto',(1,1,1),.76,0);bs=photo.node_tree.nodes.get('Principled BSDF');bs.inputs['Specular IOR Level'].default_value=.10;tex=photo.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;tex.interpolation='Linear';tex.extension='EXTEND';photo.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
frame=mat('PhotoFacade_Bund12_Measured_Casement_Bronze',(.070,.078,.061),.48,.22)
side=mat('PhotoFacade_Bund12_Glass_Edge',(.075,.14,.16),.3,.1)
FV=[];FF=[];PV=[];PF=[];PUV=[];PM=[];panes=[]
def box(x,y,z,w,d,h):
 o=len(FV);FV.extend([world((x+sx*w/2,y+sy*d/2,z+sz*h/2)) for sx,sy,sz in[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]])
 FF.extend([tuple(o+i for i in f) for f in[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]])
def pane(w,s0,s1,t0,t1,quad):
 x=w['center_x'];width=w['width'];z0=w['z0'];z1=w['z1'];H=homo(quad);N=6;o=len(PV)
 for j in range(N+1):
  for i in range(N+1):
   s=i/N;t=j/N;px,py=hp(H,s,t);PV.append(world((x-width/2+(s0+(s1-s0)*s)*width,.57,z1-(t0+(t1-t0)*t)*(z1-z0))));PUV.append((px/5184,1-py/3456))
 for j in range(N):
  for i in range(N):a=o+j*(N+1)+i;PF.append((a,a+N+1,a+N+2,a+1));PM.append(0)
 # Solid 45 mm pane edge and rear, using the same true inset volume as baseline glazing.
 corners=[o,o+N,o+N*(N+1)+N,o+N*(N+1)];back=[]
 for k in corners:
  p=local(PV[k]);back.append(len(PV));PV.append(world((p[0],.615,p[2])));PUV.append(PUV[k])
 PF.append(tuple(back));PM.append(1)
 for a in range(4):b=(a+1)%4;PF.append((corners[a],corners[b],back[b],back[a]));PM.append(1)
 panes.append({'window':w['id'],'physical_st_bounds':[s0,s1,t0,t1],'source_quad_original_pixels':quad,'source_sample_contains_primary_photo_frames':False})
for w in C['windows']:
 x,z0,z1,width=w['center_x'],w['z0'],w['z1'],w['width'];h=z1-z0;outer=.105;central=.12;hbar=.11;half_o=outer/width;half_c=central/(2*width);H=homo(w['quad_original_pixels']);cc=w['measured_center_s_of_t'];hb=w['measured_main_bars_t_of_s']; physical_bars=[.34] if w['level']==3 else[.285,.69]
 box(x-width/2+outer/2,.39,(z0+z1)/2,outer,.22,h);box(x+width/2-outer/2,.39,(z0+z1)/2,outer,.22,h)
 box(x,.39,z0+outer/2,width,.22,outer);box(x,.39,z1-outer/2,width,.22,outer);box(x,.37,(z0+z1)/2,central,.20,h-2*outer)
 for t in physical_bars:box(x,.35,z1-t*h,width-2*outer,.22,hbar)
 # The main bars are geometry. Sample only the visible glass on each side of them.
 # Fine grille and curtain detail stays in the exact original photograph, with no fabricated interior.
 for col,(sa,sb) in enumerate([(half_o,.5-half_c),(.5+half_c,1-half_o)]):
  ts=[outer/h]+[t for t in physical_bars]+[1-outer/h]
  for row in range(len(ts)-1):
   ta=ts[row]+(hbar/(2*h) if row else 0);tb=ts[row+1]-(hbar/(2*h) if row<len(ts)-2 else 0)
   def sample_st(side_index,row_boundary,is_bottom):
    # Independent photo-frame line intersections, in this window's calibrated source quad.
    # Broad frame exclusion margins are 3.5% width and 2.2% height, larger than measured frame half-widths.
    tguess=([.055]+[b[1]+b[0]*.5 for b in hb]+[.975])[row_boundary]
    if row_boundary not in(0,len(hb)+1):tguess+=(-.024 if is_bottom else .024)
    c=cc[0]*tguess+cc[1]
    if col==0:s=(.064-.035*tguess) if side_index==0 else c-.039
    else:s=c+.039 if side_index==0 else(.936-.025*tguess)
    if row_boundary not in(0,len(hb)+1):
     b=hb[row_boundary-1];t=b[0]*s+b[1]+(-.024 if is_bottom else .024)
    else:t=tguess
    return hp(H,s,t)
   quad=[sample_st(0,row,False),sample_st(1,row,False),sample_st(1,row+1,True),sample_st(0,row+1,True)]
   pane(w,sa,sb,ta,tb,quad)
def obj(name,vs,fs,mats,uvs=None,indices=None):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
 for m in mats:me.materials.append(m)
 if indices:
  for p,i in zip(me.polygons,indices):p.material_index=i
 if uvs:
  uv=me.uv_layers.new(name='Calibrated original photo UV')
  for p in me.polygons:
   for li in p.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
 return ob
F=obj('Bund12 six observed main casement frames',FV,FF,[frame]);PH=obj('Bund12 thirty independently mapped recessed glass panes',PV,PF,[photo,side],PUV,PM)
for ob in(O,F,PH):ob['sample_scope']='Six unobstructed windows, north wing bays 2–4, levels 2–3; all baseline structural faces preserved.'
PH['photo_author']='Suicasmo';PH['photo_license']='CC0-1.0';PH['photo_date']='2025-05-01';PH['photo_sha256']=sha(photo_path);PH['fine_grille_depth']='Photographic only; not survey-derived.'
models=[O,F,PH]
def export(path):
 bpy.ops.object.select_all(action='DESELECT')
 for ob in models:ob.select_set(True)
 bpy.context.view_layer.objects.active=O;bpy.ops.export_scene.gltf(filepath=str(P/path),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_image_format='AUTO',export_extras=True)
export('bund12-photo-raw.glb')
# Same corrected geometry, physically colored ordinary glazing; no image or texture in far-distance source.
no_photo=mat('Bund12_Distant_Geometric_Glazing',(.075,.14,.16),.3,.1);PH.data.materials[0]=no_photo;export('bund12-geometry-lod-source.glb');PH.data.materials[0]=photo
# Immutable face-level proof, in addition to the untouched source asset hashes.
assert all(tuple(new.vertices[i].co)==verts[i] for i in range(len(verts)))
assert all(list(p.vertices)==f and p.material_index==i for p,f,i in zip(new.polygons,faces,mi))
counts={w['id']:sum(r['window']==w['id'] for r in removed) for w in C['windows']}
report={'schema_version':'bund12-photo-six-window-validation-v1','source_native_sha256':sha(native_path),'source_raw_sha256':sha(raw_path),'original_photo_sha256':sha(photo_path),'source_baseline_vertices':len(verts),'source_baseline_faces':len(M.polygons),'structural_faces_removed':0,'selected_original_glass_and_frame_faces_removed':len(removed),'removed_per_window':counts,'all_nonselected_face_coordinates_indices_materials_identical':True,'all_source_vertices_identical':True,'preserved_original_structure_faces':len(faces),'new_main_frame_faces':len(FF),'new_glazing_faces':len(PF),'photo_glazing_panes':len(panes),'photo_texture_count':1,'mapped_window_count':6,'photographic_fine_grilles_are_not_3D':True,'browser_validation_performed':False,'limits':['Existing source apertures and whole-building dimensions remain photo-estimated; not a survey.','Only six windows receive photo samples; other facade surfaces remain baseline geometry/materials.','Curtain and reflection appearances are fixed to the May 1, 2025 photograph; no fabricated interior.','Fine decorative grille details are photographic; only the observed primary casement and transom bars are explicit solid geometry.','Stone photo mapping is deferred because existing stone joints would require separate source-to-geometry alignment.']}
(P/'panes.json').write_text(json.dumps(panes,ensure_ascii=False,indent=2));(P/'model-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=False;scene.render.resolution_x=1400;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
def camera(name,position,target,ortho):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=world(position);o.rotation_euler=(Vector(world(target))-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=ortho;return o
cam=camera('Six-window front review',(23.05,-35,18.3),(23.05,0,18.3),13.0);oblique=camera('Six-window oblique review',(33,-24,20.5),(23.05,0,18.3),14.0)
scene.camera=cam;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(P/'bund12-photo.blend'),compress=True)
if args.render:
 for name,c in [('six-window-front',cam),('six-window-oblique',oblique)]:scene.camera=c;scene.render.filepath=str(P/(name+'.png'));bpy.ops.render.render(write_still=True)
print('BUND12_SAMPLE_READY',json.dumps(report))
