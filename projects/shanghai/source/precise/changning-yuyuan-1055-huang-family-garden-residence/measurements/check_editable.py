"""Check positional seams, edge orientation, signed volume and UVs for each editable solid."""
import argparse,json
from pathlib import Path
from collections import Counter
import sys
import numpy as np
source=Path(__file__).absolute().parents[1]/'source'
sys.path.insert(0,str(source))
from build_model import Builder,PALETTE,add_building
def check(lod):
    b=Builder(PALETTE);add_building(b,lod)
    results=[]
    for part in b.parts:
        v=np.asarray(part['vertices']);idx=np.array(part['triangles'])
        unique,weld=np.unique(v.round(8),axis=0,return_inverse=True)
        tri=weld[idx]
        pairs=Counter((int(a),int(c)) for face in tri for a,c in zip(face,np.roll(face,-1)))
        edges=Counter(tuple(sorted(pair)) for pair in pairs.elements())
        xyz=v[idx]
        volume=float(np.einsum('ij,ij->i',xyz[:,0],np.cross(xyz[:,1],xyz[:,2])).sum()/6)
        open_edges=sum(n!=2 for n in edges.values())
        orientation=sum(n!=pairs[(c,a)] for (a,c),n in pairs.items())
        result={'name':part['label'],'material':part['material'],'open_edges':open_edges,'orientation_errors':orientation,'volume_m3':volume,'triangles':len(tri)}
        if 'texcoords' in part:
            uv=np.asarray(part['texcoords'])[idx];a=uv[:,1]-uv[:,0];c=uv[:,2]-uv[:,0]
            result['smallest_twice_uv_area']=float(np.min(np.abs(a[:,0]*c[:,1]-a[:,1]*c[:,0])))
        results.append(result)
    issues=[r for r in results if r['open_edges'] or r['orientation_errors'] or r['volume_m3']<=0 or r.get('smallest_twice_uv_area',1)<1e-12]
    return dict(parts=len(results),triangles=sum(r['triangles'] for r in results),longest_object_utf8_bytes=max(len(r['name'].encode()) for r in results),valid=len(results)-len(issues),issues=issues,materials=sorted({r['material'] for r in results}))
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('out',type=Path);args=parser.parse_args()
    data={'near':check(False),'far':check(True)}
    args.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    for level,r in data.items(): print(level,r['parts'],r['valid'],r['issues'][:2])
