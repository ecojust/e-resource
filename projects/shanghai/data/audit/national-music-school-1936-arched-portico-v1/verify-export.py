"""Cast through the 1936 entrance arch, its reveals, eave, gallery posts and four tile fields."""
from pathlib import Path
import argparse,json,math,runpy
import numpy as np

HERE=Path(__file__).absolute().parent
SOURCE=HERE.parents[2]/'source/precise/yangpu-national-music-school-1936-arched-portico/source'
d=json.loads((SOURCE/'dimensions.json').read_bytes())
roof=json.loads((SOURCE.parent/'measurements/joint-camera-and-roof.json').read_bytes())
INSPECT=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']

def cases():
    checks=[]
    def ray(name,origin,direction,length,material,limits):
        checks.append(dict(name=name,origin=list(map(float,origin)),direction=list(map(float,direction)),length=length,
            allowed=material if isinstance(material,list)or material is None else [material],range_m=limits))
    def front(name,x,z,mat,interval):
        ray(name,[x,-.35,z],[0,1,0],2.15,mat,interval)
    r=d['clear_width']/2;spring=d['spring'];l=d['wall_left'];right=d['wall_right'];base=d['ground'];h=d['wall_top']
    for k in range(23):
        t=math.pi*(k+.45)/23
        x,z=(r+.075)*math.cos(t),spring+(r+.075)*math.sin(t)
        front('round archivolt '+str(k+1),x,z,'Pale entrance surround',[.271,.286])
    for index,a in enumerate(np.linspace(-.90,.90,13)):
        x=r*a;head=spring+math.sqrt(r*r-x*x)
        for j,(y,mat)in enumerate([(.32,'Music School archival plaster'),(.86,'Low plinth stone')]):
            ray(f'intrados {index+1} at depth {j+1}',[x,y,spring-.25],[0,0,1],2.,mat,[head-spring+.227,head-spring+.26])
        for j,z in enumerate([.34,spring-.64,head-.24]):
            front(f'recessed arch {index+1}-{j+1}',x,z,'Neutral photographic shadow',[1.786,1.805])
    for side in [-1,1]:
        stone='Music School archival plaster'
        for j,z in enumerate([.23,1.46,2.97,4.62,5.88]):
            front(f'light pier {side}/{j}',side*(r+.62),z,stone,[.343,.357])
        front('low pedestal '+str(side),side*(r+.53),base+.25,'Low plinth stone',[.255,.276])
        front('plinth projecting bead '+str(side),side*(r+.53),-.08,'Pale entrance surround',[.231,.246])
    for k,x in enumerate([l+.19,-1.71,-.75,0,.85,1.72,right-.29]):
        front('arch panel above crown '+str(k),x,h-.26,'Music School archival plaster',[.342,.358])
    for j,x in enumerate([l-2.02+.16,l+.02-.16,right-.02+.16,right+2.38-.16]):
        front('portico-side gallery post '+str(j+1),x,2.4,'Gallery post in shade',[.66,.68])
    for j,(a,b) in enumerate([(l-2.02,l+.02),(right-.02,right+2.38)]):
        front('gallery fascia '+str(j+1),(a+b)/2,h-.55,'Gallery post in shade',[.110,.128])
        cx=(a+b)/2
        if j==0:cx=(a+b)/2-.33
        front('dark gallery bay '+str(j+1),cx,h,'Neutral photographic shadow',[.583,.604])
    x0,y0,z=roof['left_front_eave_xyz'];x1,y1,_=roof['right_rear_eave_xyz'];peak=np.array(roof['apex_xyz'])
    corners=np.array([[x0,y0,z],[x1,y0,z],[x1,y1,z],[x0,y1,z]])
    for i,(a,b) in enumerate(zip(corners,np.roll(corners,-1,axis=0))):
        for j,t in enumerate([.15,.33,.58,.79]):
            for k,u in enumerate([.29,.59,.80]):
                surface=(1-t)*((1-u)*a+u*b)+t*peak
                ray(f'tile pitch {i+1}/{j+1}/{k+1}',surface+[0,0,.22],[0,0,-1],.32,
                    ['Grey roof tile','Weathered tile'],[.183,.225])
    return checks
if __name__=='__main__':
    args=argparse.ArgumentParser(description=__doc__)
    for key in ['raw','full','lod','output']:args.add_argument(key,type=Path)
    opts=args.parse_args();picks=cases();report={k:INSPECT(getattr(opts,k),picks)for k in ['raw','full','lod']}
    opts.output.write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
    assert all(v['passed']for v in report.values()),[(k,[c['name']for c in v['cases']if not c['passed']])for k,v in report.items()]
    print(len(picks),'checks per serialized file')
