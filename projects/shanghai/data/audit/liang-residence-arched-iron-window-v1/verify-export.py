"""Check actual foreground iron, the openings through it, the wood surround, glazing overlaps and brick courses."""
from pathlib import Path
import json,runpy,sys,numpy as np
HERE=Path(__file__).absolute().parent
SRC=HERE.parents[2]/'source/precise/jingan-liang-residence-arched-iron-window'
C=json.loads((SRC/'measurements/window-camera.json').read_bytes());E=np.array(C['eye_xyz']);INV=np.linalg.inv(np.array(C['pinhole_3x4'])[:,:3]);W=C['nominal_outer_frame_width_m'];H=C['derived_outer_frame_height_m']
PROBES=json.loads((SRC/'measurements/independent-window-apertures.json').read_bytes())
check=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
def cases():
    rows=[]
    def add(name,d,end,allow):
        d=d/np.linalg.norm(d);rows.append(dict(name=name,origin=E.tolist(),direction=d.tolist(),length=float((end-E[1])/d[1]),allowed=allow,range_m=None))
    def rect(name,p,end,allow):
        x,y=p;add(name,np.array([(x/480-.5)*W,0,(1-y/875)*H])-E,end,allow)
    for p in PROBES['samples']:
        for type in ['opening','iron']:
            rect(p['feature']+' '+type,p[type+'_xy_px'],.035,['Oxide on the window grille'] if type=='iron' else None)
    interior=['Oxide on the window grille','Weathered red timber frame','Dark wood in the glazing rebate','Smoked umber window glass','Dull grey blue window glass','Light on rubbed window beads','Timber seen through the opening']
    for y in [52.4,54.1,55.7]:
        for x in [48,70,91,132,166,193,216,255,282,313,349,370,403,430]:
            rect(f'upper rebate closes the view {x}/{y}',[x,y],.21,interior)
    for j,p in enumerate([[43,641],[153,642],[240,642],[331,642],[432,642],[29,303],[450,503]]):
        rect('wood surround '+str(j+1),p,.23,['Weathered red timber frame','Dark wood in the glazing rebate','Light on rubbed window beads'])
    wall=['Painted ivory courtyard brick','Pale pink whitewash','Fine pale joints in the garden wall','Exposed red band on courtyard brick']
    for j,p in enumerate([[89,210],[91,260],[98,337],[110,424],[114,505],[416,235],[416,330],[421,414],[411,504],[100,549]]):
        add('continuous courtyard masonry '+str(j+1),INV@np.r_[p,1.],.22,wall)
    return rows
if __name__=='__main__':
    f=list(map(Path,sys.argv[1:]));roles=['raw','full','lod']if len(f)==4 else['model'];assert len(f)==len(roles)+1
    r={k:check(p,cases())for k,p in zip(roles,f[:-1])};f[-1].write_text(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
    print({k:(len(v['cases']),[(c['name'],c['first_hit']and c['first_hit']['material'])for c in v['cases']if not c['passed']])for k,v in r.items()});sys.exit(int(not all(v['passed']for v in r.values())))
