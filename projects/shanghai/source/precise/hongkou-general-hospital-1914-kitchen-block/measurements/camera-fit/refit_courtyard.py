"""Calibrate the separate courtyard exposure from its two facade vanishing points and two continuous stone courses."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from scipy.optimize import least_squares
import cv2
cv2.setNumThreads(1)
w=Path(__file__).resolve().parent;path=Path(sys.argv[1])
img=cv2.imread(str(path),0);h,ww=img.shape;cx,cy=(ww-1)/2,(h-1)/2
segs=cv2.createLineSegmentDetector().detect(img)[0].reshape((-1,4));polygon=np.int32([[180,125],[612,40],[634,257],[595,351],[495,416],[203,402]])
def fit(vp,threshold):
    selected=[]
    for a,b,c,d in segs:
        ab=np.array([c-a,d-b]);m=np.array([(a+c)/2,(b+d)/2])
        if np.linalg.norm(ab)<17 or cv2.pointPolygonTest(polygon,tuple(float(v)for v in m),False)<0:continue
        direction=vp-m
        if abs(ab[0]*direction[1]-ab[1]*direction[0])/np.linalg.norm(direction)<threshold:selected.append((a,b,c,d))
    g=np.array(selected);aa=g[:,:2];bb=g[:,2:];step=bb-aa;mid=(aa+bb)/2
    def errors(v):
        direct=v-mid
        return (step[:,0]*direct[:,1]-step[:,1]*direct[:,0])/np.linalg.norm(direct,axis=1)
    result=least_squares(errors,vp,loss='soft_l1',f_scale=.23,x_scale='jac',max_nfev=1400).x
    return result,g,float(np.median(abs(errors(result))))
vps=[[-1050.,370.],[420.,-1830.]]
groups=[];err=[]
for i in range(2):
    init=np.array(vps[i])
    for t in [2.5,1.5,.95,.73,.63]:init,g,e=fit(init,t)
    vps[i]=init;groups.append(g.round(3).tolist());err.append(e)
pp=np.array([cx,cy]);f=float(np.sqrt(-np.dot(vps[0]-pp,vps[1]-pp)));K=np.array([[f,0,cx],[0,f,cy],[0,0,1]])
def vector(v):
    r=np.linalg.solve(K,[*v,1])
    return r/np.linalg.norm(r)
ex,ez=map(vector,vps);ey=np.cross(ez,ex);R=np.column_stack((ex,ey,ez))
def ray(p):return R.T@np.linalg.solve(K,[*p,1])
# Project the same stone courses to the visible eastern quoin with their vanishing directions.
def intersect(p,v,q,u):
    a=np.cross([*p,1],[*v,1]);b=np.cross([*q,1],[*u,1]);r=np.cross(a,b);return r[:2]/r[2]
vx,vz=vps;edge=[635.,238.]
base=intersect([451.,352.5],vx,edge,vz);band=intersect([487.,141.],vx,edge,vz)
targets=[(base,3.93),(band,17.29)]
# Both controls lie on the same vertical. Each contributes a 3-D ray; solve for their common camera.
mat=[];tar=[]
for uv,z in targets:
    r=ray(uv);p=np.array([1.14,11.33,z]);M=np.eye(3)-np.outer(r,r)/(r@r);mat.extend(M);tar.extend(M@p)
eye=np.linalg.lstsq(mat,tar,rcond=None)[0]
def cut(uv,axis=1,off=11.33):
    r=ray(uv);return eye+(off-eye[axis])/r[axis]*r
def project(p):
    q=K@R@(np.array(p)-eye);return q[:2]/q[2]
if __name__=='__main__':
    print('vp',vps,'f',f,'lines',list(map(len,groups)),'res',err,'anchors',base,band,'eye',eye,'edge controls',cut(base),cut(band),flush=True)
    print('top cornice, upper windows, ground:',*[np.round(cut(uv),2).tolist()for uv in [(616,26),(453,79),(579,192),(575,350),(452,418),(214,415)]],flush=True)
    data=dict(source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),native_size=[ww,h],K=K.tolist(),R=R.tolist(),eye=eye.tolist(),vps=[v.tolist()for v in vps],retained_lines=groups,median_displacements_px=err,anchors=[{'pixel':p.tolist(),'xyz':[1.14,11.33,z]}for p,z in targets],method='The separate court photograph uses a centred principal point. Orthogonality between the steel jambs and stone courses supplies the focal length. The ground-floor belt and upper pale belt locate the eastern rear quoin and fix metric scale. Little of the west closure is visible.')
    (w/'dai-court-camera.json').write_text(json.dumps(data,indent=2)+'\n')
