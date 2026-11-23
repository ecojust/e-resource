"""Solve the projecting school-name board against three photographs on the fixed post registration."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

HERE=Path(__file__).resolve().parent

def solve():
    original=json.loads((HERE/'gate-original-pixels.json').read_text())
    stations=json.loads((HERE/'registered-gate.json').read_text())['stations']
    # Exclude the bottom left corner of each board, and leave all the posts and optics fixed.
    def residual(v,receipt=False):
        half,top,bottom,yt,yb,center=v
        corners=np.array([[center-half,yt,top,1],[center+half,yt,top,1],[center+half,yb,bottom,1],[center-half,yb,bottom,1]])
        errors=[];rows=[]
        for name,st in stations.items():
            if name not in original:continue
            proj=corners@np.array(st['P']).T
            pix=proj[:,:2]/proj[:,2,None]
            diff=pix-np.array(original[name]['plaque'])
            errors.extend((diff[:3]/({'commons-2006':4.0,'school-front':2.2,'school-postcard':3.4}[name])).ravel())
            rows.append(dict(station=name,all_native_errors_px=np.round(np.linalg.norm(diff,axis=1),2).tolist(),heldout='fourth / lower left',projected=np.round(pix,2).tolist()))
        if receipt:return rows
        return errors
    result=least_squares(residual,[1.12,3.97,3.1,-.45,-.14,0],loss='huber',f_scale=1.5)
    p=dict(zip(['half_width','top','bottom','top_y','bottom_y','center_x'],result.x))
    (HERE/'plaque-registration.json').write_text(json.dumps(dict(front=p,residuals=residual(result.x,True)),indent=2)+'\n')
if __name__=='__main__':solve()
