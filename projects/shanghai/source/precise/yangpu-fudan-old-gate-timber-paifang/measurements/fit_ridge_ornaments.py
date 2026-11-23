"""Triangulate the two pale ornaments, which sit inside the ends of the long dark ridge."""
from pathlib import Path
import json,numpy as np
from scipy.optimize import least_squares
HERE=Path(__file__).resolve().parent
def solve():
    stations=json.loads((HERE/'four-gate-stations.json').read_bytes())['stations']
    points={'commons-2006':[(489,210),(1084,282),(501,161),(1075,228)],'school-front':[(124,43),(304,43),(127,29),(299,29)],'editorial-reverse':[(626,118),(207,117),(614,81),(215,79)]}
    def residual(v,full=False):
        x,y,z,h,tip_in=v;out=[];rows={}
        xyz=np.array([[-x,y,z,1],[x,y,z,1],[-x+tip_in,y,z+h,1],[x-tip_in,y,z+h,1]])
        for k,uv in points.items():
            proj=xyz@np.array(stations[k]['P']).T;delta=proj[:,:2]/proj[:,2,None]-uv
            if full:rows[k]={'inputs':uv,'errors_px':np.linalg.norm(delta,axis=1).round(2).tolist()}
            out.extend((delta/({'commons-2006':4,'school-front':2.0,'editorial-reverse':4.0}[k])).ravel())
        return rows if full else out
    opt=least_squares(lambda v:residual(v),[2.6,0.,5.13,.39,.07],loss='soft_l1')
    out=dict(parameters=dict(zip(['half_spacing','y','z_foot','height','inward_tip'],opt.x)),control=residual(opt.x,True),notes='Four independent readings per image: image-left and right foot plus upper inward horn, reversing point order on the back view. The ends of the longer dark ridge are different landmarks.')
    (HERE/'ridge-ornaments.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':solve()
