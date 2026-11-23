"""Independent photographed leaf swing, pier face and planter depth from January 2021 angular observations."""
import json,math,hashlib,itertools
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
D=Path(__file__).parent;j=json.loads((D/'surveyed-street-gate.json').read_bytes());scale=np.array([111320*math.cos(math.radians(j['native_observations']['frame_origin_wgs84'][1])),110860]);origin=np.array(j['native_observations']['frame_origin_wgs84']);X={k:np.array(v['enu'])for k,v in j['all_three']['registered_points'].items()}
obs={2:{'west-lantern-fixture-center':(511,265),'east-lantern-fixture-center':(678,261),'west-green-address-plate-center':(496,217),'east-wall-inner-front-ground':(669,344),'east-wall-outer-front-ground':(747,333),'east-wall-outer-front-pier-top':(743,189),'sunburst-crown-upper-midpoint':(700,176),'gold-shield-center':(715,271)},5:{'east-lantern-fixture-center':(715,248),'east-wall-inner-front-ground':(698,371),'east-wall-outer-front-ground':(822,354),'east-wall-outer-front-pier-top':(825,162),'sunburst-crown-upper-midpoint':(758,129),'gold-shield-center':(775,273)}}
cams={};cal={}
for i in [2,3,5,7,8]:
 q=json.loads((D/f'metal-work-{i}.json').read_bytes());s=q['station'];az,p=np.deg2rad([q['az'],q['pitch']]);h=np.array([np.sin(az),np.cos(az),0.]);up=np.array([0.,0.,1.]);f=q['width']/(2*np.tan(np.deg2rad(q['hfov'])/2));C=np.r_[(np.array(s['position'])-origin)*scale,s['height']];M=np.stack([np.array([np.cos(az),-np.sin(az),0.]),up*np.cos(p)-h*np.sin(p),h*np.cos(p)+up*np.sin(p)])
 if i in (3,7,8):
  correction=j['all_three']['camera_rotation_corrections_deg_enu'][str(i)]
 else:
  def residual(rot):
   rows=[]
   for k,uv in obs[i].items():
    v=Rotation.from_rotvec(np.deg2rad(rot)).apply(X[k]-C)@M.T
    pred=np.array([q['width']/2+f*v[0]/v[2],q['height']/2-f*v[1]/v[2]]);rows.extend((pred-uv)/2)
   return rows
  o=least_squares(residual,[5,0,-7],loss='soft_l1');correction=o.x.tolist();cal[i]={'points':obs[i],'rotation_enu_deg':correction,'rms_px':float(np.sqrt(np.mean((np.array(residual(correction))*2)**2)*2))}
 cams[i]=(C,Rotation.from_rotvec(np.deg2rad(correction)).as_matrix().T@M.T,f,q)
def ray(i,p):
 c,m,f,q=cams[i];d=m@np.array([(p[0]-q['width']/2)/f,(q['height']/2-p[1])/f,1.]);return c,d/np.linalg.norm(d)
def estimate(ob):
 m=np.zeros((3,3));b=np.zeros(3)
 for i,p in ob.items():
  c,d=ray(i,p);s=np.eye(3)-np.outer(d,d);m+=s;b+=s@c
 x=np.linalg.solve(m,b);return x
def project(i,x):
 c,d,f,q=cams[i];v=(x-c)@d;return np.array([q['width']/2+f*v[0]/v[2],q['height']/2-f*v[1]/v[2]])
A=math.radians(j['all_three']['measures']['right_panel_axis_true_bearing_deg']);axis=np.array([math.sin(A),math.cos(A)]);dep=np.array([-axis[1],axis[0]]);G=(X['east-wall-inner-front-ground']+X['west-pier-inner-front-ground'])/2
marks={
'west-pier-outer-front-base':{3:(145,426),7:(117,462),8:(145,467)},
'west-pier-inner-front-base':{3:(251,424),7:(205,461),8:(181,474)},
'west-pier-inner-return-base':{3:(271,417),7:(238,452),8:(208,465)},
'west-leaf-hinge-foot':{3:(272,414),7:(239,448),8:(208,463)},
'west-leaf-free-tip-crown':{3:(306,168),7:(347,197),8:(338,280)},
'west-leaf-free-tip-bottom':{7:(362,412),8:(342,447)},
'east-leaf-hinge-foot':{2:(650,342),5:(679,364),3:(637,376)},
'east-leaf-free-tip-top':{2:(608,219),5:(635,192)},
'east-leaf-free-tip-bottom':{2:(607,334),5:(632,350)},
'east-planter-front-west-foot':{3:(654,379),7:(658,454),8:(376,488),5:(701,371)},
'east-planter-front-east-foot':{3:(849,349),8:(568,509),5:(820,353)},
'east-wall-gold-plaque-center':{7:(868,270),8:(514,347),5:(775,273)},
'west-low-wall-contact-with-shop':{2:(422,369),5:(259,424)},
}
out={}
for k,ob in marks.items():
 x=estimate(ob);l=x[:2]-G[:2];out[k]={'pixels':ob,'enu':x.round(3).tolist(),'relative_along_front_inward_height_m':[round(float(l@axis),3),round(float(l@dep),3),round(float(x[2]),3)],'residual_px':{i:round(float(np.linalg.norm(project(i,x)-p)),2)for i,p in ob.items()},'pairwise_enu':{str((i,g)):estimate({i:ob[i],g:ob[g]}).round(3).tolist()for i,g in itertools.combinations(ob,2)}}
def pt(k):return np.array(out[k]['relative_along_front_inward_height_m'])
cosang=lambda u:np.rad2deg(np.arctan2(u[1],u[0]))
dims={}
for side,tip in [('west','crown'),('east','top')]:
 hin=pt(side+'-leaf-hinge-foot');tip1=pt(side+'-leaf-free-tip-'+tip);tip2=pt(side+'-leaf-free-tip-bottom')
 vec=(tip2-hin)[:2];vec1=(tip1-hin)[:2];sign=1 if side=='west'else-1
 dims[side+'_leaf_bottom']=[float(np.linalg.norm(vec)),float(cosang(vec*[sign,1]))];dims[side+'_leaf_upper_vs_base']=[float(np.linalg.norm(vec1)),float(cosang(vec1*[sign,1]))]
dims['west_pier_face_width_m']=float(np.linalg.norm((pt('west-pier-inner-front-base')-pt('west-pier-outer-front-base'))[:2]));dims['west_pier_visible_return_depth_m']=float((pt('west-pier-inner-return-base')-pt('west-pier-inner-front-base'))[1]);dims['west_pier_to_shop_low_wall_projected_width_m']=float((pt('west-pier-outer-front-base')-pt('west-low-wall-contact-with-shop'))[0]);dims['east_planter_front_offset_from_plaque_m']=float(pt('east-wall-gold-plaque-center')[1]-(pt('east-planter-front-west-foot')[1]+pt('east-planter-front-east-foot')[1])/2)
report={'source_camera_bundle':j['all_three']['rms_pixels'],'site_calibration_2_and_5':cal,'sources':{i:{'extraction':f'metal-work-{i}.json','document_sha256':hashlib.sha256((D/f'metal-work-{i}.json').read_bytes()).hexdigest(),'sha256':q['photo_sha256'],'date':q['station']['date'],'station':q['station']['id']}for i,(_,_,_,q) in cams.items()},'local_system':'X=street frontage towards the photograph right; Y=inward; Z=above roadway. Leaf angle measured from the closed gate line toward the courtyard.','controls':out,'dimensions_m_and_angles_deg':dims}
(D/'metal-leaves-and-plinths.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dims,indent=2));print('extra station RMS',[(i,q['rms_px'])for i,q in cal.items()]);print([(k,p['relative_along_front_inward_height_m'],p['residual_px'])for k,p in out.items()])
