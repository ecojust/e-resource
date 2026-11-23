"""Register the fourth photo from the campus side. Rear eave heights and plaque are held out."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).resolve().parent
from fit_gate import pose
def solve():
    d=json.loads((HERE/'registered-gate.json').read_bytes());g=d['geometry']
    a,b,z,h=g['outer_post_x'],g['inner_post_x'],g['threshold_z'],g['beam_bottom']
    rows=[]
    def add(name,xy,xyz,train):rows.append((name,xy,xyz,train))
    for n,(x,uv,base) in enumerate(zip([a,b,-b,-a],[(228,300),(313,300),(515,300),(605,300)],[(228,512),(313,515),(514,515),(604,516)])):
        add('post head '+str(n+1),uv,[x,.142,h],True)
        add('post foot '+str(n+1),base,[x,.142,z],True)
    add('left ridge ornament base', [207,117],[2.62,g['ridge_y'],g['ridge_z']+.14],False)
    add('right ridge ornament base',[624,119],[-2.62,g['ridge_y'],g['ridge_z']+.14],False)
    for i,(u,x) in enumerate(zip([(58,120),(773,108)],[4.05,-4.05])):
        add('near eave corner '+str(i+1),u,[x,g['rear_beak_y'],g['roof_tip_z']],False)
    for n,(u,x,v) in enumerate(zip([(319,216),(510,216),(508,281.5),(320,281.5)],[1.122,-1.122,-1.122,1.122],[1,1,0,0])):
        add('rear plaque corner '+str(n+1),u,[x,.52 if v else .33,3.86 if v else 3.14],False)
    for u,x in zip([(298,546),(522,546)],[g['step_half_x'],-g['step_half_x']]):
        add('bottom tread end',u,[x,1.258,0],False)
    uv=np.array([v for _,v,_,_ in rows]);xyz=np.array([q for _,_,q,_ in rows]);mask=np.array([t for *_,t in rows])
    def proc(v,final=False):
        c=v[:3];r=Rotation.from_rotvec(v[3:6]).as_matrix();f=np.exp(v[6]);k=np.array([[f,0,399.5],[0,f,302.],[0,0,1.]])
        px=(xyz-c)@r.T@k.T;delta=px[:,:2]/px[:,2,None]-uv
        if final:return dict(width=800,height=605,crop=[12,47,792,568],C=c.tolist(),K=k.tolist(),R=r.tolist(),P=(k@np.column_stack((r,-r@c))).tolist(),points=[dict(feature=n,original=u,world=q,fit=t,error_px=round(float(v),2))for (n,u,q,t),v in zip(rows,np.linalg.norm(delta,axis=1))],scale_note='Fixed post spacing and 8.10 m roof span of the front-side solution. The rear camera focal length is estimated.')
        return list(delta[mask].ravel()/3.)+[(c[2]-1.62)/.27,(v[6]-np.log(810))/.32]
    eye=np.array([.25,11.,1.64]);init=np.r_[eye,pose(eye,np.array([.03,0.,2.65])),np.log(810)]
    result=least_squares(proc,init,loss='soft_l1',x_scale='jac')
    st=proc(result.x,True);d['stations']['editorial-reverse']=st
    crop={'commons-2006':[160,92,1430,1038],'school-front':[30,8,397,258],'school-postcard':[20,10,430,283]}
    for key,frame in crop.items():d['stations'][key]['crop']=frame
    (HERE/'four-gate-stations.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    print(st['C'],[p['error_px']for p in st['points']])
if __name__=='__main__':solve()
