"""Check the two arch openings, photographed radial joints, staircase and relief on serialized geometry."""
from pathlib import Path
import argparse,sys,runpy,json
import numpy as np
HERE=Path(__file__).absolute().parent
SRC=HERE.parents[2]/'source/precise/changning-great-western-villa-16-arched-entry'
sys.path.insert(0,str(SRC/'source'))
from registration import C
INSPECT=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
def cases():
    rows=[]
    def add(name,o,d,l,m=None,r=None):
        rows.append(dict(name=name,origin=list(map(float,o)),direction=list(map(float,d)),length=l,allowed=m,range_m=r))
    profile=json.loads((SRC/'measurements/vault-profile.json').read_bytes());cx,cz,rx,rz,tilt=profile['conic_parameters'];y=C['outer_front_y_m']
    obs=[r['degrees']for r in profile['radial_mortar_observations']]
    for i,(a,b)in enumerate(zip(obs[:-1],obs[1:])):
        if not 2.25<b-a<4.25:continue
        for j,rad in enumerate([.062,.168]):
            t=np.deg2rad((a+b)/2);x=cx+(rx+rad)*np.cos(t);z=cz+(rz+rad)*np.sin(t)+tilt*np.cos(t)
            add(f'Radial face wedge {i+1}/{j+1}',[x,y-.065,z],[0,1,0],.095,['Salmon facing brick','Dusty red brick','Weathered orange brick','Dark russet brick'],[.047,.066])
        if i>0 and a-obs[i-1]>2.25:
            t=np.deg2rad(a);x=cx+(rx+.080)*np.cos(t);z=cz+(rz+.080)*np.sin(t)+tilt*np.cos(t)
            add(f'Lime joint between radial bricks {i+1}',[x,y-.065,z],[0,1,0],.1,['Pale face mortar'],[.066,.071])
    for i,x in enumerate(np.linspace(-.69,.68,11)):
        for j,z in enumerate([-.80,-.34,.18,.56]):
            add(f'Open through entrance {i+1}/{j+1}',[x,y-.08,z],[0,1,0],.54)
    for i,x in enumerate([-.35,-.16,.00,.18,.35]):
        for j,z in enumerate([-.8,-.45,-.19,.13]):
            add(f'Clear inner arch {i+1}/{j+1}',[x,-.094,z],[0,1,0],.17)
    mats=['Oxide red moulded timber','Red faded door trim','Red frame shadow']
    for i,t in enumerate(np.linspace(.035,np.pi-.035,27)):
        x=(.54+.041)*np.cos(t);z=(.562+.041)*np.sin(t)
        add(f'Moulded rear arch {i+1}',[x,-.095,z],[0,1,0],.13,mats,[.034,.076])
    stair=json.loads((SRC/'measurements/stair-noses.json').read_bytes());rise=stair['conditional_rise_m'];run=stair['conditional_run_m']
    for i,row in enumerate(stair['noses']):
        z=-1.425+(i+1)*rise
        for j,x in enumerate([-.47,-.27,-.057]):
            add(f'Tread {i+1}/{j+1}',[x,.24+i*run+.11,z+.07],[0,0,-1],.11,['Weathered brown stair tread'],[.069,.071])
            add(f'Nosing {i+1}/{j+1}',[x,.24+i*run-.06,z-.013],[0,1,0],.092,['Worn stone stair nosing'],[.040,.047])
    pts=np.array(C['plaque_corners_enu']);vec=pts[1]-pts[0];w=np.linalg.norm(vec);t=vec/w;n=np.cross(t,[0,0,1.]);h=pts[0,2]-pts[3,2]
    for i,u in enumerate([.07,.17,.27,.37,.47,.57,.67,.77,.88]):
        for j,v in enumerate([.06,.22,.36,.49,.66]):
            p=pts[0]+t*(w*u)-[0,0,h*v]
            add(f'Signed stone relief {i+1}/{j+1}',p+n*.083,-n,.14,['Relief plaque from WQL photograph'],[.048,.092])
    for i,u in enumerate([-.91,-.72,.69,.88]):
        add(f'Warm entry paving {i+1}',[u,y+.29,-1.32],[0,0,-1],.15,['Warm grey threshold'],[.104,.106])
    # Low, oblique sight lines previously passed through two accidental holes to the background.
    c=next(view for view in json.loads((SRC/'source/cameras.json').read_bytes()) if view['name']=='brick')
    eye,target=(np.asarray(c[k]) for k in ('eye','target'));distance=np.linalg.norm(target-eye)
    front=(target-eye)/distance;right=np.cross(front,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,front)
    focal=c['width']*distance/c['width_m']
    for py,columns in [(280,[369,374]),(283,[373,379]),(286,[380,386]),(380,[229,253,278]),(390,[217,246,276]),(400,[205,230,257]),(410,[205,221,237])]:
        for px in columns:
            ray=front+right*((px+.5-c['width']/2)/focal)+up*((c['height']/2-py-.5)/focal)
            soffit=py<300
            add(f'Oblique camera ceiling {px},{py}',eye,ray,8.,(['Grey brown vault joint','Dark brick in the vault','Shaded salmon soffit','Muted brick soffit'] if soffit else ['Inner hallway in shade']),[4.0,5.2] if soffit else [6.0,6.8])
    for px,py in [(176,435),(175,443),(173,451),(173,459),(172,467),(171,475)]:
        ray=front+right*((px+.5-c['width']/2)/focal)+up*((c['height']/2-py-.5)/focal)
        add(f'Oblique rear corridor return {px},{py}',eye,ray,12.,['Inner hallway in shade'],[7.0,10.])
    return rows
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('raw','full','lod','output'):ap.add_argument(k,type=Path)
    a=ap.parse_args();c=cases();results={k:INSPECT(getattr(a,k),c)for k in ['raw','full','lod']}
    a.output.write_text(json.dumps(results,ensure_ascii=False,separators=(',',':'))+'\n')
    print(len(c),{k:[x['name']for x in v['cases']if not x['passed']]for k,v in results.items()})
    assert all(v['passed']for v in results.values())
