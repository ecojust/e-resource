from pathlib import Path
from hashlib import sha256
import numpy as np
import json

original = {'left':[[834,339],[990,310],[996,698],[833,710]],'centre':[[990,310],[1158,335],[1175,708],[996,698]]}
# View two shows a change of glazing behind the centre opening and an overhanging tree.
# The pair of projected mid-band and sill edges and the left lower sash are usable.
second = {
 'left':{'panel':[[354,99],[398,80],[411,208],[357,219]],'transom':[[361,118],[389,108],[390,124],[362,131]],'sill':[[358.5,174.5],[398,164]],'apron':[[365.5,190],[395,180]]},
 'centre':{'panel':[[398,80],[464,87],[480,210],[411,208]],'transom':[[414,104],[446,106],[447,121],[417,121]],'sill':[[409,163.5],[459,164.5]],'apron':[[421.5,179],[456,181]]}}
root=Path(__file__).resolve().parent
marks=json.loads((root/'229-projected-bay-proportions.json').read_bytes())
def H(fromq,toq):
 m=[];b=[]
 for (x,y),(u,v) in zip(fromq,toq):
  m.extend([[x,y,1,0,0,0,-x*u,-y*u],[0,0,0,x,y,1,-x*v,-y*v]]); b.extend([u,v])
 return np.r_[np.linalg.lstsq(m,b,rcond=None)[0],1].reshape(3,3)
def project(h,q):
 v=np.c_[q,np.ones(len(q))]@h.T
 return v[:,:2]/v[:,2,None]
def plane(q,wx,wy):
 m=H([(0,0),(1,0),(1,1),(0,1)],q);v=m[:,0]/m[2,0];u=m[:,1]/m[2,1];f2=-np.dot((v[:2]-[wx,wy]),(u[:2]-[wx,wy]));return m,f2
def fit(p):
 mm,ff=zip(*(plane(q,1041,604.5)for q in p));assert min(ff)>0
 f=np.sqrt(np.mean(ff));k=np.array([[f,0,1041],[0,f,604.5],[0,0,1]])
 rays=[np.linalg.solve(k,m[:,:2])for m in mm]
 a=[r[:,0]/np.linalg.norm(r[:,0])for r in rays];return [float(np.degrees(np.arccos(np.clip(a[0]@a[1],-1,1)))),*[float(np.linalg.norm(r[:,0])/np.linalg.norm(r[:,1]))for r in rays],float(f)],np.sqrt(ff).tolist()
val,f=fit(list(original.values()))
print(val,f)
results={}
for face,bb in second.items():
 q1=original[face];q2=bb['panel']
 mapped={}
 for n,k in [('transom','upper_transom_outer'),('sill','projecting_sill_top'),('apron','red_scalloped_apron_bottom')]:
  q=marks['faces'][face]['marks'][k]['source_px'];pred=project(H(q1,q2),q);target=np.array(bb[n])
  mapped[n]=dict(first_pixels=q,second_pixels=bb[n],predicted_from_face=pred.round(2).tolist(),residual_pixels=np.linalg.norm(pred-target,axis=1).round(2).tolist())
 results[face]=dict(first_panel=q1,second_panel=q2,independently_read_details=mapped)
rng=np.random.default_rng(229)
sample=[]
for _ in range(4000):
 points=np.array([original['left'][0],original['left'][1],original['centre'][1],original['left'][3],original['left'][2],original['centre'][2]])+rng.normal(0,1.35,(6,2))
 try:v,_=fit([points[[0,1,4,3]],points[[1,2,5,4]]]);sample.append(v)
 except AssertionError:pass
print(np.percentile(sample,[10,90],axis=0))
report={'subject':'山阴路229弄1号两面凸窗','first_source':marks['source'],'second_source':'https://www.toutiao.com/article/6984724111138243084/','first_pixels':[2082,1209],'second_pixels':[640,432],'source_view2_caption':'山阴路229弄1号；老房子爱好者','survey':results,'camera_assumptions':'Square pixels, centred principal point, zero skew. On each masonry panel the courses and vertical arrises are perpendicular; focal length comes from both homographies. The second view tests positions of architectural features using separate planar registrations.','first_per_face_focal_px':f,'fit_keys':['turn_degrees','oblique_width_over_datum_height','central_width_over_datum_height','common_focal_px'],'fit':val,'conditional_pixel_sensitivity':{'method':'4000 independent six-vertex resamplings with Gaussian perturbation 1.35 px on each picked ordinate. Shared arris points move together. Keep positive focal-length solutions. These intervals are conditional on the camera assumptions.','valid':len(sample),'percentiles_10_90':np.percentile(sample,[10,90],axis=0).round(4).tolist()},'drawing_units':'A datum height of 3.2 display units is an arbitrary reference. No independent absolute metric scale was supplied by either photograph.'}
(root/'229-two-view-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
