"""Trace the front wall, the lower lights, boundary fittings and several rolled tile crests in each real export."""
import json,sys,runpy
from pathlib import Path
import numpy as np
here=Path(__file__).resolve().parent
source=here.parents[2]/'source/precise/huangpu-shaanxi-191-197-residential-front/source'
sys.path.insert(0,str(source))
from house_fabric import SURVEY,BRICKS,TILES,LEAD,MATERIAL,FASCIA,FRAME,LIGHT,STONE
from west_photo_plane import on_wall
from court_wall import DATA,PIER,PANEL,BELT,IRON
inspect=runpy.run_path(here.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']

def probes():
    rows=[]
    def test(name,origin,dir,dist,mats,tol=.012):
        rows.append(dict(name=name,origin=origin,direction=dir,length=dist+tol+.02,range_m=[dist-tol,dist+tol],allowed=mats))
    for p in SURVEY['roughcast_samples']:
        x,_,z=on_wall(*p['center_px'])
        test('Photographed sand finish '+str(p['center_px']),[x,-.8,z],[0,1,0],.8,[MATERIAL])
    for i,w in enumerate(SURVEY['lower_windows'],1):
        l,r,b,t=[w[k] for k in ('left','right','bottom','top')];dw=r-l
        for j in range(6):
            test(f'Lower sash {i} light {j+1}',[l+dw*(j+.5)/6,-.9,b+(t-b)*.68],[0,1,0],1.057,[LIGHT])
        for j in (2,4):
            test(f'Lower sash {i} major stile {j}',[l+dw*j/6,-.9,b+(t-b)*.60],[0,1,0],1.015,[FRAME])
        for j in range(7):
            count=round((r-l+.278)/.065);pitch=(r-l+.278)/count
            xx=l-.139+pitch*(j*3+.5)
            test(f'Lower sash {i} soldier head {j}',[xx,-.8,t+.057],[0,1,0],.778,BRICKS)
    z=np.mean(SURVEY['envelope']['string_course_z_m'])
    for x in (-4.2,-2.1,-.2,1.8,3.5):
        test('Horizontal weathering band '+str(x),[x,-1.,z],[0,1,0],.922,[STONE])
    x=on_wall(965,1253)[0]
    test('North rainwater pipe below the eaves',[x-.044,-1.,6.451],[0,1,0],.847,[LEAD],.012)
    y=DATA['front_y_m']
    for i,p in enumerate(DATA['piers'],1):
        x=on_wall(p['centre'],p['shoulder'],y)[0]
        test(f'Boundary pier {i}',[x,-3.,1.16],[0,1,0],3.+y,[PIER],.012)
    top=np.mean([on_wall(u,v,y)[2] for u,v in DATA['wall_top_sample']])
    for u in (860,1065,1345,1935,2133,2345,2700,2865):
        x=on_wall(u,1880,y)[0]
        test('Boundary wall coping '+str(u),[x,-3.,top-.012],[0,1,0],3.+y+.032,[BELT])
        test('Boundary dark panel '+str(u),[x,-3.,top-.59],[0,1,0],3.+y+.062,[PANEL])
    env=SURVEY['envelope'];l,r=env['wall_ends_x_m'];xmin=l-.82;xmax=r+.51
    count=round((xmax-xmin)/.188)
    front=env['eaves_front_y_m'];back=env['represented_rear_y_m'];low=np.mean(env['eaves_front_z_m']);high=np.mean(env['upper_z_m'])
    for j in (1,3,6):
        y=front+(j+.45)*(back-front)/8
        z=low+(high-low)*(y-front)/(back-front)
        for i in (2,13,26,39,52,61):
            x=xmin+(i+.5)*(xmax-xmin)/count
            test(f'Tile crest row {j} channel {i}',[x,y,z+.32],[0,0,-1],.240,TILES,.021)
    return rows

if __name__=='__main__':
    cases=probes();out={}
    for role,path in zip(('raw','full','lod'),sys.argv[1:4]):
        out[role]=inspect(Path(path),cases)
    Path(sys.argv[4]).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print({k:[c['name'] for c in v['cases'] if not c['passed']] for k,v in out.items()})
    sys.exit(int(not all(r['passed']for r in out.values())))
