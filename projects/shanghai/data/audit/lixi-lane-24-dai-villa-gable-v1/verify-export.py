"""First-hit and clear-air checks across the façade, recessed glass, pierced balcony and tile courses."""
import argparse,json,runpy,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).absolute().parent
SRC=HERE.parents[2]/'source/precise/changning-lixi-lane-24-dai-villa-gable'
sys.path.insert(0,str(SRC/'source'))
from registration import wall,plane
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
INSPECT=inspect
def cases():
    tests=[]
    def add(name,o,d,le,m=None,r=None):
        tests.append(dict(name=name,origin=list(map(float,o)),direction=list(map(float,d)),length=le,allowed=m,range_m=r))
    # Centres and radii are taken separately for the three photographed openings.
    glass=['Attic glass in shade','Blue grey glass','Dark reflected glass']
    for i,center in enumerate([-1.48,0.,1.44]):
        for j,x in enumerate([-.37,-.13,.13,.37]):
            for k,z in enumerate([-.14,-.68,-1.28,-1.90]):
                add(f'Pane {i+1}/{j+1}/{k+1}',[center+x,-.029,z],[0,1,0],.18,glass,[.155,.159])
        for k,z in enumerate([-.19,-.62,-1.14,-1.85]):
            add(f'Central wood stile {i+1}/{k+1}',[center,-.030,z],[0,1,0],.11,['Painted green timber'],[.079,.083])
        for j,x in enumerate([-.24,-.119,.11,.23]):
            add(f'Green transom {i+1}/{j+1}',[center+x,-.03,-.37-i*.018],[0,1,0],.11,['Painted green timber'],[.079,.083])
        add(f'Wood at the crown {i+1}',[center,-.025,[.462,.474,.460][i]],[0,1,0],.11,['Painted green timber'],[.063,.067])
    for j,x in enumerate([-2.26,-.73,.72,2.15]):
        for k,z in enumerate([-.2,-.64,-1.06,-1.46,-1.85,.68,.99]):
            add(f'Roughcast pier {j+1}/{k+1}',[x,-.09,z],[0,1,0],.12,['Pebbled grey buff wall','Aggregate warm chip','Aggregate dark chip','Aggregate chalk chip'],[.078,.092])
    H=np.array(json.loads((SRC/'measurements/green-gable-profile.json').read_bytes())['district_to_street_gable_only'])
    for j,(u,v)in enumerate([(182,89),(204,90),(226,91),(250,90),(275,90),(298,91),(325,100),(351,106),(372,120),(390,146),(403,165),
                                   (155,148),(146,179),(136,202),(115,234),(97,252),(76,279),(457,290),(479,311),(500,333),(528,347)]):
        uv=H@[u,v,1];x,z=wall([uv[:2]/uv[2]],-.48)[0]
        if j in (11,14,15):
            add(f'Curved edge flashing {j+1}',[x,-.57,z],[0,1,0],.125,['Grey green edge flashing'],[.031,.035])
        else:add(f'Green gable face {j+1}',[x,-.57,z],[0,1,0],.125,['Weathered green roughcast'],[.089,.091])
    data=json.loads((SRC/'measurements/green-gable-profile.json').read_bytes())
    obs=np.array([[s['u'],s['v']]for s in data['training']]);q=np.c_[obs,np.ones(len(obs))]@H.T
    xz=wall(q[:,:2]/q[:,2,None],-.48);mats=['Clay tile ochre','Clay tile russet','Clay tile faded']
    for i in range(1,len(xz)-1):
        dx,dz=xz[i+1]-xz[i-1];normal=np.array([-dz,0.,dx])/np.hypot(dx,dz)
        for j,y in enumerate([-.25,-.07,.15,.39,.63,.83]):
            start=np.array([xz[i,0],y,xz[i,1]])+.22*normal
            add(f'Clay slope course {i}/{j+1}',start,-normal,.28,mats,[.11,.218])
    foot=plane([[210,557],[353,505],[578,507]],2,-1.675811)
    for i,(p,q,uv,half)in enumerate(zip(foot[:-1],foot[1:],[[285,575],[458,548]],[.443,.345])):
        origin=(p+q)/2;origin[2]=0;t=(q-p)/np.linalg.norm(q-p);n=np.array([t[1],-t[0],0.])
        eye=np.array([-2.6193057694550306,-14.130630907248808,-6.034448476676045])
        from registration import P
        ray=np.linalg.solve(P[:,:3],[*uv,1]);hit=eye+ray*((origin-eye)@n/(ray@n));c=(hit-origin)@t
        def face(name,x,z,mat=None,bounds=None,limit=.34):
            add(f'{name} face {i+1} {x:.3f} / {z:.3f}',origin+t*x+[0,0,z]+n*.12,-n,limit,mat,bounds)
        for z in np.linspace(-2.42,-1.86,7):
            for x in [-.83,.86]:face('Solid cheek',x,z,['Weathered cream parapet'],[.115,.125])
        for x in np.linspace(-.95,.93,15):face('Coping',x,-1.653,['Pale coping stone'],[.056,.076])
        for x in np.linspace(-.92,.92,13):face('Bottom bead',x,-2.550,['Pale coping stone'],[.081,.106])
        cz=(-2.5727+.055-1.6758-.065)/2
        for sign in [-1,1]:
            for l in [.31,.50,.64]:
                for d in [-1,1]:face('Saltire',c+sign*l*half,cz+sign*d*l*.393,['Pale coping stone','Cream cast fret'],[.108,.136])
            for ratio in [.39,.56]:
                face('Open vertical quarter',c,cz+sign*ratio*.386)
                face('Open horizontal quarter',c+sign*ratio*half,cz)
        for off in [-.845,.845]:
            face('Solid circle side',c+half*off,cz,['Pale coping stone','Cream cast fret'],[.112,.139])
    for j,z in enumerate(np.linspace(-3.22,1.04,14)):
        add(f'Round rainpipe {j+1}',[2.31,-.24,z],[0,1,0],.13,['Pale drainpipe','Pipe collar'],[.065,.084])
    return tests
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('raw','full','lod','output'):ap.add_argument(n,type=Path)
    a=ap.parse_args();tests=cases();results={k:inspect(getattr(a,k),tests)for k in ['raw','full','lod']}
    a.output.write_text(json.dumps(results,ensure_ascii=False,separators=(',',':'))+'\n')
    print(len(tests),{k:[r['name']for r in v['cases']if not r['passed']]for k,v in results.items()});assert all(r['passed']for r in results.values())
