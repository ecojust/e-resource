"""Fit two physical facade planes using five surveyed panorama poses and the 2015 27-mm-equivalent photograph."""
from pathlib import Path
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from hashlib import sha256
import numpy as np,json,math
w=Path(__file__).parent;read=lambda f:json.loads((w/f).read_bytes());t=read('triangulated.json');r=read('survey.json');idx=[0,1,4,5,6];dims=[326,255]
# The DSLR was downsampled to 820 px; its focal length in 35-mm-equivalent units is recorded in EXIF.
# Rectified crop coordinates are converted back to the full photograph.
def dslr(point):return ((np.array(point)/[762,878]*[887,1020]+[683,280]+.5)/[2144,1424]*[820,545]-.5)
qmarks={'gable_top':(345,109),'cross_joint':(345,54),'gable_window_peak':(342,326),'porch_north_coping':(64,548),'porch_south_coping':(547,548),'bay2_north_upper':(264,657)}
nice=list(qmarks);refs={k:dslr(qmarks[k])for k in nice};prior=np.array([*r['shots'][0]['offset_m'],2.32]);
def axes(theta):
 return np.array([math.sin(theta),-math.cos(theta),0.]),np.array([math.cos(theta),math.sin(theta),0.])
def locations(x):
 X,Y,A,H,D,C,T,G,V,bay_x,bay_z=x[:11];a,n=axes(A);o=np.array([X,Y,0]);z=np.array([0,0,1])
 return dict(gable_top=o+n*D+z*G,cross_joint=o+n*D+z*T,gable_window_peak=o+n*D+z*V,porch_north_coping=o-a*H+z*C,porch_south_coping=o+a*H+z*C,bay2_north_upper=o+a*bay_x+z*bay_z)
def raycoords(Q,ct,R,U,F,f,wh):
 rr=Q-ct;return np.array([(wh[0]-1)*.5+f*np.dot(rr,R)/np.dot(rr,F),(wh[1]-1)*.5-f*np.dot(rr,U)/np.dot(rr,F)])
def camera(rot):
 h,e,b=rot;f=np.array([math.sin(h)*math.cos(e),math.cos(h)*math.cos(e),math.sin(e)]);rt=np.array([math.cos(h),-math.sin(h),0]);up=np.cross(rt,f);return rt*math.cos(b)+up*math.sin(b),up*math.cos(b)-rt*math.sin(b),f
def loss(x,display=False):
 v=locations(x);res=[];report={}
 for j,i in enumerate(idx):
  s=r['shots'][i];f=s['focal']*dims[1]/s['imsize'][1];base=np.array(s['offset_m']+[s['eye_z']]);d=x[11+j*5:16+j*5];ct=base+d[:3]
  R,U,F=map(np.asarray,[s['right'],s['up'],s['forward']]);rot=Rotation.from_rotvec(d[3]*[0.,0.,1.] if False else np.array([0,0,d[3]])+d[4]*R);R,U,F=rot.apply([R,U,F]);errors=[]
  for key in nice:
   pix=t['landmarks'][key]['pixels'].get(str(i));q=raycoords(v[key],ct,R,U,F,f,dims);errors.extend(q-pix)
  res+=list(np.asarray(errors)/2.25);res+=list(d/np.array([.75,.75,.28,math.radians(1.3),math.radians(1.6)]));report[str(i)]=dict(rms_px=np.sqrt(np.mean(np.array(errors)**2)),correction_m=d[:3].tolist(),correction_yaw_pitch_deg=np.degrees(d[3:]).tolist())
 cx=x[-7:];R,U,F=camera(cx[3:6]);e=[]
 for k,px in refs.items():e.extend(raycoords(v[k],cx[:3],R,U,F,cx[-1],[820,545])-px)
 res+=list(np.asarray(e)/1.55);res +=[(cx[-1]-615)/18,(cx[2]-1.65)/.32,(x[9]+.47)/.35,(x[10]-3.86)/.46]
 report['dslr_rms_px']=np.sqrt(np.mean(np.array(e)**2));return (report,cx)if display else np.array(res)
x0=np.array([-3.2,-2.6,-.115,3.77,5.75,5.32,17.13,15.78,10.96,-.47,3.86]+[0.]*(5*len(idx))+[-19.,-2.,1.65,math.pi/2,.246,0.,615.]);out=least_squares(loss,x0,x_scale='jac',loss='soft_l1',f_scale=1.8,max_nfev=1200);x=out.x;assert out.success;sgn=read('survey.json')['target'];S=np.array([math.cos(math.radians(sgn[1])),1.])*111195.08;o=x[:2];a,n=axes(x[2]);print('planes',x[:11].round(3),'wgs',(sgn+o/S).round(9),flush=True);report,c=loss(x,True);print(report,flush=True)
# Back-project directly measured DSLR landmarks to the appropriate surface, no vanishing-line guess.
keypts={'gable':{'eave_north':(84,434),'eave_south':(606,431),'north_return':(39,444),'south_return':(650,443),'verge_north':(95,445),'sill_l':(192,545),'sill_r':(487,545),'outer_top':(341,325),'spring_l':(190,491),'spring_r':(488,486),'mullion_north':(289,425),'mullion_south':(398,420),'cross_l':(310,55),'cross_r':(378,54),'cross_tip':(344,23)},'porch':{'top_left':(61,549),'top_right':(548,550),'fascia_top':(301,564),'fascia_bottom':(301,623),'lintel':(303,652),'pier_sill':(304,761),'panel1a':(151,655),'panel1b':(214,762),'panel2a':(264,655),'panel2b':(330,762),'panel3a':(381,657),'panel3b':(447,762)}}
local={};R,U,F=camera(c[3:6])
for plane,pts in keypts.items():
 d=x[4] if plane=='gable' else 0;local[plane]={}
 for k,p in pts.items():
  px=dslr(p);ray=F+(px[0]-409.5)*R/c[-1]-(px[1]-272)*U/c[-1];origin=np.r_[o,0.];dist=(d-n@(c[:3]-origin))/(n@ray);point=c[:3]+ray*dist-origin;local[plane][k]=[round(float(a@point),4),round(float(point[2]),4)]
print(local,flush=True)
res=dict(method='robust joint bundle of five street station observations and independently EXIF-constrained DSLR photo, independent poses; x along front north-to-south and y toward church',source_sha256={f:sha256((w/f).read_bytes()).hexdigest()for f in ['known0.json','survey.json','triangulated.json','roof.json']},wgs_anchor=(sgn+o/S).tolist(),azimuth_x_deg=math.degrees(math.atan2(a[0],a[1]))%360,angle_from_due_south_deg=math.degrees(x[2]),computation_origin_wgs=sgn,axes=[a.tolist(),n.tolist()],fit_variables=x[:11].tolist(),fits=report,dslr_camera=c.tolist(),image_measurements=keypts,local_landmarks=local,uncertainty_m={'absolute_east_north':.9,'ridge_z':1.2,'porch_width':.6,'portico_depth':.75,'projected_trim':.15},rays=t['landmarks'])
(w/'measured-facade.json').write_text(json.dumps(res,indent=1,ensure_ascii=False)+'\n')
