"""Check the actual exterior fabric in each exported mesh, including all 51 shallow room and eastern stair apertures."""
from pathlib import Path
import json,runpy,sys
import numpy as np
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/jingan-jkk-apartments-changle-street-front/source'
sys.path.insert(0,str(SOURCE))
from jkk_street_fabric import LAYOUT,STEEL,GLASSES,MATERIAL,STONE,BAND,PEACH
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
def rays():
    checks=[]
    def add(name,x,y,z,expected,dist):
        checks.append(dict(name=name,origin=[x,y,z],direction=[0,1,0],length=dist+.018,allowed=expected,range_m=[dist-.006,dist+.006]))
    for row in LAYOUT['openings']+LAYOUT['east_stair']:
        x0,x1,y,z0,z1=[row[k]for k in ('left','right','wall_y','bottom','top')]
        name=row['key'];w=x1-x0;h=z1-z0
        add(name+' left jamb',x0+.021,y+.014,z1-.21,[STEEL],.091)
        add(name+' right jamb',x1-.023,y+.014,z1-.33,[STEEL],.091)
        add(name+' sill',x0+.22,y-.18,z0-.034,[STONE],.105)
        for i in range(row['columns']):
            x=x0+.044+(i+.5)*(w-.088)/row['columns']
            add(name+f' high pane {i+1}',x,y+.014,z1-.10,GLASSES,.151)
            add(name+f' lower pane {i+1}',x,y+.014,z0+.12,GLASSES,.151)
    for x0,x1,y in LAYOUT['faces_x_y']:
        x=x0+.22
        for z in (3.68,7.05,10.964):
            add(f'Raised grey band {x:.2f} {z:.2f}',x,y-.31,z,[BAND],.265)
        add(f'Rendered pier {x:.2f}',x,y-.31,9.0,[MATERIAL],.31)
    return checks
if __name__=='__main__':
    results={role:inspect(Path(path),rays())for role,path in zip(('raw','full','lod'),sys.argv[1:4])}
    Path(sys.argv[4]).write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    for role,r in results.items():print(role,len(r['cases']),[(v['name'],(v['first_hit']or {}).get('material'))for v in r['cases']if not v['passed']])
    sys.exit(int(not all(r['passed']for r in results.values())))
