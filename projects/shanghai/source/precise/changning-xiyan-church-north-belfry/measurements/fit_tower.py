"""Fit the belfry's repeated openings and exterior corners across three photographs."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

HERE=Path(__file__).resolve().parent
# Image coordinates are in the re-scaled originals. The May courtyard frame is upright.
STATIONS={
    'june-court':([1700,1129],{
        'left_foot':[995,1058],'right_foot':[1201,1058],
        'left_head':[981,215],'right_head':[1133,216],'return_head':[968,281],
        'sill_l':[1013,360],'sill_r':[1122,361],
        'tip_l':[1025,255],'tip_m':[1063,256],'tip_r':[1100,257],
        'slit_high':[1036,556],'slit_mid':[1084,703],'slit_low':[1135,857]}),
    'may-court':([1133,1700],{
        'left_foot':[497,1009],'right_foot':[671,1006],
        'left_head':[521,201],'right_head':[674,200],
        'sill_l':[541,355],'sill_r':[650,356],
        'tip_l':[555,241],'tip_m':[593,240],'tip_r':[630,239],
        'slit_high':[552,550],'slit_mid':[590,687],'slit_low':[629,827]}),
    'may-river':([1700,1133],{
        'left_head':[1225,143],'right_head':[1310,164],'return_head':[1151,168],
        'sill_l':[1243,265],'sill_r':[1300,275],
        'tip_l':[1250,179],'tip_m':[1271,183],'tip_r':[1291,189],
        'side_tip_l':[1167,196],'side_tip_m':[1185,191],'side_tip_r':[1205,184]})}
STATIONS['winter-river']=([800,533],{
    'left_head':[566,96],'right_head':[601,100],'return_head':[547,107],
    'sill_l':[574,140],'sill_r':[598,141],
    'tip_l':[576,110],'tip_m':[584,110],'tip_r':[593,111],
    'side_tip_l':[551,117],'side_tip_m':[556,114],'side_tip_r':[561,112],
    'slit_high':[580,192],'slit_mid':[590,227],'slit_low':[600,262],
    'side_mid':[558,230],'side_low':[565,262]})
for key,cap,tip in [
    ('june-court',(1044,147),(1041,96)),('may-court',(603,114),(603,30)),
    ('may-river',(1233,80),(1232,22)),('winter-river',(572,72),(572,53))]:
    STATIONS[key][1].update(cap=cap,cross_top=tip)
BASE=3.6
def surface(side,u,z,depth,h,top):
    half=BASE/2+(top-BASE)*.5*z/h
    return [((u,-half-depth), (half+depth,u),(-u,half+depth),(-half-depth,-u))[side][i]for i in range(2)]+[z]
def geometry(p):
    h,top,sill,tip,outer,step=p[:6]
    pts={'left_foot':[-BASE/2,-BASE/2,0],'right_foot':[BASE/2,-BASE/2,0],
         'left_head':[-top/2,-top/2,h],'right_head':[top/2,-top/2,h],'return_head':[-top/2,top/2,h]}
    for k,u in zip(('l','m','r'),(-step,0,step)):
        pts['tip_'+k]=surface(0,u,tip,0,h,top)
        pts['side_tip_'+k]=surface(3,u,tip,0,h,top)
    for k,u in [('l',-outer),('r',outer)]:
        pts['sill_'+k]=surface(0,u,sill,0,h,top)
    for i,k in enumerate(('high','mid','low')):
        pts['slit_'+k]=surface(0,p[6+i*2],p[7+i*2],.007,h,top)
    for i,k in [(1,'side_mid'),(2,'side_low')]:
        pts[k]=surface(3,p[6+i*2],p[7+i*2],.007,h,top)
    pts['cap']=[0,0,h+p[12]]
    pts['cross_top']=[0,0,h+p[13]]
    return pts
def camera(p,frame):
    x,y,z,yaw,tilt,roll,focal=p
    eye=np.array([x,y,z]);right=np.array([np.cos(yaw),-np.sin(yaw),0])
    flat=np.array([np.sin(yaw),np.cos(yaw),0]);up=np.array([0,0,1])
    toward=flat*np.cos(tilt)+up*np.sin(tilt);sky=up*np.cos(tilt)-flat*np.sin(tilt)
    u=right*np.cos(roll)+sky*np.sin(roll);v=right*np.sin(roll)-sky*np.cos(roll)
    def row(a):return np.r_[a,-a@eye]
    return np.stack([frame[0]/2*row(toward)+focal*row(u),frame[1]/2*row(toward)+focal*row(v),row(toward)])
def project(m,pt):
    h=m@[*pt,1]
    return h[:2]/h[2]
HOLD={('june-court','tip_m'),('may-court','tip_l'),('may-court','slit_mid'),('may-river','tip_m'),('may-river','side_tip_m'),('winter-river','slit_mid'),('winter-river','side_mid'),('winter-river','cap')}
def fit():
    initial=[15,3.43,11.95,14.05,1.15,.78,-.84,8.3,0.,6.2,.84,3.7,2.42,4.0]
    lo=[9,2.7,6.2,7,.75,.48,-1.25,4,-.55,2,.1,1,1.35,2.4]
    hi=[23,3.8,19,21,1.7,1.12,-.1,15,.55,13,1.4,10,3.4,5.3]
    stations=[[-3,-24,1.63,-.025,.3,0,1450],[1.4,-27,1.65,-.08,.16,0,1510],[-43,-39,1.65,.61,.025,0,2070],[-38,-52,1.65,.43,.015,0,1050]]
    for s in stations:
        initial+=s;lo +=[-140,-160,.4,-1.7,-.42,-.12,420];hi +=[65,-4,4.6,1.7,1,.12,7000]
    def residual(p,report=False):
        pts=geometry(p);err=[];res={}
        for i,(name,(frame,features))in enumerate(STATIONS.items()):
            pose=p[14+7*i:21+7*i];m=camera(pose,frame);rows=[]
            for k,uv in features.items():
                delta=project(m,pts[k])-uv;used=(name,k)not in HOLD
                if used:err.extend(delta)
                rows.append(dict(feature=k,uv=uv,world=pts[k],used=used,error_px=float(np.linalg.norm(delta))))
            err.extend([(pose[2]-1.65)/.34,pose[5]/.012])
            res[name]=dict(frame=frame,projection=m.tolist(),eye=pose[:3].tolist(),pose=pose.tolist(),points=rows)
        err.extend([(p[1]-3.5)/.14,(p[6]+p[10])/.14,p[8]/.13])
        return res if report else err
    solve=least_squares(residual,initial,bounds=(lo,hi),x_scale='jac',loss='soft_l1',f_scale=3,max_nfev=1800)
    p=solve.x
    return dict(base_width_conditional_m=BASE,scope='Square shaft. The 3.60 m ground width fixes only scale. Unmeasured upper width, shaft height, stair lights and belfry aperture levels are solved jointly. Some ground points are vegetation-obscured.',parameters=p[:14].tolist(),stations=residual(p,True))
if __name__=='__main__':
    data=fit()
    (HERE/'tower-stations.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(data['parameters'])
    for k,v in data['stations'].items():print(k,[(r['feature'],round(r['error_px'],1))for r in v['points']])
