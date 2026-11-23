"""Fit two independent south-elevation views to marked architectural features."""
from pathlib import Path
import sys, json, math
import numpy as np
from scipy.optimize import least_squares
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'source'))
from model import vertex, RADIUS, HALF_ARC, BASE, UPPER, ROOF
def fit(name,source,which,box,points,initial):
    uv=np.array([r[4:] for r in points],float)
    xyz=np.array([vertex(*r[1:4]) for r in points])
    def projection(par, output=False):
        ex,ey,ez,tx,tz,logf,roll=par
        eye=np.array([ex,ey,ez]);target=np.array([tx,0,tz])
        forward=target-eye;forward/=np.linalg.norm(forward)
        r=np.cross(forward,[0,0,1]);r/=np.linalg.norm(r);u=np.cross(r,forward)
        right=r*np.cos(roll)+u*np.sin(roll);up=-r*np.sin(roll)+u*np.cos(roll)
        f=np.exp(logf)
        if output:return eye.tolist(),target.tolist(),up.tolist(),f
        vectors=xyz-eye; depth=vectors@forward
        return np.column_stack((box[0]/2+f*(vectors@right)/depth,box[1]/2-f*(vectors@up)/depth))
    size=len(xyz);held=[2,size-2];idx=[i for i in range(size) if i not in held]
    def residual(par):
        return np.r_[(projection(par)[idx]-uv[idx]).ravel(), .22*(par[2]-initial[2]), .12*(par[1]-initial[1]),3.5*par[-1]]
    bounds=([-100,-180,-10,-20,-14,math.log(50),-.18],[100,-3,125,20,30,math.log(5000),.18])
    if name=='photo-garden-lawn':
        bounds[0][2]=.7; bounds[1][2]=2.5; bounds[1][1]=-23
    out=least_squares(residual,initial,bounds=bounds,max_nfev=2300)
    xy=projection(out.x);error=np.linalg.norm(xy-uv,axis=1)
    eye,target,up,f=projection(out.x,True)
    # Crop the whole-building source to the counted loggia segment for display.
    left,top,width,height=which;distance=np.linalg.norm(np.array(eye)-target)
    cam=dict(name=name,label=source['label'],eye=eye,target=target,world_up=up,width_m=distance*width/f,
        width=width,height=height,principal_point_edge_px=[box[0]/2-left,box[1]/2-top])
    record=dict(source=source,crop=[left,top,width,height],image_size=box,calibration='单幅透视拟合，绝对尺度与站位均为估计。留出两点独验。',eye=eye,target=target,focal_pixels=f,roll_rad=out.x[-1],
        rms_px=float(np.sqrt(np.mean(error[idx]**2))),holdout_rms_px=float(np.sqrt(np.mean(error[held]**2))),
        points=[dict(feature=r[0],local_position_m=xyz[i].tolist(),image_px=uv[i].tolist(),reprojection_px=xy[i].tolist(),error_px=float(error[i]),is_holdout=i in held) for i,r in enumerate(points)])
    return cam,record

aerial=[('roof west end',-6.15,0,12.48,191,144),('roof east end',6.15,0,12.48,282,143),('roof front middle',0,0,12.48,236,151),('upper central sill',0,0,8.21,236,186),('upper central crown',0,0,10.82,236,166),('upper east inner pier',2.07,0,8.21,252,184),('upper east outer pier',4.05,0,8.21,266,181),('upper west inner pier',-2.07,0,8.21,219,185),('lower east spring',5.91,0,5.38,279,201),('lower centre crown',0,0,6.18,236,204),('lower east pier foot',2.14,0,2.6,251,230),('basement light crown',-.54,-2.63,1.12,235,253),('upper terrace centre belt',0,-.15,11.39,236,162)]
ground=[('terrace crown outer east',6.15,0,12.48,600,210),('terrace crown east inner',2.07,0,12.48,525,208),('upper first side crown',3.06,0,10.82,546,249),('upper outer crown',5.1,0,10.82,585,250),('upper central crown',0,0,10.82,486,245),('upper right inner pier sill',2.07,0,8.21,525,301),('upper right outer pier sill',4.05,0,8.21,563,301),('upper east end at sill',6.15,0,8.21,600,300),('upper centre belt east inner pier',2.07,-.16,6.94,525,321),('lower east bay crown',4.145,0,6.18,562,343),('lower east inner pier',2.14,0,2.60,523,401),('lower east exterior pier',6.15,0,2.60,601,400),('upper first outer spring',3.90,0,10.33,560,258)]
specs=[('photo-garden-high',dict(label='高位正照 · 花园弧廊',url='https://www.thepaper.cn/newsDetail_forward_12580231',image='https://imagepphcloud.thepaper.cn/pph/image/130/566/295.jpg'),(161,130,157,153),(488,349),aerial,[1.,-56.,29.,1.,9.,math.log(420),0]),('photo-garden-lawn',dict(label='2024年草坪视角 · 双层拱廊',url='https://sh.people.com.cn/n2/2024/1029/c134768-41024190.html'),(344,185,296,295),(1000,666),ground,[1.,-45.,1.85,.8,6.,math.log(930),0])]
def cam(n,l,e,t,w):return dict(name=n,label=l,eye=e,target=t,width_m=w,width=900,height=720)
cams=[cam('overview','南花园双层弧廊',[14,-23,14],[0,-.4,6.0],19.)];evidence={}
for spec in specs:
    c,r=fit(*spec);cams.append(c);evidence[c['name']]=r
cams.extend([cam('west-oblique','侧面 · 拱间回折',[-17,-17,7.1],[0,-1.0,5.8],19.),cam('ground-arcade','三拱敞廊与石柱',[1,-16,5],[0,-1.1,4.5],13.8),cam('upper-windows','五扇弧顶窗与红砖饰带',[.8,-15,9.8],[0,-.9,9.1],13.6),cam('pierced-apron','窗下四叶透花',[4.5,-7.4,8.1],[2.5,-1.25,7.82],4.9),cam('terrace','上层露台与瓶栏',[8,-13,16.8],[0,-.5,11.74],14.8),cam('garden-stairs','分向花园双梯与栏板',[10,-14,5.7],[1.0,-1.2,1.75],14.4)])
(ROOT/'source/cameras.json').write_text(json.dumps(cams,ensure_ascii=False,indent=2)+'\n')
(ROOT/'measurements/photographic-registration.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
for k,r in evidence.items():print(k,round(r['rms_px'],3),round(r['holdout_rms_px'],3),r['eye'])
