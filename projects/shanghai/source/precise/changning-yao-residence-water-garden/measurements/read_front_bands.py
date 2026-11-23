"""Recover the band profiles and the pool rim in the original photographs."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent


def on_plane(station, uv, dim, coord):
    k, r, eye = [np.array(station[key]) for key in ('K','R','C')]
    ray = r.T @ np.linalg.solve(k, [*uv,1.])
    return eye + (coord-eye[dim])/ray[dim]*ray


def measure():
    fit=json.loads((HERE/'garden-cameras.json').read_bytes())
    survey=json.loads((HERE/'garden-details.json').read_bytes())
    result={}
    for side in ('back','return'):
        data=survey['bands'][side]
        dim,at=(1,-.10) if side=='back' else (0,fit['corner_x_m']+.10)
        profiles=[]
        for top,bottom in data['bright_ranges_v']:
            profiles.append([float(on_plane(fit['stations']['whb2019'],[data['sample_u'],v],dim,at)[2]) for v in (bottom,top)])
        result[side+'_bands_bottom_to_top']=list(reversed(profiles))
    line_values={}
    y=-fit['eave_projection_m']
    for edge in ('top','dark_soffit'):
        obs=[]
        for name in ('whb2019','garden2017'):
            for point in survey['cap_profiles'][name][edge]:
                obs.append(on_plane(fit['stations'][name],point,1,y))
        xyz=np.asarray(obs)
        slope,intercept=np.polyfit(xyz[:,0],xyz[:,2],1)
        model=intercept+slope*xyz[:,0]
        line_values[edge]={'slope':slope,'intercept':intercept,
                          'rms_height_m':float(np.sqrt(np.mean((model-xyz[:,2])**2)))}
    result['back_roof_edges']=line_values
    added=survey['outer_screen']
    st=fit['stations'][added['station']];x=fit['corner_x_m']+.10
    outer=[on_plane(st,[u,174],0,x)[1]for u in added['y_axis_crop_u']]
    result['outer_screen']={'observed_interval_y':outer,'bands':[]}
    for top,bottom in added['visible_bright_ranges_v']:
        result['outer_screen']['bands'].append([float(on_plane(st,[added['x_sample'],v],0,x)[2])for v in (bottom,top)])
    pool=survey['pool']
    site=np.array([on_plane(fit['stations']['garden2017'],pt,2,pool['rim_z_m'])[:2] for pt in pool['edge_points_px']])
    def residual(v):
        dx=site-v[:2];cs=np.cos(v[4]);sn=np.sin(v[4])
        local=dx@np.array([[cs,-sn],[sn,cs]])
        return np.linalg.norm(local/v[2:4],axis=1)-1
    opt=least_squares(residual,[*site.mean(axis=0),4.5,2.9,0],bounds=([-10,-20,1,1,-3.15],[20,5,15,15,3.15]))
    xo,yo,a,b,angle=opt.x
    result['pool']={'center_xy':[xo,yo],'radii':[a,b],'rotation_rad':angle,'rim_z_m':pool['rim_z_m'],
             'photo_plane_points_xy':site.tolist(),'max_fractional_radial_error':float(np.max(np.abs(residual(opt.x))))}
    return result


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('output',type=Path);args=cli.parse_args()
    args.output.write_text(json.dumps(measure(),ensure_ascii=False,indent=2)+'\n')
