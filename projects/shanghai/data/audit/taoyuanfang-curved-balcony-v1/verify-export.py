"""Inspect the three serialized balcony meshes with material and distance bounded intersection tests."""
import argparse,json,runpy,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).absolute().parent;SRC=HERE.parents[2]/'source/precise/changning-taoyuanfang-curved-balcony'
sys.path.insert(0,str(SRC/'source'))
from geometry_reference import frontage,surface
from scipy.interpolate import PchipInterpolator
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
INSPECT=inspect
X,CURVE=frontage()
def cases():
    out=[]
    def add(label,pos,direction,length,allowed,span):
        out.append(dict(name=label,origin=list(map(float,pos)),direction=list(map(float,direction)),length=length,allowed=allowed,range_m=span))
    for j,x in enumerate(np.linspace(-2.79,2.99,44)):
        y=CURVE(x)
        for label,z,mat,low,high in [('lower moulding',-.353,'Pale concrete moulding',.205,.217),
                ('recess between beads',-.316,'Darker edge groove',.223,.235),('upper moulding',-.279,'Pale concrete moulding',.204,.215),
                ('top fascia',-.205,'Warm grey balcony finish',.235,.248)]:
            add(f'{label} {j+1}',[x,y-.21,z],[0,1,0],.30,[mat],[low,high])
    data=json.loads((SRC/'measurements/drying-rack.json').read_bytes());ends=np.array(data['rod_endpoints_xyz']);z=data['rod_height_m']
    for i,(start,stop)in enumerate(zip(*ends)):
        for k,t in enumerate(np.linspace(.15,.84,8)):
            p=start+(stop-start)*t
            add(f'drying rod {i+1} / {k+1}',p+[0,0,.09],[0,0,-1],.14,['Polished drying rod'],[.074,.0785])
        for j,(q,sgn) in enumerate([(start,-1),(stop,1)]):
            add(f'plastic end {i+1} / {j+1}',q+[sgn*.065,0,0],[-sgn,0,0],.08,['Grey rod stopper'],[.058,.060])
    yz=ends[0,:,1];sp=data['rod_spacing_m']
    for j,x in enumerate([-2.38,1.737]):
        for i,u in enumerate(yz):
            for label,v,h in [('top',u,z+.025),('bottom',u,z-.195),('crossed',(u+u+sp)/2,z-.083)]:
                span=[.033,.035]if i==3 and label=='crossed'else [.059,.063]
                add(f'{label} pivot {j+1} / {i+1}',[x+.10,v,h],[-1,0,0],.15,['Aged pivot cap'],span)
    # Front rail elevations come from the rail's own imaged control points.
    top=np.asarray([[138,273],[181,251],[232,226],[279,207],[305,192],[345,177],[406,152],[451,135],[509,114],[559,96],[593,86]])
    low=np.asarray([[94,404],[151,382],[210,363],[267,341],[287,333],[351,304],[403,290],[456,277],[517,264],[578,245],[622,232]])
    for tag,coords,bounds in [('top',top,[-1.64,2.00]),('bottom',low,[-2.10,2.03])]:
        xyz=surface(coords/2+[395,165]);curve=PchipInterpolator(xyz[:,0],xyz[:,2])
        for i,x in enumerate([-2.31,-1.872,-1.312,-1.055,-.804,-.546,-.312,.523,.753,1.18,1.58,1.88,2.172,2.568,2.797]):
            zz=float(curve(np.clip(x,*bounds)))
            add(f'black {tag} rail / {i+1}',[x,CURVE(x)-.15,zz],[0,1,0],.34,['Black painted railing'],[.212,.246])
    for i,(px,py) in enumerate([(107,50),(190,18),(227,364),(128,400),(112,117),(204,142),(120,258),(220,280)]):
        p=surface([[525+px/5.002,246+py/5.002]],.072)[0]
        add(f'central rectangular insert {i+1}',p-[0,.065,0],[0,1,0],.12,['Black painted railing'],[.050,.071])
    for j,x in enumerate([-2.32,-1.95,-1.02,-.35,.43,.98,1.68,2.37]):
        for k,y in enumerate([.68,1.11,1.39]):
            add(f'slab underside {j+1}/{k+1}',[x,y,-.57],[0,0,1],.22,['Yellowed soffit'],[.160,.162])
    for j,x in enumerate([-1.43-.067,-1.43+.069]):
        add(f'lamp shade {j+1}',[x,1.285,-.925],[0,0,1],.20,['Lamp enamel'],[.16,.18])
    for i,px in enumerate([-.65,-.37,.16,.49]):
        for j,zz in enumerate([.78,1.17,1.82,2.26]):
            add(f'rear reflective pane {i+1}/{j+1}',[px,1.50,zz],[0,1,0],.30,
                ['Blue reflected glass','Pale reflected glass','Shadowed blue glass'],[.187,.191])
    return out
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('raw','full','lod','output'):ap.add_argument(n,type=Path)
    a=ap.parse_args();tests=cases();results={k:inspect(getattr(a,k),tests)for k in ['raw','full','lod']}
    a.output.write_text(json.dumps(results,ensure_ascii=False,separators=(',',':'))+'\n')
    print(len(tests),{k:[r['name']for r in v['cases']if not r['passed']]for k,v in results.items()})
    assert all(r['passed']for r in results.values())
