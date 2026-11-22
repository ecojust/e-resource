"""Trace the photographed warehouse details against three independently read mesh roles."""
from pathlib import Path
import argparse
import json
import hashlib
import numpy as np
from build_model import SASH, GLASS, EDGE, BRASS, THRESHOLD, transom_height
from xintai_brick_corner import openings,arch,WIDTH,IRON,STONE,SHADOW
from glb_surfaces import decode,hit

def test(path):
    tris, materials, palette = decode(path)
    checks=[]
    def ray(name,origin,direction,matches,tolerance=None):
        result=hit(tris,materials,np.asarray(origin),np.asarray(direction))
        assert result and matches(result[0]),(name,origin,result)
        if tolerance:assert tolerance(result[1]),(name,origin,result)
        checks.append(dict(target=name,from_m=origin,direction=direction,first_material=result[0],first_hit_m=result[1]))
    for i,o in enumerate(openings()):
        c,sill,h,spring,rise,th,red=o
        head=spring+rise
        label=f'bay-{i%2+1}-level-{i//2+1}'
        trans=transom_height(i)
        for offset in [-.67,-.17,.19,.69]:
            for frac in [.25,.53,.76]:
                ray(label+' lower glazing',[c+offset,-1.,sill+(trans-sill)*frac],[0.,1.,0.],lambda m:m in GLASS)
            ray(label+' transom glass',[c+offset*.8,-1.,(trans+head)/2],[0.,1.,0.],lambda m:m in GLASS)
        for offset in [-.46,.23,.6]:
            ray(label+' cross rail',[c+offset,-1.,trans],[0.,1.,0.],lambda m:m==SASH)
        for offset in ([0.] if i<2 else ([-.32,.33]if i%2 else [-.31,.31])):
            ray(label+' mullion',[c+offset,-1.,sill+.48*(trans-sill)],[0.,1.,0.],lambda m:m in (EDGE,SASH) if i==4 else m==SASH)
            if i==4:
                ray(label+' fixed mullion behind projected casement',[c+offset,.176,sill+.48*(trans-sill)],[0.,1.,0.],lambda m:m==SASH)
        arc,_=arch(o,32)
        for frac in [.13,.29,.49,.68,.84]:
            x,z=arc(frac,.099)
            ray(label+' outer arch',[x,-1.,z],[0.,1.,0.],lambda m:'brick' in m or 'face' in m)
        for side in [-1,1]:
            ray(label+' recessed jamb',[c,.09,(sill+spring)/2],[side,0.,0.],lambda m:'brick' in m or 'face' in m,lambda p:abs(abs(p[0]-c)-h)<.0001)
        if i<2:
            ray(label+' door handle',[c+.109,-1.,1.05],[0.,1.,0.],lambda m:m==BRASS)
        else:
            ray(label+' light sill',[c+.12,-1.,sill-.059],[0.,1.,0.],lambda m:m==STONE)
    for z in [.38,1.08,1.83,2.59,3.31]:
        ray('end wall continuous dark course',[WIDTH+1.,.82,z],[-1.,0.,0.],lambda m:m==SHADOW)
    for z in [4.01,7.77,7.38]:
        ray('iron plate on raised brick pier',[3.76,-1.,z],[0.,1.,0.],lambda m:m==IRON)
    return dict(triangles=len(tris),checks=len(checks),probes=checks)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw',type=Path,required=True);p.add_argument('--decoded-web',type=Path,required=True);p.add_argument('--decoded-lod',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();roles={k:test(v)for k,v in [('raw',a.raw),('full',a.decoded_web),('lod',a.decoded_lod)]}
    for ref,web,low in zip(*(v['probes']for v in roles.values())):
        assert ref['target']==web['target']==low['target'] and ref['first_material']==web['first_material']==low['first_material']
        assert np.max(np.abs(np.asarray(ref['first_hit_m'])-low['first_hit_m']))<.004
    a.report.write_text(json.dumps(dict(order=488,passed=True,roles=roles),ensure_ascii=False,indent=2)+'\n')
