"""Verify signed volumes, paired glass UVs and the measured through-light patterns."""
from collections import Counter
from pathlib import Path
import hashlib,json,sys
import numpy as np
root=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(root/'source'),str(root.parent/'hongkou-general-post-office/source/common')]
from photo_architecture import Builder
from rongkang_window_sashes import PALETTE,add_street_windows,schedule,GLASS,SHADE

def check():
    table=schedule(); rows=[]
    for lod in ('full','lod'):
        b=Builder(PALETTE);add_street_windows(b,lod,table)
        glass=0;minimum=float('inf')
        for part in b.parts:
            v=np.array(part['vertices']);fs=np.array(part['triangles']);v=v-v.mean(axis=0)
            edges=Counter(tuple(sorted((int(a),int(c)))) for tri in fs for a,c in zip(tri,np.roll(tri,-1)))
            assert set(edges.values())=={2},part['label']
            vols=np.einsum('ij,ij->i',v[fs[:,0]],np.cross(v[fs[:,1]],v[fs[:,2]]))/6
            volume=float(vols.sum());assert volume>1e-8,(part['label'],volume)
            minimum=min(minimum,volume)
            if part['material'] in (GLASS,SHADE):
                uv=np.array(part['texcoords']);assert len(uv)==len(v) and np.ptp(uv[:,0])>0 and np.ptp(uv[:,1])>0
                glass+=1
        for o in table['openings']:
            pieces=[p for p in b.parts if p['label'].startswith('Rongkang '+o['id']+' ')]
            expected=(len(o['horizontal_divisions'])+1)*(len(o['vertical_divisions'])+1)-len(o['vertical_divisions'])*int(o['upper_undivided'])
            assert sum(p['material'] in (GLASS,SHADE) for p in pieces)==(1 if lod=='lod' else expected)
        rows.append(dict(level=lod,closed_solids=len(b.parts),glazed_solids=glass,
                         triangles=sum(len(p['triangles']) for p in b.parts),smallest_volume_m3=minimum))
    return rows

if __name__=='__main__': print(json.dumps(check(),indent=2))
