"""Fit both north wall planes from independently marked piers and window courses.

The brick length assumption and the street-grade estimate are explicit below.
The nearby taller volume and the rounded tower are outside these planar fits.
"""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

HERE=Path(__file__).resolve().parent
def apply(h,p):
 q=np.asarray(h)@np.r_[p,1.]
 return q[:2]/q[2]
def fit(rows):
 w=np.array([[q['pier_index'],int(q['row']=='roof')] for q in rows]);p=np.array([q['px'] for q in rows])
 a=[];b=[]
 for (u,v),(x,y) in zip(w,p):
  a.extend([[u,v,1,0,0,0,-x*u,-x*v],[0,0,0,u,v,1,-y*u,-y*v]]);b.extend([x,y])
 init=np.linalg.lstsq(a,b,rcond=None)[0]
 def err(beta):return np.asarray([apply(np.r_[beta,1].reshape(3,3),s)-t for s,t in zip(w,p)]).ravel()
 f=least_squares(err,init)
 return np.r_[f.x,1].reshape(3,3),err(f.x).reshape(-1,2)
def main():
 q=json.loads((HERE/'nanjing-photo-controls.json').read_bytes());h={};errs={}
 for k in ['a','b']:h[k],errs[k]=fit(q[k])
 # Below the chosen double casement: multiple consecutive, staggered bed joints of
 # the centre pier. Three stretcher pitches from one identifiable alternate course.
 jb=np.array([[2092,1368],[2132,1367.6],[2172,1367.2]])
 inv=np.linalg.inv(h['b']);ju=[apply(inv,p)[0] for p in jb];pitch=.235/np.median(np.diff(ju))
 ratios={}
 for k,(w,ht) in {'a':(3024,4032),'b':(4032,3024)}.items():
  f=26*np.hypot(w,ht)/43.27
  ki=np.linalg.inv([[f,0,w/2],[0,f,ht/2],[0,0,1]])
  x,z=ki@h[k][:,0],ki@h[k][:,1];ratios[k]=np.linalg.norm(z)/np.linalg.norm(x)
 # The close shot has much less foreshortening and brackets this measured course.
 height=pitch*ratios['b']
 grades=[apply(np.linalg.inv(h['a']),p)[1] for p in q['grade_a']]
 # The corner starts to turn on the projecting lip of the north shop cornice.
 turns=[apply(np.linalg.inv(h['a']),p)[0] for p in q['tangent_a']]
 u0=turns[0];v0=float(np.median(grades))
 metric=np.array([[pitch,0,-pitch*u0],[0,height,-height*v0],[0,0,1]])
 hm={k:y@np.linalg.inv(metric)for k,y in h.items()}
 def xyz(k,p):return apply(np.linalg.inv(hm[k]),p)
 hs=[]
 for x,y in zip(q['holdouts']['a'],q['holdouts']['b']):
  est_b=apply(hm['b'],xyz('a',x));hs.append(dict(oblique_original_px=x,close_original_px=y,close_projected_px=est_b.tolist(),difference_px=float(np.linalg.norm(est_b-y)),difference_plane_m=float(np.linalg.norm(xyz('a',x)-xyz('b',y)))))
 windows={k:[xyz('b',p).tolist()for p in src]for k,src in q['window_faces'].items()}
 print('pitch',pitch,'height',height,'ratio',ratios,'turn',turns,'grade',grades,'windows',windows,'resids',errs,'checks',[round(g['difference_plane_m'],2)for g in hs])
 result={'frame':'X west along the north wall, Y inward. Origin is western end of the straight northern facade at ring vertex 2 of shell 822. Elevation Z measured from estimated street grade.',
 'views':{'a':'Chainwit. 2024-04-23 16:45, upright 3024x4032, IMG 01','b':'Chainwit. 2024-04-23 16:46, 4032x3024, IMG 02'},
 'homographies_xz_m_to_original_px':{k:H.tolist() for k,H in hm.items()},'control_residuals_original_px':{k:np.linalg.norm(v,axis=1).tolist()for k,v in errs.items()},'independent_window_centres':hs,
 'major_pier_pitch_estimate_m':pitch,'belt_to_parapet_estimate_m':height,'independent_vertical_to_horizontal_scale_ratios':ratios,'selected_openings_xz_m':windows,
 'brick_reference':{'image':'b','head_joint_readings_px':jb.tolist(),'estimated_stretcher_pitch_m':.235,'plausible_nominal_pitch_m':[.215,.25],'absolute_scale_is_estimated':True,'interpretation':'Same-course repeat, including one mortar joint. A 33-course vertical run is retained independently as a check.'},
 'vertical_course_crosscheck_m':float(abs(xyz('b',[2140,1595])[1]-xyz('b',[2140,1321])[1])/33),
 'coordinate_datum':{'tangent_mark_spread_m':[(x-u0)*pitch for x in turns],'sidewalk_spread_m':[(y-v0)*height for y in grades],'north_GIS_straight_m':44.1163},
 'limitations':'The rounded northwest corner has an approximate tangent, and people hide part of street grade. Allow about 1.5 m for position along the entire street wall, 0.8 m for grade, and roughly 9% for overall size. Local relative dimensions are more reliable. H applies to one plane only. Projecting steel fronts and brick reveal depth create genuine residuals.'}
 (HERE/'nanjing-window-registration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()

def complete_cameras():
 """Use independently known focal length and the two facade axes to recover Y."""
 from scipy.optimize import least_squares
 out=HERE/'nanjing-window-registration.json';j=json.loads(out.read_bytes())
 q=json.loads((HERE/'nanjing-photo-controls.json').read_bytes())
 cams={};eyes={}
 for name,(w,height_px) in {'a':(3024,4032),'b':(4032,3024)}.items():
  h=np.asarray(j['homographies_xz_m_to_original_px'][name]);h*=np.sign((h@[-20,13,1])[2])
  f=26*np.hypot(w,height_px)/43.27;k=np.array([[f,0,w/2],[0,f,height_px/2],[0,0,1.]])
  ax=np.linalg.solve(k,h[:,:2]);normal=np.cross(ax[:,1],ax[:,0]);normal*=np.linalg.norm(ax,axis=0).mean()/np.linalg.norm(normal)
  p=np.column_stack([h[:,0],k@normal,h[:,1],h[:,2]]);cams[name]=p;eyes[name]=(-np.linalg.solve(p[:,:3],p[:,3])).tolist()
 def proj(p,xyz):
  v=p@np.r_[xyz,1];return v[:2]/v[2]
 check=[]
 for a,b in zip(q['holdouts']['a'],q['holdouts']['b']):
  f=lambda xyz:np.r_[proj(cams['a'],xyz)-a,proj(cams['b'],xyz)-b];s=least_squares(f,[-19,0,12]);check.append(dict(original_a=a,original_b=b,xyz=s.x.tolist(),per_image_pixel_errors=np.linalg.norm(s.fun.reshape(2,2),axis=1).tolist()))
 j.update(cameras_west_inward_up_to_px={k:v.tolist()for k,v in cams.items()},camera_centres_estimate_m=eyes,metal_cross_intersections=check)
 j['reading']='The repeated grille crosses are setback. The single-plane residuals retain the apparent displacement. A two-camera estimate puts the grille 0.14–0.22 m behind the principal pier plane; some registration and relief remain unresolved.'
 j['control_heights_estimate_m']={'premium_shop_cornice_upper_edge':float(-np.median([apply(np.linalg.inv(np.asarray(j['homographies_xz_m_to_original_px']['a'])),p)[1]for p in q['grade_a']])),}
 # Use the horizontal reference rows themselves at pier 0 to report world Z.
 for row,key in [('sill','shop_cornice_upper_edge'),('roof','ordinary_parapet_line')]:
  v=[apply(np.linalg.inv(np.array(j['homographies_xz_m_to_original_px']['b'])),s['px'])[1]for s in q['b']if s['row']==row]
  j['control_heights_estimate_m'][key]=float(np.median(v))
 del j['control_heights_estimate_m']['premium_shop_cornice_upper_edge']
 out.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':complete_cameras()
