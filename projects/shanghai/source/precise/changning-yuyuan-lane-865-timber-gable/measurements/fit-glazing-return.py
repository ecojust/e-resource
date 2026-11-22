"""Fit three upright glazing edges from four photographed transoms across the two visible faces."""
import json,sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
here=Path(__file__).absolute().parent;sys.path.insert(0,str(here.parent/'source'))
from projection import world,photo,DATA
rows=np.array([[[286,289.8],[301,285],[319,290.5]],[[286,306.8],[301,301.8],[319,305.5]],
               [[286,325.5],[301,320.8],[321,326.3]],[[286,341.8],[301,339.0],[320.5,345.3]]])
def edges(y):
    return np.stack([world(rows[:,i],d)for i,d in enumerate([.12,*y])])
def residual(y):
    values=edges(y)[:,:,1]
    return (values-values.mean(axis=0)).ravel()
def fit():
    result=least_squares(residual,[.12,.42]);v=edges(result.x)
    depths=np.r_[.12,result.x];x=v[:,:,0].mean(axis=1);levels=v[:,:,1].mean(axis=0)
    predicted=np.array([photo([[u,d,z]for u,d in zip(x,depths)])for z in levels])
    return dict(source_sha256=DATA['source_sha256'],observed_transom_pixels=rows.tolist(),assumed_left_setback_m=.12,
                fitted_edges_xy_m=np.column_stack([x,depths]).tolist(),fitted_transom_levels_m=levels.tolist(),
                fitted_pixels=predicted.tolist(),rms_px=float(np.sqrt(np.mean(np.linalg.norm(predicted-rows,axis=2)**2))),
                interpretation='图中左面近于平行墙面，右面向内退。只能从横档和反光读出两面夹角，照片未显示开启机构。')
if __name__=='__main__':
    m=fit();(here/'central-glazing.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(m['fitted_edges_xy_m'],m['rms_px'])
