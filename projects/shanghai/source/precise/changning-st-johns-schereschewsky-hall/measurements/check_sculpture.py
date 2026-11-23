"""Rebuild both levels from the editable component, check edge incidence, and project the bronze and granite into the documented 2004 station."""
import argparse,hashlib,sys,json
from pathlib import Path
from collections import Counter
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"source"))
from sculpture import add_sculpture,PALETTE
a=argparse.ArgumentParser();a.add_argument('common',type=Path,help='Folder containing photo_architecture.py');a.add_argument('stations',type=Path,help='Measured tower-stations.json');a.add_argument('out',type=Path);a=a.parse_args()
sys.path.insert(0,str(a.common));from photo_architecture import Builder
r=json.loads(a.stations.read_bytes())['stations']['court'];e=np.array(r['C']);M=np.array(r['P']);a.out.mkdir(parents=True,exist_ok=True)
def pix(x):
 p=M@np.r_[x,1];return p[:2]/p[2]
def direct(m,b,lo,hi):
 ids=[j for j,r in enumerate(b.parts)if m in r['label']]
 v=np.vstack([b.parts[i]['vertices']for i in ids]);uv=np.array([pix(x)for x in v]);return [uv[:,0].min(),uv[:,1].min(),uv[:,0].max(),uv[:,1].max()]
stats={}
for lod in (False,True):
 b=Builder();add_sculpture(b,lod);name='statue-'+('lod'if lod else 'full');p=a.out/(name+'.glb');b.save(p,{'sculpture':'Zou Taofen (1995), southern court'})
 errs=[];total=0;rows=[];faces=[];volumes={}
 for part in b.parts:
  v=np.asarray(part['vertices']);f=np.asarray(part['triangles']);etc=Counter(tuple(sorted((q[i],q[(i+1)%3])))for q in f for i in range(3));bad=sum(n!=2 for n in etc.values())
  assert not bad,part['label'];total+=len(f)
  directed=Counter((q[i],q[(i+1)%3])for q in f for i in range(3))
  assert all(directed[(j,i)]==n for (i,j),n in directed.items()),part['label']
  t=v[f];shift=t-v.mean(axis=0)
  vol=np.einsum('ij,ij->i',shift[:,0],np.cross(shift[:,1],shift[:,2])).sum()/6
  assert vol>1e-12,(part['label'],vol)
  volumes[part['label']]=vol;area=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1);assert area.min()>1.e-12,(part['label'],area.min())
  cols=PALETTE[part['material']]['color'];normal=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);brightness=.64+.36*np.maximum(0,normal@np.array([-.48,.46,.74])/area)
  for xyz,shade in zip(t,brightness):
   depth=np.linalg.norm(xyz.mean(0)-e);uv=[tuple(pix(x))for x in xyz];faces.append((depth,uv,tuple(int(c*255*shade)for c in cols)))
 im=Image.new('RGB',(1000,745),(225,225,225));dr=ImageDraw.Draw(im)
 for _,pts,col in sorted(faces,reverse=True):dr.polygon(pts,fill=col)
 im.crop((235,440,756,721)).save(a.out/(name+'-rear-projection.png'))
 bounds={key:direct(key,b,None,None)for key in ('ground step','square inscription die','hair crown')}
 # Only the two bounding corners of the north tread and the crown of the head
 # are comparable between views. A head top or slab foot is a silhouette point.
 u=(bounds['hair crown'][0]+bounds['hair crown'][2])/2
 stats[name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'parts':len(b.parts),'triangles':total,'open_boundary_edges':0,'nonmanifold_edges':0,'all_directed_edges_balanced':True,'smallest_positive_signed_volume_m3':min(volumes.values()),'signed_volume_range_m3':[min(volumes.values()),max(volumes.values())],'projected_bounds_uv':bounds,'rear_crown_original_uv':[499,471],'rear_crown_model_uv':[u,bounds['hair crown'][1]],'photos_embedded':False}
(a.out/'sculpture-check.json').write_text(json.dumps(stats,indent=2)+'\n')
