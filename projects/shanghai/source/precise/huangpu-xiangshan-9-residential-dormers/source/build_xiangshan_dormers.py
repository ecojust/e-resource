"""Export both editable window assemblies and check every piece is consistently wound."""
import argparse
from pathlib import Path
import sys
import numpy as np
from xiangshan_dormers import PALETTE,add_dormers
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE.parent/"hongkou-general-post-office/source/common"))
from photo_architecture import Builder
def build(out):
 out.mkdir(exist_ok=True,parents=True)
 for low,name in ((False,'full'),(True,'lod')):
  model=Builder(PALETTE);add_dormers(model,low)
  for part in model.parts:
   vertices=np.asarray(part['vertices']);tri=np.asarray(part['triangles']);v=vertices[tri]
   vol=np.einsum('ij,ij->i',v[:,0],np.cross(v[:,1],v[:,2])).sum()/6
   edges=np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1)
   if vol<=0 or not np.all(np.unique(edges,axis=0,return_counts=True)[1]==2):raise ValueError(part['label'])
  model.save(out/f'xiangshan-dormers-{name}.glb',dict(level=name,scope='Street-side gabled dormers and connecting pair of windows from the 2015 and 2018 photographs'))
  print(name,len(model.parts),sum(len(p['triangles'])for p in model.parts))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('output',type=Path);build(p.parse_args().output)
