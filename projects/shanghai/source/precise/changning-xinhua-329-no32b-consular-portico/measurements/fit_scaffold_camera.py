"""Register the third, 433 x 325 court photograph embedded on planning atlas page 10."""
from pathlib import Path
import json
import math
import numpy as np

HERE=Path(__file__).absolute().parent
book=json.loads((HERE/'portico-camera-pair.json').read_bytes())
# Capitals, feet, projecting cornice and the jambs remain visible around the scaffold.
# Features covered by workers, bamboo, plants, or an open door leaf have been omitted.
front={
'left shaft foot centre':(177,257),'right shaft foot centre':(248,260),
'left shaft capital centre':(181,177),'right shaft capital centre':(249,180),
'balustrade left top':(177,125),'balustrade right top':(248,132),
'balustrade left foot':(177,140),'balustrade right foot':(248,146),
'frieze left bottom':(170,165),'frieze right bottom':(256,172),
'right abacus outer tip':(257,177),'left abacus outer tip':(171,173)}
# The historic lower-jamb points are obscured by temporary boards on the work site.
rear={'left spring of fanlight':(193,207),'right spring of fanlight':(226,209),
'apex of inner fanlight':(209,191)}
points=[]
for key,obs in [('front',front),('rear',rear)]:
    for row in book[key+'_controls']:
        name=row['feature']
        if name in obs:points.append((name,row['xyz'],obs[name],key))
xyz=np.array([r[1] for r in points]);uv=np.array([r[2] for r in points])
def rotation(omega):
    a=np.linalg.norm(omega)
    x,y,z=omega
    k=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    return np.eye(3)+np.sinc(a/np.pi)*k+.5*np.sinc(a/(2*np.pi))**2*k@k

def camera(state):
    f=np.exp(state[0])
    K=np.array([[f,0,216],[0,f,162],[0,0,1.]])
    R=rotation(state[1:4])@np.array([[1.,0,0],[0,0,-1.],[0,1.,0]])
    return K,R,state[4:7]

def residual(state):
    K,R,C=camera(state)
    ph=(xyz-C)@R.T@K.T
    # The focal prior prevents an implausible long-lens fit to the largely planar controls.
    return np.r_[((ph[:,:2]/ph[:,2,None]-uv)/2.).ravel(),(state[0]-math.log(430))/1.3,(state[6]-1.5)/.17]
state=np.array([math.log(430),.03,.01,0.,-.15,-15.,1.75])
damping=.01
def cost(r):return np.sum(np.sqrt(1+r*r)-1)
for _ in range(220):
    r=residual(state);step=1e-5*np.maximum(1.,abs(state));eye=np.eye(len(state))
    J=np.column_stack([(residual(state+step[i]*eye[i])-r)/step[i]for i in range(len(state))])
    weight=1/np.sqrt(1+r*r)
    a=J.T@(J*weight[:,None])
    delta=np.linalg.solve(a+damping*np.diag(np.maximum(1,np.diag(a))),-J.T@(r*weight))
    nxt=state+delta
    if np.log(220)<nxt[0]<np.log(1200) and -40<nxt[5]<-7 and cost(residual(nxt))<cost(r):
        state=nxt;damping=max(1e-9,damping*.4)
        if np.linalg.norm(delta)<1e-8:break
    else:
        damping*=3
        if damping>1e11:break
K,R,C=camera(state)
errors=residual(state)[:-2].reshape((-1,2))*2
data=dict(size=[433,325],K=K.tolist(),R=R.tolist(),C=C.tolist(),source='http://www.dayuehs.com/pdf/xmyh02.pdf',page=10,pdf_object=112,unfitted_floor_controls=[[192,258],[226,260]],camera_height_prior_m=[1.5,.17],image_sha256='8557b65d6270c8579946094a6bddafdfeda7e5e5f3e04314b72004d172cc26e0',rms_px=float(np.sqrt(np.mean(np.sum(errors**2,axis=1)))),controls=[dict(feature=p[0],xyz=p[1],pixel=p[2],plane=p[3],residual_px=round(float(np.linalg.norm(e)),3))for p,e in zip(points,errors)],limits='Original 433 x 325 photograph. Bamboo, vegetation and scaffolding partly hide the courtyard and the foot of the doorway. Camera height uses a standing courtyard-camera prior, since the independently fitted result is ill-conditioned. The inter-column world span retains the first camera pair’s nominal door-height scale.')
(HERE/'scaffold-camera.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(round(data['rms_px'],2),round(K[0,0],1),C,[v['residual_px'] for v in data['controls']])
