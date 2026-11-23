"""Bundle the two published garden views with their shared glazed head height."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent


def camera(eye, aim, focal, size, roll=0):
    forward = np.asarray(aim) - eye
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0., 0., 1.])
    right /= np.linalg.norm(right)
    down = np.cross(forward, right)
    rot = Rotation.from_matrix(np.vstack((right, down, forward))).as_rotvec()
    return [*eye, *rot, focal]


def unpack(params, size):
    eye = np.array(params[:3])
    r = Rotation.from_rotvec(params[3:6]).as_matrix()
    k = np.array([[params[6], 0, (size[0]-1)/2], [0, params[6], (size[1]-1)/2], [0, 0, 1]])
    return k, r, eye


def solve(book):
    rows = book['axes']
    stations = list(book['photos'])
    dims = [book['photos'][name]['size'] for name in stations]
    head, sill = book['opening_head_m'], book['sill_m']
    var = [r['seed'] for r in rows if r['key'] != 'court-white-left']
    n = len(var)
    def structure(p):
        out = {}
        it = iter(p)
        for r in rows:
            out[r['key']] = 0 if r['key'] == 'court-white-left' else next(it)
        return out
    series = []
    for station, size, eye, focal in zip(stations, dims, [[2., -16., 1.55],[3.7,-24.,1.65]], [420.,410.]):
        series.extend(camera(eye, [1.0, -0.4, 1.35], focal, size))
    x0 = [*var, -2., 3.00, .47, .65, *series]
    def residual(p, report=False):
        ax = structure(p[:n]); xcorner, roofz, lip, depth = p[n:n+4]
        errs,records = [],[]
        for i,(name, size) in enumerate(zip(stations,dims)):
            k,r,c = unpack(p[n+4+7*i:n+11+7*i], size)
            def observe(world,uv,sigma,label):
                q = k@r@(np.asarray(world)-c)
                pred=q[:2]/q[2];err=pred-uv
                errs.extend(err/sigma);records.append({'station':name,'target':label,'world_m':world,'observed_px':uv,
                    'projected_px':pred.tolist(),'residual_px':float(np.linalg.norm(err))})
            for row in rows:
                u=ax[row['key']]
                xy=[u,0.] if row['plane']=='back' else [xcorner,u]
                for h,pair,z in zip(['head','sill'],row[name],[head,sill]):
                    if pair is not None:observe([*xy,z],pair,row.get('uncertainty_px',2.5),row['key']+'/'+h)
            a=book['corner_eave'][name]
            for z,uv,label in [(roofz,a[0],'cap'),(roofz-lip,a[1],'soffit')]:
                observe([xcorner+depth,-depth,z],uv,3.2,'reentrant-canopy/'+label)
            errs.extend([(c[2]-1.62)/.35,(p[n+10+i*7]-[445,465][i])/170])
        errs.extend([(depth-.68)/.27,(lip-.44)/.15,(xcorner+2.1)/1.2,(roofz-3.05)/.55])
        return records if report else errs
    result=least_squares(residual,x0,loss='soft_l1',f_scale=2.,max_nfev=1700)
    p=result.x; rec=residual(p,True)
    out={'axes_m':structure(p[:n]),'corner_x_m':p[n],'eave_top_m':p[n+1],
        'eave_face_height_m':p[n+2],'eave_projection_m':p[n+3],'opening_head_m':head,'sill_m':sill,'stations':{}}
    for i,(name,size) in enumerate(zip(stations,dims)):
        k,r,c=unpack(p[n+4+7*i:n+11+7*i],size)
        z=np.array([d['residual_px']for d in rec if d['station']==name])
        out['stations'][name]={'size':size,'K':k.tolist(),'R':r.tolist(),'C':c.tolist(),'P':(k@np.column_stack((r,-r@c))).tolist(),
                              'median_residual_px':np.median(z),'max_residual_px':np.max(z),'observations':len(z)}
    out['records']=rec
    return out


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('output',type=Path)
    args=cli.parse_args()
    data=json.loads((HERE/'garden-observations.json').read_bytes())
    args.output.write_text(json.dumps(solve(data),ensure_ascii=False,indent=2)+'\n')
