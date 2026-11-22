from pathlib import Path
import json,hashlib,math
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
import numpy as np
import argparse
parser=argparse.ArgumentParser(description='Fit two cameras to separately digitised 2016 views of the three-window wall.')
parser.add_argument('source_photographs',type=Path)
parser.add_argument('output',type=Path)
args=parser.parse_args()
p=args.source_photographs
land={}
for ix,name in enumerate(('Left','Middle','Right')):
 c=(ix-1)*2.4
 land[name+' peak']=[c,-.233,3.55]
 land[name+' crest top']=[c,-.142,3.212]
 land[name+' crest foot']=[c,-.143,2.878]
 land[name+' right volute']=[c+.317,-.153,2.940]
 land[name+' left volute']=[c-.317,-.153,2.940]
 for side,k in [(-1,'L'),(1,'R')]:
  t=c+side*.859
  land[name+' '+k+' cap outer']=[t+side*.304,-.315,2.961]
  land[name+' '+k+' cap inner']=[t-side*.304,-.315,2.961]
  land[name+' '+k+' head']=[t,-.181,2.525]
  land[name+' '+k+' plinth']=[t,-.204,.214]
  land[name+' '+k+' diamond tip']=[t,-.150,1.60]
  land[name+' '+k+' inner base']=[t-side*.198,-.204,.005]
  land[name+' '+k+' shutter base']=[c+side*.566,.195,.04]
# Picked on 1000w and oblique crop independently, then registered to native px.
front=[('Left peak',189,45.5),('Middle peak',522,60),('Right peak',836,77),
       ('Left R inner base',247,546),('Middle L inner base',422,546),
       ('Middle R inner base',624,545),('Right L inner base',789,545),
       ('Left R cap outer',348,133),('Middle L cap outer',360,134),('Right R cap outer',993,160),
       ('Left R head',297,203),('Middle L head',402,207),('Right L head',735,217)]
front_test=[('Left crest foot',190,135),('Middle crest foot',520,149),('Right crest foot',827,160),
       ('Left crest top',190,90),('Middle crest top',522,105),('Right crest top',830,116),
       ('Left R diamond tip',296,318),('Middle L diamond tip',400,316),('Middle R diamond tip',644,318),
       ('Left right volute',233,129),('Right left volute',790,153),('Middle left volute',478,140)]
# Coordinates in the privately inspected 423x780 crop. Dimensions of crop's
# 690w overview were [50,310,275,725]. Only the third window remains fully identifiable.
def ob(rows):
 return [(name,50+x*225/423,310+y*415/780) for name,x,y in rows]
ang=ob([('Right peak',271,34),('Right L cap outer',64,67),('Right L cap inner',181,117),
 ('Right R cap inner',340,200),('Right R cap outer',411,241),('Right L head',85,195),
 ('Right R head',347,299),('Right L plinth',38,709),('Right L inner base',75,763)])
ang_test=ob([('Right crest top',230,94),('Right crest foot',232,161),
 ('Right right volute',277,166),('Right left volute',197,131),
 ('Right L diamond tip',73,383)])
PROFILE=[(0.,0.),(.3,0.),(1.6,0.),(2.525,-.080),(2.856,.060),(2.961,.035),(3.55,.105)]
def actual(point):
 x,y,z=point
 return [x,y,z+np.interp(z,*np.array(PROFILE).T)]
for name, xyz in land.items():land[name]=actual(xyz)
def calc(photo,size,fit,held):
 width,height=size;actual=np.array([width,height]);preview=1000 if photo=='06' else 690; k=width/preview
 K=np.eye(3);K[0,2]=preview/2;K[1,2]=height/k/2
 def matrices(v):
  rx,ry,rz,x,y,z,f,px,py=v
  R=Rotation.from_rotvec([rx,ry,rz]).as_matrix()@[[1,0,0],[0,0,-1],[0,1,0]]
  K[0,0]=K[1,1]=f;K[0,2]=px;K[1,2]=py
  return K@np.column_stack((R,-R@[x,y,z]))
 def project(v,rows):
  pts=np.array([[*land[n],1.] for n,*_ in rows]);q=pts@matrices(v).T
  return q[:,:2]/q[:,2:]
 target=np.array([xy for n,*xy in fit]);targeth=np.array([xy for n,*xy in held])
 vals=([-0.25,0,0,-.7,-6.5,.2,780]if photo=='06' else [-.12,-.95,.02,-4.2,-3.,.35,720])
 vals.extend([preview/2,height/k/2]); foc=25*np.hypot(4288,3216)/np.hypot(36,24)/k
 vals[6]=foc
 left,right=(475,526) if photo=="06" else (303,387); top,bottom=(193,395) if photo=="06" else (451,516)
 res=least_squares(lambda v:np.r_[(project(v,fit)-target).ravel(),(v[6]-foc)*.024,(v[7]-preview/2)*.015,(v[8]-height/k/2)*.015],vals,
    bounds=([-2,-2,-1,-30,-35,-7,foc*.97,left,top],[2,2,1,30,-1,8,foc*1.03,right,bottom]),max_nfev=3000)
 P=matrices(res.x).copy();P[:2,:]*=k
 def data(rows):
  pr=project(res.x,rows);out=[]
  for (name,x,y),(u,v) in zip(rows,pr):
   out.append(dict(point=name,model_xyz=land[name],native_pixel=np.round([x*k,y*k],2).tolist(),projection=np.round([u*k,v*k],2).tolist(),residual_px=round(math.hypot(u-x,v-y)*k,2)))
  return out
 return dict(file='yicao-'+photo+'.jpg',sha256=hashlib.sha256((p/('yicao-'+photo+'.jpg')).read_bytes()).hexdigest(),dimensions=size,native_focal_px=res.x[6]*k,estimated_principal_point=(res.x[7:9]*k).tolist(),P=P.tolist(),camera_xyz=res.x[3:6].tolist(),fit=data(fit),held=data(held))
book={'claim':'2016-11-02正面与斜面：6号三窗，3号含直面组右端一窗与紧邻转角。照片作者言衣草发布，未见单独转载许可；公开保留原创几何、测点和来源。轴距2.40m为比例假定。','article':'https://blog.sina.cn/dpool/blog/s/blog_a598306e0102xev6.html','front':calc('06',[4082,2392],front,front_test),'oblique':calc('03',[2867,4019],ang,ang_test)}
book['source_urls']={'front':'https://s14.sinaimg.cn/large/003216vszy76zbuRUN75d','oblique':'https://s10.sinaimg.cn/large/003216vszy76zbjhvol69'}
book['interpretation']='正面拟合13处，独立对照12处；斜面9处拟合、5处对照。斜面右柱菱线被植物遮挡，未用作定位。轴距估值并非建筑实测长度。'
for n in ['front','oblique']:
 m=book[n];print(n,m['camera_xyz'],[(j,np.round([q['residual_px'] for q in m[j]],1)) for j in ['fit','held']])
args.output.write_text(json.dumps(book,ensure_ascii=False,indent=2)+'\n')
