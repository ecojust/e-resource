"""Check the four open reliefs against fixed control points picked on the upright photograph."""
import argparse
import hashlib
import json
import runpy
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

# Control coordinates were sighted independently on equal-sized 156 × 200
# reproductions of the four original crops. They are kept separate from the
# silhouette and relief sampling code that constructed the mesh.
CONTROLS = [
    ((185,2440,352,2750), [(81,52),(78,70),(77,83),(85,93),(94,100),(104,101),(114,89),(117,67),(116,39),(109,30),(99,34)], [(101,60),(101,71),(102,78),(99,80),(106,58)], [(67,49),(72,108),(91,117),(131,87)]),
    ((579,2145,798,2430), [(79,99),(75,113),(73,131),(76,145),(84,158),(93,157),(106,146),(110,127),(109,110),(109,91),(104,68)], [(95,105),(94,117),(96,131),(89,126),(97,100)], [(66,105),(65,146),(100,177),(120,125)]),
    ((1100,1830,1345,2130), [(74,101),(71,117),(71,133),(74,153),(82,166),(93,167),(103,151),(107,134),(108,112),(108,98),(102,76)], [(91,108),(90,121),(90,132),(88,141),(94,113)], [(54,106),(61,150),(90,188),(123,134)]),
    ((1790,1420,2034,1815), [(67,91),(67,105),(67,118),(73,130),(84,142),(92,143),(105,134),(112,119),(115,101),(116,83),(111,69),(95,61),(79,69)], [(88,90),(88,105),(91,119),(82,110),(96,90)], [(55,87),(49,120),(90,167),(127,108)]),
]
RED={'Russet wreath relief','Dark red wreath returns'}


def stations(photo):
    with Image.open(photo) as raw:
        upright=ImageOps.exif_transpose(raw).convert('RGB')
    points=[]
    for ordinal,(box,raised,openings,surrounds) in enumerate(CONTROLS,1):
        left,top,right,bottom=box
        for kind,observed in [('wreath',raised),('centre',openings),('pier',surrounds)]:
            for x,y in observed:
                u=int(np.floor(left+(x+.5)*(right-left)/156))
                v=int(np.floor(top+(y+.5)*(bottom-top)/200))
                rgb=np.asarray(upright.crop((u-1,v-1,u+2,v+2)))
                points.append(dict(wreath=ordinal,zone=kind,pixel=[u,v],source_rgb=np.median(rgb.reshape(-1,3),axis=0).astype(int).tolist()))
    return points


def check(project,source,mesh,points,isolated):
    sys.path.insert(0,str(source))
    from photo_plane import H,D,position
    tools=runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    triangles,indices,names,info=tools['load_triangles'](mesh)
    appearance=tools['material_appearance'](mesh)['materials']
    both=np.array([appearance[n]['doubleSided']for n in names])[indices]
    normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    vertices=triangles.reshape(-1,3)
    homogeneous=np.column_stack((vertices[:,0],vertices[:,2],np.ones(len(vertices))))@H.T+vertices[:,1,None]*D
    if np.min(homogeneous[:,2])*np.max(homogeneous[:,2])<=0:raise ValueError('Unexpected camera-plane crossing')
    screen=(homogeneous[:,:2]/homogeneous[:,2,None]).reshape(-1,3,2)
    lower,upper=np.min(screen,axis=1)-.005,np.max(screen,axis=1)+.005
    checks=[]
    for pt in points:
        u,v=pt['pixel'];origin=position(u,v,-3.0);ray=position(u,v,1.)-origin;ray/=np.linalg.norm(ray)
        idx=np.flatnonzero(np.all(lower<=[u,v],axis=1)&np.all(upper>=[u,v],axis=1))
        idx=idx[both[idx]|((normals[idx]@ray)<-1e-12)]
        material=None;location=None
        if len(idx):
            i,t,p=tools['first_hit'](triangles[idx],origin,ray)
            if np.isfinite(t):material=names[indices[idx[i]]];location=np.round(p,5).tolist()
        if pt['zone']=='wreath':passed=material in RED
        elif isolated:passed=material is None
        else:passed=material is not None and material not in RED and location[1]>-.238
        checks.append(dict(**pt,material=material,position=location,passed=bool(passed)))
    return dict(sha256=info['sha256'],passed=sum(c['passed']for c in checks),count=len(checks),checks=checks)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['project','source','mesh','photo','output']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--isolated',action='store_true')
    a=p.parse_args();picks=stations(a.photo);r=check(a.project,a.source,a.mesh,picks,a.isolated)
    r['photo_sha256']=hashlib.sha256(a.photo.read_bytes()).hexdigest()
    a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(r['passed'],r['count'],[(c['wreath'],c['zone'],c['pixel'],c['material'])for c in r['checks'] if not c['passed']])
