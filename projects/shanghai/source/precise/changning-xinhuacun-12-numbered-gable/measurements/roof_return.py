"""Transfer the later photograph's far gable and both early photographs' west chimney to the local model."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
HERE=Path(__file__).absolute().parent
cams=json.loads((HERE/'three-photographic-stations.json').read_bytes())
def p(q,xyz):
    v=np.asarray(q['P'])@[*xyz,1];return v[:2]/v[2]
def rect(q,uv,x):
    P=np.asarray(q['P']);B=np.column_stack([P[:,1],P[:,2],P[:,3]+x*P[:,0]]);v=np.linalg.solve(B,[*uv,1]);return (v[:2]/v[2]).tolist()
controls={'numbered-front':[448,163],'archival-front':[86.7,66.2]}
def residual(v):
    return np.r_[*(x for k,uv in controls.items()for x in (p(cams[k],v)-uv)/[2.5,3.5]),(v[1]-1.9)/.85]
chim=least_squares(residual,[-.45,1.9,10.39],loss='soft_l1').x
marks={'rear-ridge':[814,390],'near-eave-obscured':[779,466],'far-eave-see-edge':[848,509],'tile-slope-independent':[792.65,416.18]}
result=dict(west_chimney_center_xyz=chim.tolist(),two_chimney_checks={k:dict(read=uv,projected=p(cams[k],chim).round(3).tolist())for k,uv in controls.items()},far_gable_probe_plane_x=7.4,far_gable_yz_at_observed_pixels={k:dict(uv=uv,yz=rect(cams['garden-oblique'],uv,7.4))for k,uv in marks.items()},
            modelling_basis='The near roof slope and ridge are directly visible. The lower ends are partly obscured by the long eaves and trees. Both eaves use a level approximation and the rear roof beyond the photographed strip is omitted.')
(HERE.parent/'source/roof-end.json').write_text(json.dumps(result,indent=2)+'\n')
