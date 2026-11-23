"""Fit common lintel and sill levels to the 2015 licensed photograph. Inputs and uncertainty are explicit."""
from pathlib import Path
import argparse,hashlib,json,math
import numpy as np
from PIL import Image
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

parser=argparse.ArgumentParser();parser.add_argument('--photograph',type=Path,required=True);parser.add_argument('--footprint',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);q=parser.parse_args()
def sha(path):
 with path.open('rb') as fi:return hashlib.file_digest(fi,'sha256').hexdigest()
image=Image.open(q.photograph);assert image.size==(4912,3264)
width,height=840,3264*840/4912; f35=image.getexif().get_ifd(34665)[41989]; assert f35==24
reg=json.loads(q.footprint.read_text());reg=reg.get('registration',reg);radius=reg['radius_m'];half=reg['arc_length_m']/2
# Working-pixel readings at the midpoints between the two panes on each bay.
# Heads and sills use the dark masonry aperture, excluding projecting sill noses.
levels={
'ground-contact':[(348,522),(450,526),(546,525)],
'ground-aperture-sill':[(345,489),(450,496),(548,497)],
'ground-aperture-head':[(346,434),(450,434),(548,440)],
'base-cap':[(347,386),(450,383.5),(546,389)],
'L2-sill':[(354,381),(451,378.5),(543.5,383.5)],'L2-head':[(354,343.5),(451,338),(543.5,345)],
'L3-sill':[(358.5,304.5),(451,299),(541.5,307.5)],'L3-head':[(358.5,268.5),(451,260.5),(541.5,270.5)],
'L4-sill':[(361,234),(450.5,224.5),(537,235)],'L4-head':[(361,201.5),(450.5,190.5),(537,202)],
'L5-sill':[(363.5,167.5),(450.5,157),(535.5,171)],'L5-head':[(363.5,146),(450.5,132),(535.5,146.5)],
'L6-sill':[(370,94),(450.5,80),(534.5,96)],'L6-head':[(370,75),(450.5,58.5),(534.5,76)]}
zz=[0,0.9,3.6,5.7,6.0,8.0,9.5,11.5,13.0,15.0,17,19,21,23];rows=list(levels); uv=np.array(list(levels.values()));cx,cy=(width-1)/2,(height-1)/2
# X grows along the image to the Fuzhou Road wing, Z is upward. Y increases inwards.
def station_fit(focal_equiv,arc_spacing,drop=None):
 xx=arc_spacing*np.array([-1.,0.,1.]);plane=np.c_[radius*np.sin(xx/radius),radius*(1-np.cos(xx/radius))];f=width*focal_equiv/36
 def project(v):
  camera=v[:3]; yaw,pitch,roll=v[3:6]; opt=np.array([math.sin(yaw)*math.cos(pitch),math.cos(yaw)*math.cos(pitch),math.sin(pitch)]);right=np.array([math.cos(yaw),-math.sin(yaw),0]);down=np.cross(opt,right);R=np.vstack([right,down,opt]);rot=Rotation.from_rotvec(np.array([0,0,roll])).as_matrix();R=rot@R
  ht=np.r_[0,v[6:]];points=np.zeros((len(ht),3,3));points[:,:,:2]=plane[None,:,:];points[:,:,2]=ht[:,None];cam=(points-camera)@R.T;pred=cam[:,:,:2]/cam[:,:,2,None]*f+[cx,cy];return pred
 def residual(v):
  delta=project(v)-uv
  # The pavement is behind feet/poles; its approximate ordinate carries less weight.
  weights=np.ones((len(rows),3,1));weights[0]=.4;weights[1]=.65;weights[2]=.75;weights[3]=.7
  if drop is not None:weights[drop]=0
  return (delta*weights).ravel()
 r=least_squares(residual,[0.,-20.,1.6,0.,.45,0.,*zz[1:]],loss='soft_l1',f_scale=1.,max_nfev=1250);px=project(r.x);errs=np.sqrt(((px-uv)**2).sum(axis=2));return {'camera_m':r.x[:3].tolist(),'yaw_pitch_roll_degrees':np.degrees(r.x[3:6]).tolist(),'levels_m':dict(zip(rows,np.r_[0,r.x[6:]].tolist())),'focal_equiv_mm':focal_equiv,'spacing_m':arc_spacing,'projected':px.tolist(),'error':errs.tolist(),'median':float(np.median(errs)),'max':float(errs.max())}
nominal=reg['arc_length_m']/3;v=station_fit(f35,nominal);sweeps=[station_fit(f0,nominal*k) for f0 in [23.,24.,25.]for k in [.95,1.,1.05]];raw={k:{'working_px':r,'native_px':[[round((x+.5)*4912/840-.5,2),round((y+.5)*4912/840-.5,2)]for x,y in r]}for k,r in levels.items()};ht=v['levels_m'];results={'photo_sha256':sha(q.photograph),'native_pixels':image.size,'working_pixels':{'width':840,'height':height,'coordinates':'origin at upper left pixel centre, working X and Y use the same native scale'},'footprint_registration_sha256':sha(q.footprint),'model':'All levels are conditional estimates. Three equal arc intervals within the externally registered 13.05 m arc anchor scale. Fit allows one elevation per feature level; five footprint nodes supply radius. One camera, flat floor datum approximate, local projections and lens distortion are not surveyed. Visible cap and plinth can project beyond the window plane.','arc_radius_m':radius,'external_five_node_arc_m':reg['arc_length_m'],'normalized_observations':raw,'fit':v,'sensitivity_23_25mm_and_5pct_spacing':{k:[round(min(s['levels_m'][k] for s in sweeps),3),round(max(s['levels_m'][k] for s in sweeps),3)]for k in rows},'adjacent_sill_intervals_m':{str(i)+'–'+str(i+1):round(ht['L'+str(i+1)+'-sill']-ht['L'+str(i)+'-sill'],2) for i in range(2,6)}};q.output.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print(v['median'],v['max'],v['camera_m'],ht,results['adjacent_sill_intervals_m'])
