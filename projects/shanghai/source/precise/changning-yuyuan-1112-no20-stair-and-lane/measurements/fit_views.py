"""Recover the façade-plane camera from vanishing lines and a conditional door height."""
from pathlib import Path
import json, numpy as np
from scipy.optimize import least_squares
D=Path(__file__).absolute().parent
read=lambda x:json.loads((D/x).read_bytes())
X=[((35,181),(92,119)),((41,190),(94,128)),((30,331),(277,222)),((29,344),(276,246)),((27,348),(276,257)),((80,324),(119,309)),((156,233),(199,214)),((145,411),(172,412)),((125,453),(283,479)),((27,452),(127,489))]
Z=[((39,188),(23,446)),((73,321),(68,466)),((131,89),(124,483)),((249,3),(295,494)),((170,57),(169,104)),((182,176),(183,219)),((52,369),(44,454)),((158,321),(155,407))]
def fit_vp(lines):
 # robust signed perpendicular pixel distance per segment endpoint at its own observed length
 def f(p):
  res=[]
  for a,b in lines:
   a,b=np.array(a),np.array(b);mid=(a+b)/2;q=p-mid;d=(b-a);res.append(np.cross(q,d)/np.linalg.norm(q))
  return np.array(res)
 return least_squares(f,[0,0],loss='soft_l1',f_scale=1.).x
def exterior():
 vx=fit_vp(X);vz=fit_vp(Z); u=np.array([187.,249.5]);f=np.sqrt(-(vx-u)@(vz-u));print('vp',vx,vz,'f',f)
 K=np.array([[f,0,u[0]],[0,f,u[1]],[0,0,1.]])
 def unit(p):
  q=np.linalg.solve(K,[*p,1]);return q/np.linalg.norm(q)
 ex=-unit(vx);ez=unit(vz);ey=np.cross(ez,ex);r=np.column_stack((ex,ey,ez));print('R',r,np.linalg.det(r))
 # left door outer right jamb tracked at its head and sill; local X=0, ground at pavement.
 base,top=(55,458),(62,369)
 q0=np.linalg.solve(K,[*base,1]);q1=np.linalg.solve(K,[*top,1]);ab=np.linalg.lstsq(np.column_stack((q1,-q0)),ez*2.12,rcond=None)[0]
 trans=ab[1]*q0;P=K@np.column_stack((r,trans));C=-r.T@trans
 print('C',C,'scales',ab)
 return P,C,r,K
def plane(P,uv,y=0):
 m=np.column_stack((P[:,0],P[:,2],P[:,3]+y*P[:,1]));q=np.linalg.solve(m,[*uv,1]);return q[:2]/q[2]
if __name__=='__main__':
 P,C,r,K=exterior()
 for a in [(27,449),(50,451),(62,369),(100,409),(158,408),(155,322),(279,478),(265,226),(120,62),(40,185),(178,8),(18,441),(20,347)]:print(a,plane(P,a).round(2))
def interior():
    # Read the dark leading edge of each visible terrazzo tread at column 45, and its end below the balusters.
    horizontal_ordinate=[436,380,342,304,275,249,226,207,190,174,162,149,139,129]
    right_ends=[[228,397],[207,359],[189,328],[175,296],[163,268],[151,245],[142,225],[134,205],[128,189],[121,174],[116,162],[111,151],[107,141],[103,131]]
    def matrix(v):
        cx,cy,cz,yaw,up,roll,f,run,rise=v
        d=np.array([np.sin(yaw)*np.cos(up),np.cos(yaw)*np.cos(up),np.sin(up)]);right=np.cross(d,[0,0,1.]);right/=np.linalg.norm(right)
        down=np.cross(d,right);R=np.array([right*np.cos(roll)+down*np.sin(roll),-right*np.sin(roll)+down*np.cos(roll),d])
        K=np.array([[f,0,187.],[0,f,249.5],[0,0,1.]])
        C=np.array([cx,cy,cz]);return K@np.column_stack((R,-R@C)),C,R,K
    # Single-image scale is conditional on a domestic riser. Width is bounded by the visible inner edge of the left wall.
    def error(v):
        P,C,R,K=matrix(v);run,rise=v[-2:];r=[]
        def pix(x,y,z):
            a=P@[x,y,z,1];return a[:2]/a[2]
        for j,(yy,end) in enumerate(zip(horizontal_ordinate,right_ends)):
            a=pix(.55,j*run,(j+1)*rise);b=pix(-.65,j*run,(j+1)*rise)
            r.extend((a-end)*.7);r.append(a[1]+(45-a[0])*(b[1]-a[1])/(b[0]-a[0])-yy)
        r.extend([(v[6]-401)*.08,(run-.268)*28,(rise-.167)*150,(C[2]-1.52)*6,v[5]*6])
        return r
    pars=least_squares(error,[.43,-1.42,1.50,-.4,-.10,.02,400,.268,.167],bounds=([-2.1,-3.,.9,-.9,-.65,-.3,310,.215,.152],[1.4,-.50,2.07,.4,.60,.3,510,.34,.19]),loss='soft_l1',f_scale=2.3).x
    P,C,R,K=matrix(pars); shift=np.array([-1.00,6.,0.]);C=C+shift; P=K@np.column_stack((R,-R@C))
    return P,C,R,K,dict(right_ends=right_ends,left_scan_x45_original_y=horizontal_ordinate,rise_m=pars[-1],run_m=pars[-2],wall_lateral_m=[-.65,.64],study_translation=shift.tolist(),geometric_residual_px=[round(float(x),2) for x in error(pars)[:-6]])
def register():
    P,C,R,K=exterior();Pi,Ci,Ri,Ki,notes=interior();nodes={}
    for name,pm,c,r,k,raw in [('photo-lane',P,C,R,K,{'facade_horizontal_lines':X,'vertical_lines':Z,'door_jamb_height_assumed_m':2.12,'scale_interval_m':[1.98,2.26]}),('photo-stair',Pi,Ci,Ri,Ki,notes)]:
        nodes[name]=dict(C=c.tolist(),R=r.tolist(),K=k.tolist(),P=pm.tolist(),size=[375,500],original_reference=name,readings=raw,source='https://4travel.jp/travelogue/11082493',photographer='中国の風景',image_date='2015-11-16')
    (D/'two-stations.json').write_text(json.dumps(nodes,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':register()
