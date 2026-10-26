"""Boundary-only union of source-identified rectangular wall volumes.
No decoration/material-wide geometric guessing. Recessed spans retain their depths.
"""
from pathlib import Path
import json,math,collections,hashlib
import numpy as np
from arguments import workdir
P=workdir();TOL=2e-5

def key(r):
 return (tuple(round(x,6)for x in r['u']),tuple(round(x,6)for x in r['n']),round(float(np.dot(r['a'],r['n'])),4))
def cluster(values):
 groups=[]
 for v in sorted(values):
  if groups and v-groups[-1][0]<=TOL:groups[-1].append(v)
  else:groups.append([v])
 return np.array([sum(g)/len(g)for g in groups])
def index(axis,value):
 q=int(np.argmin(abs(axis-value)));assert abs(axis[q]-value)<=TOL,(value,axis[q]);return q

def build(bid):
 cap=json.loads((P/f'{bid}-capture.json').read_text());groups=collections.defaultdict(list)
 for r in cap['captured']:groups[key(r)].append(r)
 contacts=collections.defaultdict(list)
 for c in cap['contacts']:contacts[key(c)].append(c)
 out={'id':bid,'source_capture_sha256':hashlib.sha256((P/f'{bid}-capture.json').read_bytes()).hexdigest(),'groups':[],'statistics':{}}
 grand=collections.Counter()
 for gi,(k,boxes)in enumerate(groups.items()):
  base=boxes[0];a=np.array(base['a']);u=np.array(base['u']);n=np.array(base['n']);basis=np.array([u,[0,0,1],n]).T
  assert abs(np.linalg.det(basis))>.99999
  bdata=[];values=[[],[],[]]
  for b in boxes:
   delta=np.linalg.solve(basis,np.array(b['a'])-a);q=b['bounds'];bounds=[q[0]+delta[0],q[1]+delta[0],q[2],q[3],q[4]+delta[2],q[5]+delta[2]]
   assert abs(delta[1])<TOL
   bdata.append((b,bounds))
   for j in range(3):values[j]+=bounds[j*2:j*2+2]
  for c in contacts[k]:
   delta=np.linalg.solve(basis,np.array(c['a'])-a)
   values[0]+=[v+delta[0]for v in c['u_breaks']];values[1]+=c['z_breaks']
  axes=[cluster(v)for v in values];shape=tuple(len(v)-1 for v in axes);occ=np.zeros(shape,np.int16);conflict=0;max_shift=0
  for b,bb in bdata:
   ij=[index(axes[j],bb[2*j+i])for j in range(3)for i in range(2)];s=tuple(slice(ij[j*2],ij[j*2+1])for j in range(3));view=occ[s];conflict+=int(np.count_nonzero((view>0)&(view!=b['material']+1)));occ[s]=b['material']+1
   max_shift=max(max_shift,max(abs(axes[j][ij[j*2+i]]-bb[j*2+i])for j in range(3)for i in range(2)))
  assert not conflict,(bid,gi,'different source material overlap',conflict)
  vertices=[];faces=[];materials=[];nodes={}
  def vertex(q):
   q=tuple(q)
   if q not in nodes:
    v=a+basis@np.array([axes[j][q[j]]for j in range(3)]);nodes[q]=len(vertices);vertices.append(v.tolist())
   return nodes[q]
  for axis in range(3):
   other=[j for j in range(3)if j!=axis]
   for sign in [-1,1]:
    neighbor=np.zeros(shape,np.int16)
    ss=[slice(None)]*3;dd=ss.copy()
    if sign<0:ss[axis]=slice(None,-1);dd[axis]=slice(1,None)
    else:ss[axis]=slice(1,None);dd[axis]=slice(None,-1)
    neighbor[tuple(dd)]=occ[tuple(ss)]
    cells=np.argwhere((occ>0)&(neighbor==0))
    for ij in cells:
     q=ij.copy();q[axis]+=int(sign>0);v=[]
     for p1,p2 in [(0,0),(1,0),(1,1),(0,1)]:
      qq=q.copy();qq[other[0]]+=p1;qq[other[1]]+=p2;v.append(vertex(qq))
     normal=np.cross(np.array(vertices[v[1]])-vertices[v[0]],np.array(vertices[v[2]])-vertices[v[0]])
     if float(np.dot(normal,basis[:,axis]*sign))<0:v.reverse()
     faces.append(v);materials.append(int(occ[tuple(ij)])-1)
  counts=collections.Counter();direction=collections.Counter();volume=0.;area_front=0.
  for f in faces:
   for i,j in zip(f,f[1:]+f[:1]):counts[tuple(sorted((i,j)))]+=1;direction[(i,j)]+=1
   v0,v1,v2,v3=[np.array(vertices[i])for i in f]
   volume+=np.dot(v0,np.cross(v1,v2))/6+np.dot(v0,np.cross(v2,v3))/6
  bad=sum(c!=2 for c in counts.values());winding=sum(direction[(i,j)]!=direction[(j,i)]for i,j in counts)
  assert bad==0 and winding==0,(bid,gi,'nonmanifold',bad,winding)
  du,dz,dd=[np.diff(x)for x in axes];expected=float(np.sum((occ>0)*du[:,None,None]*dz[None,:,None]*dd[None,None,:]))*abs(np.linalg.det(basis))
  assert abs(volume-expected)<max(1e-6,expected*1e-9),(bid,gi,volume,expected)
  # Surface partition at each front-depth level proves that original setbacks
  # remain explicit. Only occupied/empty transitions emit faces at any depth.
  exposure=[]
  for di,d in enumerate(axes[2]):
   behind=occ[:,:,di-1]>0 if di>0 else np.zeros(shape[:2],bool)
   ahead=occ[:,:,di]>0 if di<shape[2] else np.zeros(shape[:2],bool)
   area=float(np.sum((behind&~ahead)*du[:,None]*dz[None,:]));
   if area>1e-8:exposure.append({'depth_from_frame_m':float(d),'front_area_m2':area})
  report={'group':gi,'frame_a':a.tolist(),'u':u.tolist(),'n':n.tolist(),'source_panels':len(boxes),'source_objects':sorted(set(b['object']for b in boxes)),'axis_size':[len(x)for x in axes],'depth_breaks_m':axes[2].tolist(),'front_exposed_area_by_depth':exposure,'max_axis_snap_m':max_shift,'rectangular_union_volume_m3':expected,'mesh_signed_volume_m3':volume,'nonmanifold_edges':bad,'inconsistently_oriented_edges':winding,'vertices':len(vertices),'quads':len(faces),'triangles':len(faces)*2,'source_material_indices':sorted(set(materials)),'contact_arch_or_oculus_count':len(contacts[k])}
  out['groups'].append({'report':report,'vertices':vertices,'faces':faces,'materials':materials})
  grand.update({'panels':len(boxes),'vertices':len(vertices),'quads':len(faces),'triangles':len(faces)*2,'groups':1})
 out['statistics']=dict(grand);(P/f'{bid}-wall-union.json').write_text(json.dumps(out,separators=(',',':')));print(bid,dict(grand),flush=True)
for bid in ['bund19','bund20','bund23']:build(bid)
