"""Trace the photographed bay panes plus each new opening and the roof return."""
import json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/jingan-may-lee-court-no14-canted-bay/source'
sys.path.insert(0,str(SOURCE))
from garden_bay import GLASS,STONE,LIP,STEEL,MULLION,BRICK
from garden_extensions import OBS,PLANES,DEEP,ROOF
from sections import test
from read_study import decode,hit
def inspect(path):
    tri,names,palette=decode(path)
    # Old isolated construction was measured before the rainwater pipe was added.
    # Retain each whole-building first hit, and separately read the same line
    # against the original bay surfaces to document the photographed obstruction.
    from garden_bay import PALETTE
    keep=np.isin(names,list(PALETTE))
    first=[]
    def read_underlying(t,m,origin,direction):
        first.append(hit(tri,names,origin,direction))
        return hit(t,m,origin,direction)
    rows=test(tri[keep],names[keep],read_underlying)
    for row,actual in zip(rows,first,strict=True):
        row['whole_first_material']=None if actual is None else actual[0]
        row['whole_first_point']=None if actual is None else actual[1]
        row['first_matches_isolated']=actual is not None and actual[0]==row['material']
        row['documented_occlusion']=bool(actual and 'downpipe' in actual[0] and row['material']==BRICK and row['label']=='narrow continuous brickwork')
        row['passed']=row['first_matches_isolated'] or row['documented_occlusion']
    for record in OBS['aperture_observations']:
        l,r,lo,hi=record['outer_trim_m']
        face,offset=PLANES[record['plane']]
        direction=np.array([0.,1.,0.] if face=='front' else [1.,0.,0.])
        def probe(u,z,expected,d,name):
            v=[u,offset-.32,z] if face=='front' else [offset-.32,u,z]
            origin=np.array(v);first=hit(tri,names,origin,direction)
            success=first is not None and first[0] in expected and abs(np.linalg.norm(first[1]-origin)-(.32+d))<.004
            rows.append(dict(label=record['kind']+' '+name,material=None if first is None else first[0],
                point=None if first is None else first[1],expected=expected,passed=bool(success)))
        if record['columns']==1:
            probe((l+r)/2,(lo+hi)/2,[DEEP],.43,'shaded opening')
            continue
        probe(l+.036,(lo+hi)/2,[STONE],-.040,'jamb')
        probe(r-.032,(lo+hi)/2,[STONE],-.040,'opposing jamb')
        probe((l+r)/2,lo+.064,[LIP],-.085,'sill')
        xs=np.linspace(l+.112,r-.112,record['columns']+1)
        zs=np.linspace(lo+.137,hi-.115,record['rows']+1)
        for i,(a,b) in enumerate(zip(xs,xs[1:])):
            for j,(bottom,top) in enumerate(zip(zs,zs[1:])):
                probe((a+b)/2,(bottom+top)/2,list(GLASS),.184,f'pane {i+1}/{j+1}')
        for x in xs[1:-1]:probe(x,(zs[0]+zs[1])/2,[MULLION],.132,'stile')
        for z in zs[1:-1]:probe((xs[0]+xs[1])/2,z,[STEEL],.136,'rail')
    out=dict(sha256=__import__('hashlib').sha256(path.read_bytes()).hexdigest(),triangles=len(tri),cases=rows,passed=all(x.get('passed',True) for x in rows))
    return out
if __name__=='__main__':
    out={role:inspect(Path(p)) for role,p in zip(('raw','full','lod'),sys.argv[1:4])}
    Path(sys.argv[4]).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    for k,v in out.items():print(k,len(v['cases']),[(r['label'],r['material']) for r in v['cases'] if not r.get('passed',True)])
    sys.exit(0 if all(v['passed'] for v in out.values()) else 1)
