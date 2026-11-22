"""Cast the independently selected photograph rays into an exported corner-entrance GLB."""
import argparse
import json
from pathlib import Path
import runpy
import sys

import numpy as np


def measure(project,source,mesh,sample,isolated):
    sys.path.insert(0,str(source))
    from photo_plane import H,D,position
    from corner_fanlight import BRONZE,BRONZE_EDGE,GLASS,STEEL,STONE
    lib=runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    tris,ids,materials,identity=lib['load_triangles'](mesh)
    ma=lib['material_appearance'](mesh)['materials']
    both=np.array([ma[m]['doubleSided']for m in materials])[ids]
    n=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0])
    xyz=tris.reshape(-1,3);q=np.column_stack((xyz[:,0],xyz[:,2],np.ones(len(xyz))))@H.T+xyz[:,1,None]*D
    if np.min(q[:,2])*np.max(q[:,2])<=0:raise ValueError('Mesh straddles camera')
    pix=(q[:,:2]/q[:,2,None]).reshape(-1,3,2);lo=pix.min(axis=1)-.008;hi=pix.max(axis=1)+.008
    roles={'bronze':{BRONZE,BRONZE_EDGE},'glass':{GLASS},'metal':{STEEL},'trough':{STONE},'ridge':{STONE}}
    result=[];depths={}
    for obs in sample['points']:
        uv=obs['pixel'];o=position(*uv,-2.8);direction=position(*uv,1.4)-o;direction/=np.linalg.norm(direction)
        select=np.flatnonzero(np.all(lo<=uv,axis=1)&np.all(hi>=uv,axis=1))
        select=select[both[select]|((n[select]@direction)<-1e-12)]
        got=None;loc=None
        if len(select):
            index,dist,hit=lib['first_hit'](tris[select],o,direction)
            if np.isfinite(dist):
                got=materials[ids[select[index]]];loc=np.round(hit,6).tolist()
        kind=obs['kind']
        if kind=='counter':
            passed=got is None if isolated else got is not None and got not in {BRONZE,BRONZE_EDGE}
        else:passed=got in roles[kind]
        result.append(dict(**obs,material=got,point_m=loc,passed=passed))
        if kind in ('trough','ridge')and loc is not None and passed:depths.setdefault(obs['group'],{})[kind]=loc[1]
    comparison=[dict(group=g,source_dark_groove_deeper_by_m=round(d['trough']-d['ridge'],6))for g,d in depths.items()if set(d)=={'ridge','trough'}]
    return dict(**identity,photo_sha256=sample['photograph_sha256'],passed=sum(o['passed'] for o in result),count=len(result),points=result,grooves=comparison)


if __name__=='__main__':
    args=argparse.ArgumentParser(description=__doc__)
    for v in ('project','source','mesh','controls','output'):args.add_argument('--'+v,type=Path,required=True)
    args.add_argument('--isolated',action='store_true')
    a=args.parse_args();r=measure(a.project,a.source,a.mesh,json.loads(a.controls.read_bytes()),a.isolated)
    a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(r['passed'],r['count'],'failed',[(p['category'],p.get('group'),p['kind'],p['pixel'],p['material'])for p in r['points']if not p['passed']])
    depths=[q['source_dark_groove_deeper_by_m']for q in r['grooves']];print('arch grooves',sum(v>0 for v in depths),'/',len(depths),'depth differences m',np.round(np.percentile(depths,[0,50,100]),4))
