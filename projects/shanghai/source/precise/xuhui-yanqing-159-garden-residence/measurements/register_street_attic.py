"""Test the high and low attic interpretations on independent street images.

Fit only the centres of the head and sill of three lower main windows. Use
the documented rectilinear field of view and wall axes to recover a camera.
The higher attic window is held out throughout the optimisation.
"""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).resolve().parent
DATA=json.loads((HERE/'north-street-window-intersections.json').read_text())
GARDEN_BAYS={'A':(1.800,3.07,4.24),'B':(4.845,2.66,3.82),'C':(7.36,2.63,3.74)}


def fit(i):
    view=DATA['views_in_order'][i];w,h=view['image_size_px']
    f=.5*w/np.tan(np.deg2rad(view['rectilinear_azimuth_pitch_hfov_deg'][2]/2))
    k=np.array([[f,0,w/2],[0,f,h/2],[0,0,1.]])
    world,obs=[],[]
    for kbay,(y,s,t) in GARDEN_BAYS.items():
        for key,z in [('head',t),('sill',s)]:
            px=DATA['point_observations'][kbay+'_'+key]['pixels_by_view'][i]
            if px is not None:
                world.append([0.,y,z]);obs.append(px)
    world=np.array(world);obs=np.asarray(obs)
    # A street camera looks towards -X, +Y runs to the right, +Z upwards.
    initial=np.array([[0,1.,0],[0,0,-1.],[-1.,0,0]])
    def proj(v,xyz):
        r=Rotation.from_rotvec(v[:3]).as_matrix()
        q=(k@r@(np.asarray(xyz)-v[3:]).T).T
        return q[:,:2]/q[:,2,None]
    def residual(v):
        return (proj(v,world)-obs).ravel()
    results=[]
    for cy in [-9,0,7,18]:
        opt=least_squares(residual,[*Rotation.from_matrix(initial).as_rotvec(),8.,cy,1.3],
                          loss='soft_l1',f_scale=2,max_nfev=900)
        if opt.x[3]>.5:results.append(opt)
    best=min(results,key=lambda c:c.cost)
    def xy(y,z):return proj(best.x,[[0,y,z]])[0]
    top=DATA['point_observations']['front_high_vent_top']['pixels_by_view'][i]
    sill=DATA['point_observations']['front_high_vent_sill']['pixels_by_view'][i]
    if not top or not sill:return None
    v=best.x
    def attic(z,u=1.16):
        rt=xy(u,z+1.03);rb=xy(u,z+.06)
        return np.array([rt,rb])
    # Fit one common vertical displacement and one lateral shift of the pair;
    # also show the heights without the lateral adjustment.
    picked=np.array([top,sill])
    solution=least_squares(lambda pair:(attic(*pair)-picked).ravel(),[5.4,1.16],bounds=([4.5,.4],[6.5,2.0]))
    solution_z=least_squares(lambda q:(attic(q[0])-picked).ravel(),[5.4])
    def flexible_height(v):
        y,z0,z1=v
        return (np.asarray([xy(y,z1),xy(y,z0)])-picked).ravel()
    free=least_squares(flexible_height,[1.5,5.33,6.1])
    adopted=np.asarray([xy(1.49,6.11),xy(1.49,5.33)])
    model={}
    for title,base in [('street_absolute',5.82),('same_face_ratio',5.27)]:
        model[title]={'base':base,'corner_distances_px':np.linalg.norm(attic(base)-picked,axis=1).round(2).tolist(),
                      'vertical_residuals_px':(attic(base)-picked)[:,1].round(2).tolist()}
    rot=Rotation.from_rotvec(v[:3]).as_matrix();projmat=k@rot@np.column_stack([np.eye(3),-v[3:]])
    return dict(view=i,source_sha256=view['projection_jpeg_sha256'],calibrating_points=len(obs),
                fitted_main_window_errors_px=np.linalg.norm(proj(v,world)-obs,axis=1).round(2).tolist(),
                comparison=model,fitted_base_and_centre=solution.x.tolist(),
                independent_vent_centre_sill_head=free.x.tolist(),
                adopted_vent_centre_sill_head=[1.49,5.33,6.11],
                adopted_vent_distances_px=np.linalg.norm(adopted-picked,axis=1).tolist(),
                base_holding_measured_centre=solution_z.x[0],P_pre_metric=projmat.tolist(),
                measured_top_and_sill_xy=picked.tolist())
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    args=parser.parse_args();rows=[r for i in [0,1,3] if (r:=fit(i))]
    print([(r['view'],r['fitted_base_and_centre'],r['comparison'])for r in rows])
    args.output.write_text(json.dumps(dict(method=__doc__,views=rows),indent=2)+'\n')
