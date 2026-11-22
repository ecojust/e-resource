"""Refit two camera stations without using the observed upper endpoint of the flagstaff."""
from pathlib import Path
import argparse,json,sys
import numpy as np
from scipy.optimize import least_squares,minimize_scalar
HERE=Path(__file__).resolve().parent
DATA=json.loads((HERE/'photo-observations.json').read_bytes())
def summary(project):
    measurements=project/'source/precise/jingan-bank-of-communications-warehouse-guangfu-riverfront/measurements'
    sys.path.insert(0,str(measurements));from fit_terrace_photo import project as image
    layout=json.loads((measurements/'riverfront-layout.json').read_bytes())
    roof=json.loads((measurements/'roof-terrace-fit.json').read_bytes())
    mat=np.array(roof['plan_pixel_to_xy']);deck=layout['roof_deck_z']
    axis=[.01,1.02];tip_z=27.0
    def height(cam,uv,relative):
        def err(z):return np.linalg.norm(image(cam,np.array([[*axis,z-relative]]))[0]-uv)
        return float(minimize_scalar(err,bounds=(22,34),method='bounded').x)
    def trunc(v):return np.round(v,5).tolist()
    data=DATA['controls_34']
    world=[];screen=[];noise=[]
    bays={b['bay']:b for b in layout['bays']}
    for name,u,v1,v0 in data['upper_window_columns_head_sill_uv']:
        o=next(r for r in layout['openings']if r['key']==name+'-F4');b=bays[name]
        x=(o['x0']+o['x1'])/2; y=np.interp(x,[b['x0'],b['x1']],[b['y0'],b['y1']])
        for z,v,s in [(o['z1'],v1,1.4),(o['z0'],v0,1.8)]:
            world.append([x,y,z]);screen.append([u,v]);noise.append(s)
    for xy,uv,s in zip([mat@[739,252,1],layout['outer_ends_xy'][1],layout['outer_ends_xy'][0]],data['coping_uv'],[2.4,1.6,2.3]):
        world.append([*xy,layout['bay_wall_top']]);screen.append(uv);noise.append(s)
    world=np.array(world);screen=np.array(screen);noise=np.array(noise)
    def fit34(pts,mask,start):
        def err(q):
            return np.r_[((image(q,world[mask])-pts[mask])/noise[mask,None]).ravel(),
                         (q[6]-850)/500,(q[7]-540)/100,(q[8]-360)/100,q[5]/.03]
        return least_squares(err,start,max_nfev=900).x
    every=np.ones(len(world),bool);q=fit34(screen,every,[70,-80,40,-.6,-.2,0,920,540,360])
    at34=image(q,np.array([[*axis,tip_z]]))[0];u34=np.array(data['tip_uv']);z34=height(q,u34,0)
    rng=np.random.default_rng(644);family=[]
    for i in range(24):
        mask=every.copy();mask[[i%20,(i+5)%20]]=False
        q2=fit34(screen+rng.normal(0,.6,(len(world),2))*noise[:,None],mask,q)
        family.append(height(q2,u34+rng.normal(0,[.7,1.5]),0))
    s34={'controls':len(world),'camera_xyz_yaw_pitch_roll_f_cx_cy':trunc(q),'control_residual_px':trunc(np.linalg.norm(image(q,world)-screen,axis=1)),'heldout_tip_observed':trunc(u34),'tip_projected_at_27m':trunc(at34),'tip_z_m':z34,'perturbation_interval_05_95':trunc(np.quantile(family,[.05,.95]))}
    data=DATA['controls_39'];corn=np.c_[data['pavilion_corners_plan_uv'],np.ones(2)]@mat.T
    pts=np.array(data['floor_uv']+data['roof_uv']+[data['axis_floor_uv']])
    def fit39(focal):
        def err(p):
            scene=np.r_[np.c_[corn,[0,0]],np.c_[corn,[p[9],p[9]]],[[*axis,0]]]
            return np.r_[((image(p[:9],scene)-pts)/np.array([4,4,1,1,2])[:,None]).ravel(),(p[2]-1.55)/.4,p[5]/.01,(p[7]-432)/80,(p[8]-335)/80,(p[6]-focal)/250,(p[9]-6.61)/.45]
        return least_squares(err,[34,25,1.52,-1.62,0,0,focal,431,350,6.6],max_nfev=2500).x
    q39=fit39(650)[:9];u39=np.array(data['tip_uv'])
    zs=[height(fit39(p)[:9],u39,deck)for p in (440,650,850)]
    s39={'camera_xyz_yaw_pitch_roll_f_cx_cy':trunc(q39),'heldout_tip_observed':trunc(u39),'tip_projected_at_27m':trunc(image(q39,np.array([[*axis,tip_z-deck]]))[0]),'tip_z_m':height(q39,u39,deck),'camera_prior_sensitivity_m':trunc([min(zs),max(zs)])}
    cam38=np.array(roof['camera_xyz_yaw_pitch_roll_f_cx_cy']); u38=np.array(DATA['controls_38']['native_shaft_top_uv'])
    re38=image(cam38,np.array([[*axis,tip_z-deck]]))[0]
    s38={'fixed_unmodified_terrace_camera':trunc(cam38),'tip_observed_uv':trunc(u38),'tip_projected_at_27m':trunc(re38),'residual_uv_px':trunc(re38-u38),'tip_height_equivalent_at_axis_m':height(cam38,u38,deck),'note_zh':'露台相机以地坪和扶手的近水平视线为主。杆顶在此相机上有约21像素的纵向差值。'}
    def z(v):
        h=738.5-v
        return .04040596*h/(1+.00012320*h)
    s16={'crown_front_plane_m':z(DATA['controls_16']['front_crown_uv'][1]),'tip_equivalent_front_plane_m':z(DATA['controls_16']['tip_uv'][1]),'interpretation_zh':'正照中桅杆与前山墙同轴；后退的杆顶压至山墙平面时读数偏低。'}
    return dict(station_34=s34,station_39=s39,station_38=s38,station_16=s16,model_tip_m=tip_z,reported_height_range_m=[26.5,27.5],deck_m=deck,axis_xy=axis)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('project',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    a.output.write_text(json.dumps(summary(a.project),ensure_ascii=False,indent=2)+'\n')
