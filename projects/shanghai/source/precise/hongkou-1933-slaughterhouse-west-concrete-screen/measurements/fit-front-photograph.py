"""Fit independently marked screen centres in Windmemories' street photograph."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import numpy as np
from scipy.optimize import least_squares

SOURCE=Path(__file__).resolve().parent.parent/'source'
p=json.loads((SOURCE/'dimensions.json').read_bytes())
# Axes run from north to south. The coordinates are measured on the 900 x 600
# copy of the 1800 x 1200 original. Points correspond to circular pane centres.
corners=[
 ((109,149),(67,379)),((177,149),(143,379)),
 ((262,149),(237,380)),((330,149),(315,381)),
 ((431,116),(429,367)),((467,116),(471,367)),
 ((570,149),(587,380)),((638,149),(663,381)),
 ((722,149),(758,380)),((790,149),(832,381))]
width=p['facade_width'];c=p['centre_bay'];span=(width-c)/8
axes=[(sign*(c/2+(j+.5)*span)+side*p['pair_axis']/2,False)for sign in (-1,1)for j in (0,1)for side in (-1,1)]
axes+= [(side*p['centre_ring_separation']/2,True)for side in (-1,1)]
axes.sort()
world=[];observed=[];labels=[]
for (axis,central),(top,bottom) in zip(axes,corners):
    pitch=p['central_pitch'] if central else p['screen_pitch']
    sill=p['central_sill'] if central else p['ordinary_sill']
    for i,xy in [(12 if central else 11,top),(0,bottom)]:
        labels.append(f'axis {axis:.3f} m, ring {i+1}')
        world.append([.145,-axis,sill+(i+.5)*pitch]);observed.append(xy)
world=np.array(world);observed=np.array(observed)
unit=lambda v:v/np.linalg.norm(v)


def project(params):
    ex,ey,ez,az,tilt,focus=params
    eye=np.array([ex,ey,ez]);az,tilt=np.radians([az,tilt])
    view=np.array([np.cos(tilt)*np.cos(az),np.cos(tilt)*np.sin(az),np.sin(tilt)])
    right=unit(np.cross(view,[0.,0.,1.]));up=np.cross(right,view)
    a=world-eye;px=450+focus*(a@right)/(a@view);py=300-focus*(a@up)/(a@view)
    return np.stack([px,py],axis=1),eye,view


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('output',type=Path);args=cli.parse_args()
    def residuals(params):return (project(params)[0]-observed).ravel()
    solved=least_squares(residuals,[-27,0,1.7,0,15,650],bounds=([-65,-6,.75,-15,2,370],[-14,6,2.8,15,36,1100]),loss='soft_l1',f_scale=1.6)
    predicted,eye,view=project(solved.x);err=np.linalg.norm(predicted-observed,axis=1)
    angle=-math.radians(p['front_axis_bearing_deg']);rot=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
    target=eye+view*((.145-eye[0])/view[0])
    def enu(v):return [*(rot@v[:2]),v[2]]
    span=np.linalg.norm(target-eye)*900/solved.x[5]
    note='Original-resolution residuals double the distances measured in the 900 px working image. The pose is an estimate from almost coplanar centres, without independent absolute camera range.'
    receipt=dict(source='https://commons.wikimedia.org/wiki/File:20260208_Shanghai_International_Settlement_Slaughterhouse_01.jpg',photograph_sha256='72c5d55a386ff2ad97a00194bae07300ffbc75f6aa4feebd7964db2c6c3af42f',source_size=[1800,1200],working_size=[900,600],method=note,source_groups=len(axes),marks=[dict(point=name,world_local_east_north_up=pt.tolist(),observed_working_px=xy.tolist(),projected_working_px=q.round(3).tolist(),distance_original_px=round(2*d,3))for name,pt,xy,q,d in zip(labels,world,observed,predicted,err)],camera_parameters=solved.x.tolist(),rms_original_px=2*float(np.sqrt(np.mean(err**2))),maximum_original_px=2*float(err.max()),view=dict(name='windmemories-west-front',eye=enu(eye),target=enu(target),width_m=span,width=900,height=600))
    args.output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(receipt['rms_original_px'],receipt['maximum_original_px'],solved.x)
