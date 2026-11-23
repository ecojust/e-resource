"""Fit an approximate interior photograph to the conditional gallery, using a separate group of held-out pixels."""
import json
import math
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

HERE=Path(__file__).resolve().parent
OUTPUT=HERE/'auditorium-station.json'
FRAME=(850,567)
# Named readings on Ctny's 2017 interior photograph at a reduced working resolution.
# X/Y of the rear gallery and seats are conditional model dimensions.
def projection(values):
    x,y,z,yaw,pitch,roll,f=values
    ca,sa=math.cos(yaw),math.sin(yaw)
    cp,sp=math.cos(pitch),math.sin(pitch)
    forward=np.array([sa*cp,-ca*cp,sp])
    right=np.array([-ca,-sa,0.]);up=np.cross(right,forward)
    cr,sr=math.cos(roll),math.sin(roll)
    u=cr*right+sr*up;v=sr*right-cr*up
    rotation=np.vstack((u,v,forward))
    k=np.array([[f,0,(FRAME[0]-1)/2],[0,f,(FRAME[1]-1)/2],[0,0,1.]])
    return k@rotation@np.column_stack((np.eye(3),-np.array([x,y,z])))
def project(p,point):
    v=p@[*point,1.]
    return v[:2]/v[2]
vp=np.cross(np.cross([536.1,400,1],[479.25,550,1]),np.cross([617.3,400,1],[697.1,550,1]));vp=vp[:2]/vp[2]
def obs(v):
 y,cap,lower,bay,rect,s,xe,xw,back=v[7:]
 return [
 ('cap',[9.91,y,cap],[179,222],.85),
 ('bottom',[9.91,y,lower],[181,285],.85),
 ('central doorway',[0,13.2,1.50],[559,324],3),
 ('centre nearest over door',[0,13.20,2.6155],[559,295],.9),
 ('right pier',[xe,y-back,2.51],[454,299],.9),
 ('left pier',[xw,y-back,2.51],[693,286],.9),
 ('left cap',[xw,y,cap],[696,185],1),
 ('left bottom',[xw,y,lower],[696,256],1),
 ('sill',[10.04,bay,1.19],[52,356],1),
 ('near red sun',[10.04,bay,1.19+(6.91-1.19)*s],[54,188],0),
 ('near left medallion',[10.0,bay+.81,1.19+(4.27-1.19)*s],[33,256],.85),
 ('near right medallion',[10.,bay-.81,1.19+(4.27-1.19)*s],[70,265],0),
 ('rect sill',[10.,rect,1.20],[164,353],1),
 ('rect transom',[10.,rect,2.51],[163,316],0),
 ('door jamb left',[-.83,13.2,1.5],[574,324],0),
 ('door jamb right',[.90,13.2,1.5],[546,324],0)]

def fit():
    geometry=[25.79,4.84,3.19,29.785,26.37,.719,2.44,-3.35,.918]
    def error(v):
        p=projection(v)
        return np.r_[(p[:2,1]/p[2,1]-vp)*2.5,
            np.concatenate([(project(p,pt)-uv)*w for _,pt,uv,w in obs([*v,*geometry]) if w]),
            (v[6]-600)/90,(v[2]-1.8)*2]
    sol=least_squares(error,[-.5,40.6,2.08,.232,.050,-.021,612.],
        bounds=([-9,32.,1.,-.9,-.5,-.2,300],[5,52.,3.3,.9,.5,.2,1200]),x_scale='jac',loss='soft_l1',f_scale=5)
    p=projection(sol.x)
    sx=1600/FRAME[0];sy=1067/FRAME[1]
    pn=np.array([[sx,0,(sx-1)*.5],[0,sy,(sy-1)*.5],[0,0,1.]])@p
    records=[]
    for name,pt,uv,w in obs([*sol.x,*geometry]):
        projected=project(p,pt)
        records.append(dict(label=name,xyz=pt,observed=uv,projected=projected.round(4).tolist(),
                     residual_px=round(float(np.linalg.norm(projected-uv)),4),fit_weight=w))
    return dict(photo='https://commons.wikimedia.org/wiki/File:Shanghai_No._3_Girls%27_High_School,_theater.jpg',
       date='2017-08-21',author='Ctny',license='CC BY-SA 4.0',frame=list(FRAME),native=[1600,1067],
       eye=sol.x[:3].tolist(),parameters=sol.x.tolist(),projection=p.tolist(),native_projection=pn.tolist(),
       gallery_geometry=dict(front_y=25.79,front_top=4.84,slab_soffit=3.19,pier_setback=.918,inside_pier_jamb_west_east=[-3.35,2.44]),
       reading='Working photo was resized to 850 by 567. The aisle floor edges were traced over y=364..565 using horizontal intensity gradients across the seat bases; bright reflections inside the aisle were excluded.',
       aisle_lines=[[[536.10,400],[479.25,550]],[[617.30,400],[697.10,550]]],vanishing_point_observed=vp.tolist(),
       vanishing_point_model=(p[:2,1]/p[2,1]).tolist(),fit=[r for r in records if r['fit_weight']>0],
       held_out=[r for r in records if not r['fit_weight']],scope='Approximate perspective conditional on the georeferenced 26.4 m hall width. The central open door and the aisle convergence constrain orientation. Gallery pier widths, setback and stained-glass proportions were fitted before locking the working geometry. No surveyed interior optical centre.',
       alternative=dict(method='initial section with the central doorway withheld; assumed jambs at +3.99/-6.29 metres',eye=[-.20735,38.15497,2.47523],door_residual_px=80.955,door_target_uv=[559,324],door_projected_uv=[478.045,324.039]))
if __name__=='__main__':
    result=fit();OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('eye',result['eye'],'vp',result['vanishing_point_model'],'independent',[(r['label'],r['residual_px']) for r in result['held_out']])
