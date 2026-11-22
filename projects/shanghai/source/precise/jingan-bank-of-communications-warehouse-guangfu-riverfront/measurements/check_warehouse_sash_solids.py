"""Verify each editable frame, grille and pane as constructed and optionally save isolated GLBs."""
from collections import Counter
from pathlib import Path
import argparse,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'hongkou-general-post-office/source/common')]
from photo_architecture import Builder
from warehouse_window_sashes import PALETTE, add_west_return_windows, add_warehouse_windows, SKY, CLEAR, DARK

def verify(level,layout,save):
    builder=Builder(PALETTE)
    add_warehouse_windows(builder,level,layout)
    add_west_return_windows(builder,level,layout)
    assert len(builder.parts)==3*72
    by_key={};volumes=[];triangles=0;glazed=0
    for part in builder.parts:
        v=np.array(part['vertices']);f=np.array(part['triangles'])
        label=part['label'];key=label.split(' | ')[0].removeprefix('Warehouse ')
        by_key.setdefault(key,[]).append(part['material'])
        edges=Counter(tuple(sorted((a,b)))for t in f for a,b in zip(t,np.roll(t,-1)))
        assert set(edges.values())=={2},label
        # Triangle indices within a glass group are individual closed eight-corner panes.
        glass=part['material'] in (SKY,CLEAR,DARK)
        if glass:
            uv=np.array(part['texcoords'])
            assert len(uv)==len(v) and len(v)%8==0
            a,b,c=uv[f].transpose(1,0,2);u=b-a;w=c-a
            assert np.all(np.abs(u[:,0]*w[:,1]-u[:,1]*w[:,0])>1e-12)
            glazed+=len(v)//8
        for island in (np.split(f,len(v)//8) if glass else [f]):
            t=v[island];t=t-t[0,0]
            volume=float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6)
            assert volume>1e-8,(label,volume);volumes.append(volume)
        triangles+=len(f)
    assert len(by_key)==72 and all(len(set(v))==3 for v in by_key.values())
    if save:builder.save(save/f'sashes-{level}.glb')
    return dict(lod=level,windows=len(by_key),editable_parts=len(builder.parts),checked_closed_solids=len(volumes),glazing_islands=glazed,
                triangles=triangles,smallest_positive_volume_m3=min(volumes),materials=list(PALETTE))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--export',action='store_true');a=p.parse_args()
    a.output.mkdir(exist_ok=True,parents=True)
    table=json.loads((HERE/'riverfront-layout.json').read_bytes())
    results=[verify(l,table,a.output if a.export else None) for l in ('full','lod')]
    (a.output/'editable-sash-solids.json').write_text(json.dumps(results,indent=2)+'\n')
    print(results)
