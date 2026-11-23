"""Fit the photographed window heads and tall parallel projection lines to a local display scale."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

root = Path(__file__).resolve().parents[1]
# Coordinates are in a 1000 by 562 reading of the 5312 by 2988 original.
# Left spring, uppermost visible glass, right spring. The first left spring is partly behind iron.
observed = np.array([[[255.2,331.0],[282.0,296.6],[307.2,320.7]],
                     [[329.0,325.3],[361.2,284.0],[389.8,314.3]],
                     [[414.4,311.0],[450.4,270.4],[482.8,299.5]]])
verticals=[[[485.5,145],[487.6,298]],[[252,332],[249,358]]]
angles=np.linspace(0,np.pi,721)

def camera(v):
    f,yaw,pitch,roll,ex,ey,ez=v[:7]
    forward=np.array([np.sin(yaw)*np.cos(pitch),np.cos(yaw)*np.cos(pitch),np.sin(pitch)])
    right=np.array([np.cos(yaw),-np.sin(yaw),0])
    down=np.cross(forward,right)
    r=right*np.cos(roll)+down*np.sin(roll)
    d=down*np.cos(roll)-right*np.sin(roll)
    rot=np.array([r,d,forward])
    k=np.array([[f,0,500],[0,f,281],[0,0,1]])
    return k@np.column_stack((rot,-rot@np.array([ex,ey,ez])))

def pixels(p,xyz):
    pts=(p@np.column_stack((xyz,np.ones(len(xyz)))).T).T
    return pts[:,:2]/pts[:,2,None]

def shapes(v):
    return zip([v[7],0.,v[8]],[v[9],.75,v[10]])

def predict(v):
    p=camera(v); rows=[]
    for cx,rx in shapes(v):
        xyz=np.column_stack((cx+rx*np.cos(angles),np.full(len(angles),.105),rx*v[11]*np.sin(angles)))
        uv=pixels(p,xyz);rows.append([uv[-1],uv[np.argmin(uv[:,1])],uv[0]])
    return np.array(rows)

def errors(v):
    err=(predict(v)-observed).ravel().tolist()
    H=camera(v)
    for a,c in verticals:
        l=np.cross([*a,1],[*c,1]);center=(np.array(a)+c)/2
        vv=H[:,2]
        # Compare finite line endpoints rather than weighing a far-away vanishing point.
        direction=vv[:2]-center*vv[2];direction/=np.linalg.norm(direction)
        uv=(np.array(c)-a)@direction
        err.append(np.linalg.norm(np.cross(np.array([*direction,0]),np.array([*(np.array(c)-a),0])))*np.sign(l@vv))
    return [*err,(v[0]-741.)/35,(v[9]-.75)/.05,(v[10]-.75)/.05,(v[11]-1.)/.10]
fit=least_squares(errors,[740,-.67,.15,0,8.,-13.,-2.,-2.00,2.05,.75,.75,1.],bounds=([640,-1.36,-.4,-.2,1,-25,-7,-3.5,1.2,.58,.58,.7],[850,-.1,.7,.2,18,-4,1,-1.2,3.5,.95,.95,1.3]),max_nfev=1500)
v=fit.x;p=camera(v); delta=np.linalg.norm(predict(v)-observed,axis=2)
def cut(u,v,axis,value):
    return np.linalg.solve(np.vstack((p[0,:3]-u*p[2,:3],p[1,:3]-v*p[2,:3],np.eye(3)[axis])),[u*p[2,3]-p[0,3],v*p[2,3]-p[1,3],value])
result=dict(reading_size=[1000,562],original_size=[5312,2988],source='https://commons.wikimedia.org/wiki/File:襄阳南路362号住宅.jpg',
  credits='Antigng, 2018-08-02 16:36:16. Wikimedia Commons, CC BY-SA 4.0.',source_sha256='a201724c2bf4419246b6964a76eed1fb09f1c033c414ed1889a9ddb08628c87f',
  basis='X across the three lights from left to right in the photograph, Y into their common wall, Z relative to the spring line; middle axis X0. The 1.50 m middle clear width sets a display scale; there is no independently surveyed dimension.',
  P=p.tolist(),camera_eye=v[4:7].tolist(),f_px=v[0],axes=[dict(x=cx,rx=rx,rise=rx*v[11]) for cx,rx in shapes(v)],glass_y=.105,
  clicked_springs_and_crowns=observed.tolist(),predicted=predict(v).tolist(),errors_px=delta.tolist(),
  vertical_segments=verticals,plane_controls={k:cut(*uv,1,0).tolist()for k,uv in {'parapet_left':[197,253],'parapet_right':[485,198],'end_join_low':[186,256],'end_join_top':[197,166]}.items()},
  limits='The geometry of the 362 photograph is free-standing. No external placement, residential floor plan or link to the municipal 364 street house has been inferred. Equal-height spring points and similar head proportions are constrained across the group.')
out=root/'measurements/courtyard-camera.json'
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(v,delta,result['plane_controls'])
