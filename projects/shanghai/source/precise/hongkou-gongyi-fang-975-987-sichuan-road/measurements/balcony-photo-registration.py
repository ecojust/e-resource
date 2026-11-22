"""Cross-check the two balcony levels from the oblique 2018 and restored street views."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

HERE=Path(__file__).resolve().parent


def apply(H, xy):
    q=np.c_[xy,np.ones(len(xy))]@H.T
    return q[:,:2]/q[:,2,None]


def fit(xy,uv):
    rows=[]
    for (x,y),(u,v) in zip(xy,uv):
        rows.extend([[x,y,1,0,0,0,-u*x,-u*y,-u],[0,0,0,x,y,1,-v*x,-v*y,-v]])
    h=np.linalg.svd(rows)[2][-1].reshape(3,3)
    def matrix(params):return np.r_[params,1].reshape(3,3)
    p=least_squares(lambda v:(apply(matrix(v),xy)-uv).ravel(),
                    (h/h[2,2]).ravel()[:8],loss='soft_l1',f_scale=2.)
    return matrix(p.x)


def register():
    data=json.loads((HERE/'balcony-photo-traces.json').read_bytes())['registration']
    layout=json.loads((HERE.parent/'source/front-layout.json').read_bytes())
    edges=layout['bay_edges']
    cap=.235*np.median(np.diff(edges))
    results=[]
    for name,axes,test in [('chapter_06',list(range(10)),[1,4,6,8]),
                           ('chapter_15',list(range(5,10)),[6,8])]:
        xy=[];observed=[];split=[];tags=[]
        for k,level in enumerate(['lower','upper']):
            z=layout['balcony_z'][k]+cap
            for j,uv in zip(axes,data[name][level+'_cap_centres']):
                xy.append([edges[j],z]);observed.append(uv);split.append(j not in test)
                tags.append(f'{level} cap {j+1}')
        xy,observed,split=map(np.array,(xy,observed,split))
        h=fit(xy[split],observed[split])
        uv=apply(h,xy);err=np.linalg.norm(uv-observed,axis=1)
        readings=[dict(feature=tag,image=observed[i].tolist(),projected=uv[i].round(3).tolist(),
                       reference='fit' if split[i] else 'held out',residual_px=float(err[i]))
                  for i,tag in enumerate(tags)]
        if name=='chapter_15':
            for k,level in enumerate(['lower','upper']):
                q=np.column_stack(([edges[i] for i in axes],np.full(len(axes),layout['balcony_z'][k])))
                p=apply(h,q)
                for i in range(len(axes)):
                    uv0=data[name][level+'_floor_front_foot'][i]
                    readings.append(dict(feature=f'{level} deck at pier {axes[i]+1}',image=uv0,
                                         projected=p[i].round(3).tolist(),reference='independent deck edge',
                                         residual_px=round(float(np.linalg.norm(p[i]-uv0)),3)))
        results.append(dict(image=name,plane='rail-pier front face, X right, Z up',
                            xz_to_image=h.tolist(),heldout_median_px=float(np.median(err[~split])),
                            heldout_max_px=float(err[~split].max()),readings=readings))
    return results


if __name__=='__main__':
    out={'scope':'Independent pier bearings and projected height. The two homographies apply to visible pier fronts and deck edges. Depth is estimated from the oblique views.',
         'photos':register()}
    (HERE/'balcony-photo-registration.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    for r in out['photos']:
        print(r['image'],r['heldout_median_px'],r['heldout_max_px'])
