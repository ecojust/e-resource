"""Check every independent closed shell of the editable arch and window pieces."""
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import argparse
import json
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'hongkou-general-post-office/source/common')]
from photo_architecture import Builder
from shanyin_arches import PALETTE, add_shanyin_arches


def inspect(part):
    vertices=np.asarray(part['vertices'],dtype='float64')
    faces=np.asarray(part['triangles'],dtype=np.int64)
    links=list(range(len(vertices)))
    def root(i):
        while links[i]!=i:
            links[i]=links[links[i]]
            i=links[i]
        return i
    edges=Counter()
    for a,b,c in faces:
        for x,y in ((a,b),(b,c),(c,a)):
            edges[tuple(sorted((x,y)))]+=1
            links[root(y)]=root(x)
    shells=defaultdict(list)
    for face in faces:
        shells[root(face[0])].append(face)
    volumes=[]
    for block in shells.values():
        tri=vertices[np.asarray(block)]
        tri-=tri[0,0].copy()
        volume=np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6
        volumes.append(float(volume))
    bad=sum(n!=2 for n in edges.values())
    return {'label':part['label'],'shells':len(volumes),'triangles':len(faces),'non_two_sided_edges':bad,
            'smallest_shell_volume_m3':min(volumes),'all_shell_volumes_positive':min(volumes)>0,'passed':not bad and min(volumes)>0}


def audit(layout):
    output=[]
    for variant in ('full','lod'):
        b=Builder(PALETTE);add_shanyin_arches(b,variant,layout['rows'])
        parts=[inspect(p) for p in b.parts]
        output.append({'variant':variant,'groups':len(parts),'shells':sum(p['shells'] for p in parts),
                       'triangles':sum(p['triangles'] for p in parts),'passed':all(p['passed'] for p in parts),
                       'smallest_shell_volume_m3':min(p['smallest_shell_volume_m3']for p in parts),'pieces':parts})
    return output


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('layout',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args()
    rows=audit(json.loads(a.layout.read_bytes()))
    report={'layout_sha256':sha256(a.layout.read_bytes()).hexdigest(),
            'source_sha256':sha256((HERE.parent/'source/shanyin_arches.py').read_bytes()).hexdigest(),'variants':rows}
    a.output.write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
    for row in rows:print(row['variant'],row['groups'],row['shells'],row['triangles'],row['passed'])
    raise SystemExit(not all(row['passed'] for row in rows))
