"""Shoot the original and both decoded meshes through the dormer, clay rows and open loggia."""
from pathlib import Path
import json,sys,runpy
import numpy as np

HERE=Path(__file__).absolute().parent
SOURCE=HERE.parents[2]/'source/precise/changning-cypress-hotel-2-dormer-and-loggia'
C=json.loads((SOURCE/'measurements/lawn-camera.json').read_bytes())
Q=np.asarray(C['pinhole_3x4']);E=np.asarray(C['eye_xyz']);INV=np.linalg.inv(Q[:,:3])
test=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
def cases():
    r=[]
    def ray(name,pixel,materials,end_y=None):
        d=INV@np.r_[pixel,1.];d/=np.linalg.norm(d);length=80. if end_y is None else (end_y-E[1])/d[1]
        r.append(dict(name=name,origin=E.tolist(),direction=d.tolist(),length=float(length),allowed=materials,range_m=None))
    crops=json.loads((SOURCE/'measurements/loggia-geometry-checked.json').read_bytes())
    samples=crops['results'][0]['probes']
    # Stop immediately behind the foreground pier and rail. Empty arches have a
    # recessed back wall and therefore should see daylight only over this interval.
    for i,p in enumerate(samples):
        m=p['foreground_material'];ray('gallery foreground '+str(i+1),p['pixel'],[m]if m else None,-.51)
    window=['Cypress shaded garden glass','Cypress reflected garden glass']
    for i,p in enumerate([(475,263),(484.3,264),(501.4,258.8),(511.3,274.4),(482.3,342),(490.5,345.7),(503.2,345)]):ray('rear and upper brick windows '+str(i+1),p,window)
    for i,p in enumerate([(458,303),(482,305),(492,275),(510,304)]):ray('running bond field '+str(i+1),p,['Cypress red clay','Cypress russet clay','Cypress orange clay','Cypress warm bedding mortar'])
    for i,(x,mat) in enumerate([(491.,'Blue on left dormer glass'),(506.8,'Dark blue on projecting casement')]):
        for j,y in enumerate([193.0,198.0,204.0,209.0]):ray(f'dormer true glass {i+1}/{j+1}',[x,y],[mat])
    for j,p in enumerate([(490.6,216.0),(494.0,216.3)]):ray('left curtain '+str(j+1),p,['Pale curtain behind the left pane'])
    for j,p in enumerate([(480.5,197),(517.7,202),(499.5,201),(486,184.5)]):
        ray('dormer posts and top cap '+str(j+1),p,['Red lead painted timber','Sunlit terracotta timber trim','Yellow clay on the dormer cheek'])
    pans=['Ochre roof pans with mineral speckle','Fired orange pan','Weathered russet pan','Dark upper roof joints','Orange clay at the ridge']
    for x in [460.,467.,525.,531.,536.,541.]:
        for y in [197.,205.,212.,221.,231.]:ray(f'principal roof {x}/{y}',[x,y],pans)
    for x in [603,614,627,638,650]:
        for y in [205,214,224,236]:ray(f'over loggia {x}/{y}',[x,y],pans)
    for j,p in enumerate([(572,201),(573,206)]):ray('small gable return '+str(j+1),p,['Dark blue on projecting casement','Red lead painted timber'])
    for j,p in enumerate([(530,309),(537,250),(600,162),(622,174)]):
        if j>=2:ray('cut sky '+str(j+1),p,None)
    return r
if __name__=='__main__':
    f=list(map(Path,sys.argv[1:]));roles=['raw','full','lod']if len(f)==4 else['model'];assert len(f)==len(roles)+1
    result={r:test(m,cases())for r,m in zip(roles,f)}
    f[-1].write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    for r,d in result.items():print(r,len(d['cases']),[(s['name'],s['first_hit']and s['first_hit']['material'])for s in d['cases']if not s['passed']])
    sys.exit(int(not all(r['passed']for r in result.values())))
