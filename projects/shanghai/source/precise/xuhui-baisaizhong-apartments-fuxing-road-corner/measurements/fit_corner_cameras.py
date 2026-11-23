from pathlib import Path
import numpy as np,json
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
import argparse
cli=argparse.ArgumentParser(description='Fit the two street cameras and the independent 1934 image plane.')
cli.add_argument('output',type=Path)
args=cli.parse_args()
# Four under-edges and four top coping edges, measured in the native captures.
# The little return posts and the end of the slab are different points. End coordinates
# below refer to the face of the slab, including the small stone end trim.
a={'size':[1424,2144],'f':2144*48/36,'outer_L':(367,1855),'outer_R':(1028,1853),
'left':[467,463,470,477],'right':[932,929,922,914],
'lower':[[1693,1693],[1420,1420],[1152,1154],[892,893]],
'upper':[[1594,1591],[1323,1328],[1063,1065],[807,810]],
'canopy':[615,616],'grade_mid':[694,1865],
'entry':{'outer_jamb_px':[[585,1860],[817,1860]],'centre_diamond_hidden_by_later_screen':True}}
b={'size':[1080,810],'f':1200,'outer_L':(430,656),'outer_R':(641,656),
'left':[469,470,469,470],'right':[618,618,619,620],
'lower':[[601,601],[515,516],[426,428],[338,338]],'upper':[[570,571],[485,484],[397,396],[306,306]],
'canopy':[248,248],'grade_mid':[542,655]}
# In the third photograph the street grade is cropped. Validate only the eight front edges.
c={'size':[707,900],'left':[207,202,195,194],'right':[499,498,518,517],
'lower':[[779,779],[631,632],[480,480],[332,331]],'upper':[[721,721],[577,580],[427,428],[275,273]],'grade_cropped':True}
half=4.125
data=[a,b]
def intr(d,fl):
 x,y=d['size'];return np.array([[fl,0,x/2],[0,fl,y/2],[0,0,1.]])
def facing(yaw,tilt,roll):
 x=np.radians(yaw);t=np.radians(tilt);rr=np.radians(roll)
 f=np.array([np.sin(x)*np.cos(t),np.cos(x)*np.cos(t),np.sin(t)])
 right=np.array([np.cos(x),-np.sin(x),0]);down=np.cross(f,right)
 return np.array([np.cos(rr)*right+np.sin(rr)*down,-np.sin(rr)*right+np.cos(rr)*down,f])
def camera(d,pars):
 cx,cy,cz,yaw,tilt,roll,fl=pars;C=np.array([cx,cy,cz]);R=facing(yaw,tilt,roll);return intr(d,fl)@np.column_stack([R,-R@C])
def projected(P,I):
 q=np.asarray([P@[*v,1.] for v in I]);return q[:,:2]/q[:,2,None]
def control(d,z,upper,w):
 coords=[];pix=[];err=[]
 def add(X,Y,Z,p,sd):coords.append((X,Y,Z));pix.append(p);err.append(sd)
 f=1 if d is a else .37
 add(-half,0,0,d['outer_L'],13*f);add(half,0,0,d['outer_R'],13*f);add(0,0,0,d['grade_mid'],10*f)
 for i,((ul,ur),(vl,vr)) in enumerate(zip(d['lower'],d['upper'])):
  for side,us,v1,v2 in [(-1,d['left'],ul,vl),(1,d['right'],ur,vr)]:
   # The projected coping and underside outer corners differ slightly in u.
   add(w*side,-.13,z[i],(us[i],v1),5*f)
   add(w*side,-.13,upper[i],(us[i]+(1 if side==-1 else -1),v2),7*f)
 return coords,np.asarray(pix),np.asarray(err)[:,None]
def fun(x):
 z=x[:4];upper=z+x[4];w=x[5];res=[]
 for i,d in enumerate(data):
  pars=x[6+i*7:13+i*7];k=camera(d,pars);coords,uv,sd=control(d,z,upper,w)
  res.extend(((projected(k,coords)-uv)/sd).flatten())
  res.extend([(pars[2]-1.58)/.6,(pars[-1]-d['f'])/(d['f']*(.045 if i==0 else .35))])
 return res
init=np.array([2.10,5.4,8.75,12.04,1.12,2.86,0.,-35.,1.6,0.,8.,0.,a['f'],0.,-42.,1.6,0.,4.5,0.,b['f']])
opt=least_squares(fun,init,max_nfev=1200,loss='soft_l1',f_scale=1)
x=opt.x;z=x[:4];upper=z+x[4];w=x[5]
out={'sources':{'commons2015':a,'housing2023':b,'press1934':c},'front_width_m':2*half,'corner_origin':'X across the face to the viewer’s right, Y into the building, Z up, front-wall centre on grade at [0,0,0].','balcony_undersides_m':z.tolist(),'parapet_coping_m':upper.tolist(),'overall_underside_to_coping_m':x[4],'balcony_halfwidth_m':w,'cameras':{}}
for i,(d,n) in enumerate(zip(data,['commons2015','housing2023'])):
 pars=x[6+i*7:13+i*7];p=camera(d,pars);coords,uv,sd=control(d,z,upper,w)
 delta=np.linalg.norm(projected(p,coords)-uv,axis=1)
 def level(u,v,y=0):
  M=np.linalg.inv(p[:,:3]);C=-M@p[:,3];line=M@[u,v,1];return (C+line*((y-C[1])/line[1]))[2]
 can=level(np.mean(d['left']+d['right']),np.mean(d['canopy']))
 out['cameras'][n]={'P':p.tolist(),'eye':pars[:3].tolist(),'parameters':pars.tolist(),'errors_px':delta.tolist(),'median_px':float(np.median(delta)),'canopy_underside_at_y0_m':float(can)}
# Historical newspaper image has a different crop and unreported optics. Fit its facade homography to the shared planes.
points=[];pixels=[]
for i,(vs,ts) in enumerate(zip(c['lower'],c['upper'])):
 for xx,us,j in [(-w,c['left'],0),(w,c['right'],1)]:
  points.extend([[xx,z[i]],[xx,upper[i]]]);pixels.extend([[us[i],vs[j]],[us[i],ts[j]]])
src=np.array(points);uv=np.array(pixels)
rows=[]; obs=[]
for (x,z),(u,v) in zip(src,uv):
 rows.extend([[x,z,1,0,0,0,-x*u,-z*u],[0,0,0,x,z,1,-x*v,-z*v]]);obs.extend([u,v])
H=np.r_[np.linalg.lstsq(rows,obs,rcond=None)[0],1.].reshape(3,3)
uvw=np.c_[src,np.ones(len(src))]@H.T;pr=uvw[:,:2]/uvw[:,2,None]
err=np.linalg.norm(pr-uv,axis=1);out['press_1934_front_plane']={'H_XZ_to_uv':H.tolist(),'native_px_error':err.tolist(),'median_px':float(np.median(err)),'p90_px':float(np.quantile(err,.90))}
out['notes']='Sixteen matched balcony corners per photograph. Street corners and grade have lower confidence from tree or street furniture occlusion. The four original levels are identifiable in 1934 and 2015. The central raised decoration is measured from the 2023 close view. Only image observations and parameters are distributed.'
args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('undersides',out['balcony_undersides_m'],upper,'span',2*w);print([(n,q['median_px'],q['canopy_underside_at_y0_m'],q['eye']) for n,q in out['cameras'].items()],out['press_1934_front_plane']['median_px'])
