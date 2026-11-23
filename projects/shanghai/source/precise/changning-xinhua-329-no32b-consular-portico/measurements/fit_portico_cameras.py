from pathlib import Path
import numpy as np,json
def rotmat(r):
 a=np.linalg.norm(r);x,y,z=r
 skew=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
 if a<1e-8:return np.eye(3)+skew+skew@skew*.5
 return np.eye(3)+np.sin(a)/a*skew+((1.-np.cos(a))/(a*a))*(skew@skew)
def rotvec(R):
 theta=np.arccos(np.clip((R.trace()-1)*.5,-1.,1.));v=np.array([R[2,1]-R[1,2],R[0,2]-R[2,0],R[1,0]-R[0,1]])
 return v*(theta/(2*np.sin(theta))) if theta>1e-7 else v*.5
def fit(fun,seed,lo,hi):
 x=np.clip(seed,lo,hi);damping=.01
 def cost(r):return np.sum(np.sqrt(1+(r/1.4)**2)-1)
 for i in range(360):
  r=fun(x);weight=1/np.sqrt(1+(r/1.4)**2);scale=np.maximum(1.,abs(x))*1e-5
  J=np.column_stack([(fun(x+np.identity(len(x))[j]*scale[j])-r)/scale[j] for j in range(len(x))])
  lhs=J.T@(J*weight[:,None]);step=np.linalg.solve(lhs+damping*np.diag(np.maximum(1.,np.diag(lhs))),-(J.T@(r*weight)))
  xn=np.clip(x+step,lo,hi)
  if cost(fun(xn))<cost(r):
   if np.linalg.norm(xn-x)<1e-8:break
   x=xn;damping=max(damping*.36,1e-9)
  else:
   damping*=3
   if damping>1e12:break
 return x
s=Path(__file__).absolute().parents[1]
# The portrait was inspected at 537 x 805. The wide station was independently
# inspected on a double-size crop of (120,125) to (410,360) of the 579 x 386 original.
front=[
('left shaft foot centre',(124,638),(170,378)),('right shaft foot centre',(427,638),(360,379)),
('left shaft capital centre',(126,294),(197,174)),('right shaft capital centre',(422,294),(365,178)),
('balustrade left top',(111,84),(196,61)),('balustrade right top',(436,83),(373,76)),
('balustrade left foot',(111,146),(186,90)),('balustrade right foot',(437,145),(373,102)),
('frieze left bottom',(99,251),(182,150)),('frieze right bottom',(450,251),(377,159)),
('right abacus outer tip',(458,261),(381,167)),('left abacus outer tip',(89,261),(176,162))]
wall=[
('left door jamb lower',(213,630),(221,397)),('right door jamb lower',(340,630),(310,397)),
('left spring of fanlight',(213,398),(222,248)),('right spring of fanlight',(340,398),(310,250)),
('apex of inner fanlight',(276,329),(269,209)),('white plaque upper left',(37,418),(123,249)),
('white plaque upper right',(95,418),(160,251)),('white plaque lower left',(37,464),(120,278)),
('white plaque lower right',(95,464),(157,280))]
u1=lambda p:np.array(p)*np.array([1280/537,1919/805])
u2=lambda p:np.array(p)*.5+np.array([120,125])
def homography(x,y):
 A=[]
 for (u,v),(p,q) in zip(x,y):A.extend([[u,v,1,0,0,0,-p*u,-p*v,-p],[0,0,0,u,v,1,-q*u,-q*v,-q]])
 return np.linalg.svd(np.asarray(A))[2][-1].reshape(3,3)
def map_h(h,pts):
 p=np.c_[pts,np.ones(len(pts))]@h.T;return p[:,:2]/p[:,2:]
# The span is a provisional scale. A second pass below normalizes the door leaf.
nominal=np.array([[-1.4,.68],[1.4,.68],[-1.4,3.86],[1.4,3.86]])
front1=np.array([u1(a)for _,a,_ in front]);front2=np.array([u2(b)for _,_,b in front])
wall1=np.array([u1(a)for _,a,_ in wall]);wall2=np.array([u2(b)for _,_,b in wall])
xz=map_h(homography(front1[:4],nominal),front1)
front3=np.column_stack((xz[:,0],np.zeros(len(xz)),xz[:,1]))
centres=[np.array([639.5,959.]),np.array([289.,192.5])]
def init(uv,centre,f):
 inv=np.linalg.inv([[f,0,centre[0]],[0,f,centre[1]],[0,0,1]]);A=inv@homography(xz,uv)
 if A[2,2]<0:A=-A
 scale=np.mean([np.linalg.norm(A[:,0]),np.linalg.norm(A[:,1])]);a,b,t=(A/scale).T
 r=np.column_stack([a,np.cross(b,a),b]);u,v,h=np.linalg.svd(r);rot=u@h
 return np.r_[np.log(f),rotvec(rot),-rot.T@t]
def camera(vec,centre):
 f=np.exp(vec[0]);R=rotmat(vec[1:4]);C=vec[4:7]
 K=np.array([[f,0,centre[0]],[0,f,centre[1]],[0,0,1]])
 return K,R,C
def project(cam,v):
 K,R,C=cam;q=(v-C)@R.T@K.T;return q[:,:2]/q[:,2:]
def back(cam,uv,pos):
 K,R,C=cam;rays=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T@R
 return C+rays*((pos-C[1])/rays[:,1,None])
def residual(x):
 first,second=(camera(x[i*7:i*7+7],centres[i])for i in (0,1))
 pts=back(first,wall1,x[-1])
 return np.r_[((project(first,front3)-front1)/2.7).ravel(),(project(second,front3)-front2).ravel(),(project(second,pts)-wall2).ravel(),(x[0]-np.log(2300))/1.25,(x[7]-np.log(490))/.8]
seed=np.r_[init(front1,centres[0],2300),init(front2,centres[1],490),1.12]
low=np.full(len(seed),-np.inf);hi=-low;low[[0,7,14]]=[np.log(550),np.log(180),.25];hi[[0,7,14]]=[np.log(15000),np.log(2700),3.]
answer=fit(residual,seed,low,hi)
cams=[camera(answer[i*7:i*7+7],centres[i])for i in (0,1)]
door=back(cams[0],np.array([u1((274,409)),u1((274,630))]),answer[-1])
factor=2.10/(door[0,2]-door[1,2])
metrics=[]
for i,(cam,uv)in enumerate(zip(cams,[front1,front2])):
 errors=np.linalg.norm(project(cam,front3)-uv,axis=1);K,R,C=cam
 metrics.append(dict(size=[[1280,1919],[579,386]][i],K=K.tolist(),R=R.tolist(),C=(C*factor).tolist(),front_residual_px=errors.tolist()))
rearerr=np.linalg.norm(project(cams[1],back(cams[0],wall1,answer[-1]))-wall2,axis=1)
j=dict(stations=dict(portrait=metrics[0],wide=metrics[1]),front_controls=[dict(feature=n,portrait_px=a.tolist(),wide_px=b.tolist(),xyz=(v*factor).tolist())for (n,_,_),a,b,v in zip(front,front1,front2,front3)],rear_controls=[dict(feature=n,portrait_px=a.tolist(),wide_px=b.tolist(),xyz=(v*factor).tolist(),wide_residual_px=err)for (n,_,_),a,b,v,err in zip(wall,wall1,wall2,back(cams[0],wall1,answer[-1]),rearerr)],wall_y_m=answer[-1]*factor,scale_from_assumed_2_10_m_leaf=factor,limits='Absolute scale assumes a 2.10 m red door leaf from its sill to the transom. Lens centre is fixed at image centre. Front axis centres approximate curved shafts. The rear jamb and plaque are treated as one approximate wall plane.')
(s/'measurements/portico-camera-pair.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
print('scale',factor,'depth',j['wall_y_m'],'focals',[c[0][0,0]for c in cams],'front RMS',[np.sqrt(np.mean(np.array(c['front_residual_px'])**2))for c in metrics],'rear RMS',np.sqrt(np.mean(rearerr**2)),'C',[c['C']for c in metrics])
