"""Project three entrances in the 2015 south view using their measured horizontal spacing."""
from pathlib import Path
import json,math
import numpy as np
from scipy.optimize import least_squares
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
# Photo native and preview have the same complete frame. Pixel observations use its 1000-pixel derivative.
F=1000*27/36;cx,cy=500,332
w=19.4093
# The 2020 near-axial image (front-high-crop) gives axes ~345,515,687; outer facade x~98,925.
spacing=170/(925-98)*w
# Fit the right and left outer arch jambs, not the foreground granite drums or lions.
# Each door has two separately observed datum points at the threshold and spring.
obs=[(-1,-1,172,541,182,384),(-1,1,318,540,322,383),(0,-1,434,537,435,386),(0,1,593,537,591,384),(1,-1,682,536,682,403),(1,1,784,532,785,401)]
def calculate(p,u,z):
 yaw,pitch,roll,X,Y,Z=p[:6]
 look=np.array([np.sin(yaw)*np.cos(pitch),np.cos(yaw)*np.cos(pitch),np.sin(pitch)])
 right=np.array([np.cos(yaw),-np.sin(yaw),0.]);up=np.cross(right,look)
 d=np.array([u-X,-Y,z-Z]);x=d@right/(d@look);y=d@up/(d@look)
 return np.array([cx+F*(x*np.cos(roll)+y*np.sin(roll)),cy+F*(x*np.sin(roll)-y*np.cos(roll))])
def residual(p):
 ar=[];half=[p[6],p[7],p[6]];spr=[p[8],p[9],p[8]]
 for i,s,x,y,xx,yy in obs:
  u=i*spacing+s*half[i+1];ar.extend(calculate(p,u,.48)-[x,y]);ar.extend(calculate(p,u,spr[i+1])-[xx,yy])
 return ar+[(p[2]-.0)*100,(p[5]-1.58)*3]
fit=least_squares(residual,[.20,.15,0,-2.5,-10,1.7,1.0,1.15,2.7,2.9],bounds=([-.95,-.27,-.3,-15,-30,.55,.6,.75,1.9,1.9],[.95,.50,.3,15,-4,3.4,1.8,2.,4.5,4.9]),loss='soft_l1',f_scale=3.5);p=fit.x
def elevation(px,u=0):
 return round(least_squares(lambda z:[calculate(p,u,z[0])[1]-px],[4.]).x[0],3)
print('spacing',spacing,'residual',np.sqrt(np.mean(np.array(residual(p))[:24]**2)),p.tolist(),flush=True)
data=dict(derived_photo_size=[1000,664],lens_equivalent_mm=27,assumed_focal_px=F,horizontal_spacings_m=spacing,full_width_m=w,outer_wall_pixel_estimate=[98,925],aerial_x_axes_px=[345,515,687],front_samples=obs,reprojection_rms_px=float(np.sqrt(np.mean(np.array(residual(p))[:24]**2))),fit_params=p.tolist(),features={n:dict(front_y=y,axis_x_m=x,estimated_z_m=elevation(y,x))for n,y,x in [('central_arch_inner_apex',321,0),('central_arch_outer_apex',306,0),('side_outer_crown',345,spacing),('central_sign_mid',193,0),('central_frieze_foot',246,0),('central_tile_eave',86,0),('central_soffit',128,0),('plinth_top',499,0)]})
print(data['features'],flush=True);args.out.write_text(json.dumps(data,indent=2)+'\n')
