"""Export both ordinary editable levels of the 195 street-facing window pair."""
import argparse
from pathlib import Path
import sys
import numpy as np
from west_upper_windows import PALETTE,add_windows

P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'hongkou-general-post-office'/'source'/'common'))
from photo_architecture import Builder

def build(dst):
    dst.mkdir(parents=True,exist_ok=True)
    for lod in ('full','lod'):
        b=Builder(PALETTE);add_windows(b,lod)
        for part in b.parts:
            pts=np.array(part['vertices']);faces=np.array(part['triangles']);f=pts[faces]
            volume=np.einsum('ij,ij->i',f[:,0],np.cross(f[:,1],f[:,2])).sum()/6
            edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
            if volume<=0 or np.any(np.unique(edges,axis=0,return_counts=True)[1]!=2):
                raise ValueError('Open or inverted part '+part['label'])
        b.save(dst/('west-upper-'+lod+'.glb'),{'subject':'Upper lights and shallow sills of 195 Shaanxi Road South','lod':lod,'source':'WQL, 2018-06-10'})
        print(lod,len(b.parts),sum(len(p['triangles']) for p in b.parts))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path)
    build(p.parse_args().output)
