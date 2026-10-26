"""Open-perimeter facade modules and glTF serialization; inferred detail only."""
import math,json,struct
from pathlib import Path
import numpy as np
import mapbox_earcut
from shapely.geometry import Polygon,Point
from shapely import constrained_delaunay_triangles,get_coordinates
materials=[('Inferred neutral plaster',(.60,.58,.54),.88,0),('Inferred window reveals',(.42,.41,.39),.86,0),('Inferred dark glazing',(.055,.085,.10),.26,.08),('Inferred painted frames',(.24,.26,.25),.7,0),('Retained roof',(.35,.38,.37),.9,0),('Inferred inset doors',(.14,.12,.10),.86,0)]
class Batch:
 def __init__(self):self.pos=[];self.norm=[];self.idx=[]
 def face(self,pts,normal):
  pts=[tuple(float(x) for x in p) for p in pts];off=len(self.pos)
  u=np.subtract(pts[1],pts[0]);v=np.subtract(pts[2],pts[0])
  if np.dot(np.cross(u,v),normal)<0:pts=pts[:1]+list(reversed(pts[1:]))
  self.pos.extend(pts);self.norm.extend([normal]*len(pts))
  for j in range(1,len(pts)-1):self.idx.extend([off,off+j,off+j+1])
 def triangles(self,pts,indices,normal):
  # Emit one indexed face batch. Preserve the old face-by-face first-use order
  # so subsequent exact welding produces identical serialized geometry.
  ii=np.asarray(indices,dtype='i8').reshape(-1,3).copy()
  if not len(ii):return
  ps=np.asarray(pts,dtype='f8');tt=ps[ii]
  flip=(np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0])@np.asarray(normal))<0
  ii[flip]=ii[flip][:,[0,2,1]]
  flat=ii.reshape(-1);used,first=np.unique(flat,return_index=True);used=used[np.argsort(first)]
  remap=np.empty(len(ps),dtype='i8');remap[used]=np.arange(len(used));off=len(self.pos)
  self.pos.extend(tuple(map(float,p)) for p in ps[used]);self.norm.extend([normal]*len(used));self.idx.extend((remap[flat]+off).tolist())
 def tri_count(self):return len(self.idx)//3

FAMILIES={
 'house':{'opening':(.24,.76,.28,.80),'bay':2.8,'frame':.026,'transom':.65},
 'apartment':{'opening':(.18,.82,.24,.84),'bay':3.2,'frame':.018,'transom':None},
 'industrial':{'opening':(.10,.90,.48,.90),'bay':5.5,'frame':.016,'transom':.55},
 'office':{'opening':(.13,.87,.17,.86),'bay':3.3,'frame':.012,'transom':.72},
 'unknown':{'opening':(.24,.76,.25,.80),'bay':3.4,'frame':.020,'transom':None}}

def module(kind,family):
 bs=[Batch() for _ in materials];structural=[Batch() for _ in materials];profile=FAMILIES[family];x0,x1,wy0,wy1=profile['opening'];xs=[0,x0,x1,1];ys=sorted(set([0,wy0,wy1,.82,1]))
 if kind=='plain':
  boundary=[(x,0,0) for x in xs]+[(1,y,0) for y in ys[1:]]+[(x,1,0) for x in xs[-2::-1]]+[(0,y,0) for y in ys[-2:0:-1]]
  for pa,pb in zip(boundary,boundary[1:]+boundary[:1]):bs[0].face([pa,pb,(.5,.5,0)],(0,0,-1))
  structural[0],bs[0]=bs[0],structural[0]
  return bs,structural
 y0,y1=(0,.82) if kind=='door' else (wy0,wy1);depth=.28 if kind=='door' else .22
 for i in range(3):
  for j in range(len(ys)-1):
   if xs[i]>=x0 and xs[i+1]<=x1 and ys[j]>=y0-1e-9 and ys[j+1]<=y1+1e-9:continue
   bs[0].face([(xs[i],ys[j],0),(xs[i+1],ys[j],0),(xs[i+1],ys[j+1],0),(xs[i],ys[j+1],0)],(0,0,-1))
 bs[1].face([(x0,y0,0),(x0,y1,0),(x0,y1,depth),(x0,y0,depth)],(1,0,0));bs[1].face([(x1,y0,0),(x1,y1,0),(x1,y1,depth),(x1,y0,depth)],(-1,0,0))
 if y0>0:bs[1].face([(x0,y0,0),(x1,y0,0),(x1,y0,depth),(x0,y0,depth)],(0,1,0))
 bs[1].face([(x0,y1,0),(x1,y1,0),(x1,y1,depth),(x0,y1,depth)],(0,-1,0))
 structural[0],bs[0]=bs[0],structural[0]
 structural[1],bs[1]=bs[1],structural[1]
 panel=2 if kind=='window' or family=='office' else 3 if family=='industrial' else 5
 bs[panel].face([(x0,y0,depth),(x1,y0,depth),(x1,y1,depth),(x0,y1,depth)],(0,0,-1))
 # One continuous thick frame ring, including front/back and real returns.
 t=profile['frame'];front=depth-.055;back=depth-.008
 outer=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)];inner=[(x0+t,y0+t),(x1-t,y0+t),(x1-t,y1-t),(x0+t,y1-t)];normals=[(0,-1,0),(1,0,0),(0,1,0),(-1,0,0)]
 for i in range(4):
  j=(i+1)%4;oo,op=outer[i],outer[j];ii,ip=inner[i],inner[j]
  for z,n in [(front,(0,0,-1)),(back,(0,0,1))]:bs[3].face([(*oo,z),(*op,z),(*ip,z),(*ii,z)],n)
  bs[3].face([(*oo,front),(*op,front),(*op,back),(*oo,back)],normals[i]);bs[3].face([(*ii,front),(*ip,front),(*ip,back),(*ii,back)],tuple(-x for x in normals[i]))
 def bar(u0,u1,v0,v1):
  bs[3].face([(u0,v0,front),(u1,v0,front),(u1,v1,front),(u0,v1,front)],(0,0,-1))
  bs[3].face([(u0,v0,back),(u1,v0,back),(u1,v1,back),(u0,v1,back)],(0,0,1))
  # Ends meeting frame/transom remain open: no opposing internal end faces.
  if u1-u0<v1-v0:
   for u,n in [(u0,(-1,0,0)),(u1,(1,0,0))]:bs[3].face([(u,v0,front),(u,v1,front),(u,v1,back),(u,v0,back)],n)
  else:
   for v,n in [(v0,(0,-1,0)),(v1,(0,1,0))]:bs[3].face([(u0,v,front),(u1,v,front),(u1,v,back),(u0,v,back)],n)
 if kind=='window':
  mid=(x0+x1)/2;w=.009;bar(mid-w,mid+w,y0+t,y1-t)
  if profile['transom'] is not None:
   y=y0+(y1-y0)*profile['transom'];bar(x0+t,mid-w,y-.009,y+.009);bar(mid+w,x1-t,y-.009,y+.009)
  # Actual projecting sill with exposed top/front/underside/end returns; rear
  # attachment face omitted rather than coplanar against the structural wall.
  a,b=x0-.025,x1+.025;lo,hi=y0-.025,y0;z0=-.065;z1=0
  bs[1].face([(a,lo,z0),(b,lo,z0),(b,hi,z0),(a,hi,z0)],(0,0,-1));bs[1].face([(a,hi,z0),(b,hi,z0),(b,hi,z1),(a,hi,z1)],(0,1,0));bs[1].face([(a,lo,z0),(b,lo,z0),(b,lo,z1),(a,lo,z1)],(0,-1,0))
  for u,n in [(a,(-1,0,0)),(b,(1,0,0))]:bs[1].face([(u,lo,z0),(u,hi,z0),(u,hi,z1),(u,lo,z1)],n)
 elif family=='house':
  # Door's inset upper light and two raised panel outlines, all inferred.
  z=depth-.007;u0,u1=x0+t*2,x1-t*2;v0,v1=y0+(y1-y0)*.58,y1-t*2
  bs[2].face([(u0,v0,z),(u1,v0,z),(u1,v1,z),(u0,v1,z)],(0,0,-1))
 elif family=='industrial':
  for j in range(1,8):
   y=y0+(y1-y0)*j/8;bar(x0+t,x1-t,y-.004,y+.004)
 return bs,structural

def surface(rings,y,normal,batch):
 pts=[p for ring in rings for p in ring];ends=np.cumsum([len(r) for r in rings],dtype=np.uint32);idx=mapbox_earcut.triangulate_float64(np.array(pts),ends)
 batch.triangles([(x,y,z) for x,z in pts],idx,normal)

def side(a,b,y0,y1,batch):
 dx,dz=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dz);batch.face([(a[0],y0,a[1]),(a[0],y1,a[1]),(b[0],y1,b[1]),(b[0],y0,b[1])],(dz/L,0,-dx/L))
_MODULE_PARTS={k+'_'+fam:module(k,fam) for fam in FAMILIES for k in ['plain','window','door']}
MODULES={k:v[0] for k,v in _MODULE_PARTS.items()}
STRUCTURAL_MODULES={k:v[1] for k,v in _MODULE_PARTS.items()}
DETAIL_TRIANGLES={k:sum(b.tri_count() for b in v) for k,v in MODULES.items()}
MODULE_TRIANGLES={k:DETAIL_TRIANGLES[k]+sum(b.tri_count() for b in STRUCTURAL_MODULES[k]) for k in MODULES}

def clip_above(points,y):
 out=[]
 for a,b in zip(points,points[1:]+points[:1]):
  ia=a[1]>=y-1e-8;ib=b[1]>=y-1e-8
  if ia:out.append(a)
  if ia!=ib:
   t=(y-a[1])/(b[1]-a[1]);out.append(tuple(a[k]+t*(b[k]-a[k]) for k in range(3)))
 return out

def mesh_to_batch(mesh,batch,minimum_y=None):
 for j in range(0,len(mesh.indices),3):
  ids=mesh.indices[j:j+3];pts=[mesh.positions[i] for i in ids];normal=mesh.normals[ids[0]]
  if minimum_y is not None:pts=clip_above(pts,minimum_y)
  if len(pts)<3:continue
  if np.linalg.norm(np.cross(np.subtract(pts[1],pts[0]),np.subtract(pts[2],pts[0])))<1e-9:continue
  batch.face(pts,normal)

def feature_estimate(f):
 height=max(0,f['eave']-f['base']);floors=max(1,round(height/3.2));total=0;vertices=0
 for rings in f['rings']:
  for ring in rings:
   vertices+=len(ring)
   total+=sum(max(1,math.floor(math.dist(a,b)/FAMILIES[f['family']]['bay'])) for a,b in zip(ring,ring[1:]+ring[:1]))*floors*MODULE_TRIANGLES['window_'+f['family']]
 return total+vertices*120+64

def feature_near(f,neighbors,tree,roof_shell_function):
 instances={k:[] for k in MODULES};unique=[Batch() for _ in materials]
 base,H,top=f['base'],f['height'],f['eave'];height=max(0,top-base)
 floors=max(1,int(f['properties'].get('num_floors') or round(height/3.2)))
 if f.get('residual') or not 2.2<=height/floors<=5.5:floors=max(1,round(height/3.2))
 if f['family']=='industrial' and not f['properties'].get('num_floors'):floors=1
 floorheight=height/floors;edges=[]
 for ci,rings in enumerate(f['rings']):
  localg=Polygon(rings[0],rings[1:])
  if f.get('roof'):
   roof,walls=roof_shell_function(rings,f)
   mesh_to_batch(roof,unique[4]);mesh_to_batch(walls,unique[0],top)
  else:surface(rings,H,(0,1,0),unique[4]);surface(rings,base,(0,-1,0),unique[0])
  ns=[neighbors[int(i)] for i in tree.query(localg.buffer(.4)) if neighbors[int(i)]['key']!=f['key']]
  for ri,ring in enumerate(rings):
   for ei,(pa,pb) in enumerate(zip(ring,ring[1:]+ring[:1])):
    dx,dz=pb[0]-pa[0],pb[1]-pa[1];L=math.hypot(dx,dz)
    if L<.001:continue
    T=np.array([dx/L,dz/L]);N=np.array([dz/L,-dx/L]);point=Point(np.array(pa)+T*(L/2)+N*.20)
    exposed=not any(n['local_geometry'].covers(point) and n['height']>base+1 for n in ns)
    edges.append((ci,ri,ei,pa,pb,L,T,N,ns,exposed))
  if not f.get('roof'):
   outer=localg.buffer(.07,join_style=2);band=outer.difference(localg)
   for part in ([band] if band.geom_type=='Polygon' else getattr(band,'geoms',[])):
    if part.geom_type!='Polygon' or part.is_empty:continue
    rr=[list(part.exterior.coords)[:-1]]+[list(i.coords)[:-1] for i in part.interiors]
    surface(rr,H,(0,1,0),unique[0]);surface(rr,max(base,H-.13),(0,-1,0),unique[0])
   for op in ([outer] if outer.geom_type=='Polygon' else outer.geoms):
    for ri,rr in enumerate([op.exterior,*op.interiors]):
     ring=list(rr.coords)[:-1];area=sum(x[0]*y[1]-y[0]*x[1] for x,y in zip(ring,ring[1:]+ring[:1]))
     if (area>0)!=(ri==0):ring.reverse()
     for aa,bb in zip(ring,ring[1:]+ring[:1]):side(aa,bb,max(base,H-.13),H,unique[0])
 if height>.01:
  door_edge=max((e for e in edges if e[1]==0 and e[9] and e[5]>1.7),key=lambda e:e[5],default=None) if base<.3 and f['properties']['source_layer']=='building' else None
  if base<.3:
   door_cut=None
   if door_edge is not None:
    ci,ri,ei,pa,pb,L,T,N,ns,exposed=door_edge;bay=L/max(1,math.floor(L/FAMILIES[f['family']]['bay']));col=max(1,math.floor(L/FAMILIES[f['family']]['bay']))//2;x0,x1,_,_=FAMILIES[f['family']]['opening'];aa=np.array(pa)+T*(col*bay+x0*bay);bb=np.array(pa)+T*(col*bay+x1*bay)
    door_cut=Polygon([tuple(aa-N*.1),tuple(bb-N*.1),tuple(bb+N*.1),tuple(aa+N*.1)])
   add_base_course(f['local_geometry'],base,min(top,base+.28),unique[1],door_cut)
  for ci,ri,ei,pa,pb,L,T,N,ns,exposed in edges:
   bays=max(1,math.floor(L/FAMILIES[f['family']]['bay']));bay=L/bays;theta=-math.atan2(T[1],T[0]);q=[0,math.sin(theta/2),0,math.cos(theta/2)]
   openings=[];door_bounds=None
   # XZ coverage does not depend on floor height. Cache the exact same point
   # test once per column, retaining row/column order and scalar height tests.
   covered_by=[]
   for col in range(bays):
    u0=col*bay;point=Point(np.array(pa)+T*(u0+bay/2)+N*.2)
    covered_by.append([n for n in ns if n['local_geometry'].covers(point)])
   for row in range(floors):
    yy=base+row*floorheight
    for col in range(bays):
     u0=col*bay
     blocked=any(n['base']<yy+floorheight*.65<n['height'] for n in covered_by[col])
     kind='plain' if bay<1.45 or floorheight<2 or blocked else 'window'
     if door_edge is not None and (ci,ri,ei)==door_edge[:3] and row==0 and col==bays//2 and not blocked:kind='door'
     module_key=kind+'_'+f['family']
     if kind!='plain':
      x0,x1,wy0,wy1=FAMILIES[f['family']]['opening'];wy0,wy1=(0,.82) if kind=='door' else (wy0,wy1)
      left,right=(col+x0)*bay,(col+x1)*bay;low,high=base+(row+wy0)*floorheight,base+(row+wy1)*floorheight
      if kind=='door':door_bounds=(left,right,high)
      else:openings.append([(left,low),(right,low),(right,high),(left,high)])
     # Structural surfaces use one canonical world-coordinate calculation for
     # every boundary, not independent instance TRS multiply/add sequences.
     # In particular (col+1) and next col+0 are the same integer expression;
     # original footprint endpoints close every facade corner bit-exactly.
     for mat,(dest,src) in enumerate(zip(unique,STRUCTURAL_MODULES[module_key])):
      if mat==0:continue # one conforming perforated wall skin per full edge below
      off=len(dest.pos)
      for x,y,z in src.pos:
       column=col+x;row_y=row+y
       if column==0:px,pz=pa
       elif column==bays:px,pz=pb
       else:px,pz=pa[0]+T[0]*(column*bay),pa[1]+T[1]*(column*bay)
       py=base if row_y==0 else top if row_y==floors else base+row_y*floorheight
       dest.pos.append((px-N[0]*z,py,pz-N[1]*z))
      for nx,ny,nz in src.norm:dest.norm.append((T[0]*nx-N[0]*nz,ny,T[1]*nx-N[1]*nz))
      dest.idx.extend(i+off for i in src.idx)
     if DETAIL_TRIANGLES[module_key]:instances[module_key].append(([pa[0]+T[0]*u0,yy,pa[1]+T[1]*u0],q,[bay,floorheight,1],f['local_id']))
   # Triangulate the whole facade with genuine holes, rather than many bay
   # quads. Every opening boundary is exactly the jamb boundary; no T-junction
   # or independent instance arithmetic remains on a structural wall.
   outline=[(0,base)]
   if door_bounds:
    left,right,high=door_bounds;outline.extend([(left,base),(left,high),(right,high),(right,base)])
   outline.extend([(L,base),(L,top),(0,top)]);rings2=[outline]+openings
   points=[p for ring in rings2 for p in ring];ends=np.cumsum([len(ring) for ring in rings2],dtype=np.uint32)
   # Earcut may omit collinear constraint vertices on aligned window rows,
   # leaving long-edge/short-edge T junctions. GEOS constrained Delaunay keeps
   # every opening boundary and produces a strictly conforming triangle mesh.
   triangulated=constrained_delaunay_triangles(Polygon(outline,openings))
   coordinates=get_coordinates(triangulated).reshape(-1,4,2)[:,:3]
   point_ids={tuple(p):i for i,p in enumerate(points)}
   ix=np.asarray([point_ids[tuple(p)] for p in coordinates.reshape(-1,2)],dtype='u4')
   wall=[]
   for u,y in points:
    if u==0:px,pz=pa
    elif u==L:px,pz=pb
    else:px,pz=pa[0]+T[0]*u,pa[1]+T[1]*u
    wall.append((px,y,pz))
   unique[0].triangles(wall,ix,(N[0],0,N[1]))
 return instances,unique

def combine(batch_sets):
 result=[Batch() for _ in materials]
 for batches in batch_sets:
  for dest,src in zip(result,batches):
   n=len(dest.pos);dest.pos.extend(src.pos);dest.norm.extend(src.norm);dest.idx.extend(i+n for i in src.idx)
 return result

def weld(batch):
 """Share exact serialized vertices; preserve hard-edge normals, never snap.
 Vectorized deduplication retains original first-use order and float32 bits.
 """
 if not batch.pos:return
 ps=np.asarray(batch.pos,dtype='<f4');ns=np.asarray(batch.norm,dtype='<f4');keys=np.concatenate((ps,ns),axis=1)
 _,first,inverse=np.unique(keys,axis=0,return_index=True,return_inverse=True)
 order=np.argsort(first);remap=np.empty(len(order),dtype='i8');remap[order]=np.arange(len(order));keep=first[order]
 batch.pos=ps[keep].tolist();batch.norm=ns[keep].tolist();batch.idx=remap[inverse[np.asarray(batch.idx,dtype='i8')]].tolist()

class Encoder:
 def __init__(self):self.buf=bytearray();self.views=[];self.accessors=[];self.meshes=[];self.nodes=[]
 def acc(self,values,typ,kind,target=None):
  arr=np.asarray(values,dtype={5126:'<f4',5125:'<u4'}[typ]);start=len(self.buf);self.buf.extend(arr.tobytes())
  while len(self.buf)%4:self.buf.append(0)
  view={'buffer':0,'byteOffset':start,'byteLength':arr.nbytes}
  if target:view['target']=target
  self.views.append(view);a={'bufferView':len(self.views)-1,'componentType':typ,'count':len(arr),'type':kind}
  if kind=='VEC3' and len(arr):a['min']=arr.min(axis=0).tolist();a['max']=arr.max(axis=0).tolist()
  self.accessors.append(a);return len(self.accessors)-1
 def mesh(self,name,batches,feature_ids=None):
  prim=[]
  for i,m in enumerate(batches):
   if not m.idx:continue
   # Inspect the exact serialized float32 positions. Clipped roof walls can
   # contain a mathematically tiny triangle whose vertices round to duplicates.
   # Drop only exact zero-area triangles in exported coordinates, never loosen
   # the post-compression geometry equality requirement.
   p32=np.asarray(m.pos,dtype='<f4').astype('f8');ii=np.asarray(m.idx,dtype='i8').reshape(-1,3);tt=p32[ii];area=np.linalg.norm(np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]),axis=1);keep=area>0
   m.float32_degenerate_removed=int((~keep).sum());m.idx=ii[keep].reshape(-1).tolist()
   if not m.idx:continue
   attrs={'POSITION':self.acc(m.pos,5126,'VEC3',34962),'NORMAL':self.acc(m.norm,5126,'VEC3',34962)}
   if feature_ids is not None:attrs['_FEATURE_ID_0']=self.acc(feature_ids[i],5125,'SCALAR',34962)
   prim.append({'attributes':attrs,'indices':self.acc(m.idx,5125,'SCALAR',34963),'material':i})
  self.meshes.append({'name':name,'primitives':prim});return len(self.meshes)-1
 def save(self,path,extras,instancing=False):
  mats=[{'name':n,'pbrMetallicRoughness':{'baseColorFactor':[*c,1],'roughnessFactor':r,'metallicFactor':m}} for n,c,r,m in materials]
  g={'asset':{'version':'2.0','generator':'Shanghai v5 resumable allcity builder','copyright':'© Overture Maps Foundation; © OpenStreetMap contributors ODbL-1.0; Qian Shi et al. CC BY4.0; CMAB/CNBH/GHSL CC BY4.0. Inferred facade geometry MIT.'},'scene':0,'scenes':[{'nodes':list(range(len(self.nodes)))}],'nodes':self.nodes,'meshes':self.meshes,'materials':mats,'buffers':[{'byteLength':len(self.buf)}],'bufferViews':self.views,'accessors':self.accessors,'extras':extras}
  if instancing:g['extensionsUsed']=g['extensionsRequired']=['EXT_mesh_gpu_instancing']
  js=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();js+=b' '*((-len(js))%4);data=struct.pack('<4sII',b'glTF',2,28+len(js)+len(self.buf))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(self.buf),0x004e4942)+self.buf
  if len(data)>=100_000_000:raise RuntimeError('File limit exceeded; split or report indivisible feature')
  path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
  return len(data)

def write_near(path,features,neighbors,tree,roof_shell_function,extras):
 instances={k:[] for k in MODULES};sets=[]
 for f in features:
  ins,unique=feature_near(f,neighbors,tree,roof_shell_function);sets.append(unique)
  for k,v in ins.items():instances[k].extend(v)
 unique=combine(sets)
 for batch in unique:weld(batch)
 e=Encoder();matrix_bytes=0;draws=0
 for k,v in instances.items():
  if not v:continue
  mi=e.mesh(k+'_open_perimeter_module',MODULES[k]);attrs={n:e.acc([it[j] for it in v],5126,t) for n,j,t in [('TRANSLATION',0,'VEC3'),('ROTATION',1,'VEC4'),('SCALE',2,'VEC3')]}
  attrs['_FEATURE_ID_0']=e.acc([it[3] for it in v],5125,'SCALAR')
  e.nodes.append({'name':k+'_instances','mesh':mi,'extensions':{'EXT_mesh_gpu_instancing':{'attributes':attrs}}})
  d=sum(bool(b.idx) for b in MODULES[k]);draws+=d;matrix_bytes+=len(v)*64*d
 e.nodes.append({'name':'source_roofs_and_continuous_caps','mesh':e.mesh('footprint_surfaces',unique)});draws+=sum(bool(b.idx) for b in unique)
 triangles=sum(DETAIL_TRIANGLES[k]*len(v) for k,v in instances.items())+sum(m.tri_count() for m in unique)
 extras={**extras,'expandedTriangles':triangles,'facade_accuracy':'procedural inference; roof overrides retain documented source parameters','structural_wall_coordinates':'canonical world-space float32 shared vertices; no per-bay TRS', 'structural_wall_topology':'open-perimeter skin and genuine reveal faces; detail instances retained', 'cornice_projection_m':.07,'qualified_roof_overhang_added':False,'float32_degenerate_triangles_removed':sum(getattr(m,'float32_degenerate_removed',0) for m in unique)}
 size=e.save(path,extras,True)
 # Geometry buffers exclude TRS source arrays (converted to matrices by Three).
 geometry=sum((len(m.pos)*24+len(m.idx)*4) for m in unique)+sum((len(m.pos)*24+len(m.idx)*4) for k,v in instances.items() if v for m in MODULES[k])
 return {'bytes':size,'expandedTriangles':triangles,'geometryBytes':geometry+matrix_bytes,'drawCalls':draws,'instances':{k:len(v) for k,v in instances.items()},'float32_degenerate_triangles_removed':sum(getattr(m,'float32_degenerate_removed',0) for m in unique)}

def add_base_course(geometry,y0,y1,batch,door_cut=None):
 """Continuous plinth, with doorway gap and no hidden wall-attachment faces."""
 band=geometry.buffer(.035,join_style=2).difference(geometry)
 if door_cut is not None:band=band.difference(door_cut)
 for part in ([band] if band.geom_type=='Polygon' else getattr(band,'geoms',[])):
  if part.geom_type!='Polygon' or part.is_empty:continue
  rings=[list(part.exterior.coords)[:-1]]+[list(r.coords)[:-1] for r in part.interiors]
  surface(rings,y1,(0,1,0),batch);surface(rings,y0,(0,-1,0),batch)
  for ri,ring in enumerate(rings):
   area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring,ring[1:]+ring[:1]))
   if (area>0)!=(ri==0):ring.reverse()
   for a,b in zip(ring,ring[1:]+ring[:1]):
    if geometry.boundary.distance(Point((a[0]+b[0])/2,(a[1]+b[1])/2))<1e-7:continue
    side(a,b,y0,y1,batch)
