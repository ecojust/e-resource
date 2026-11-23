"""The two working leaves, western address pier, east planter, and street threshold."""
from pathlib import Path
import json,math
import numpy as np
import pier_details
import wall_plane
from shapely.geometry import box
H=Path(__file__).absolute().parent
STONE='grey-pink aggregate plaster';EDGE='worn pale cement';GREEN='green enamel address plate';IRON='black enamel gate iron';SOIL='dark planter soil';PAVE='age-darkened lane paving'
def frontage(b,depth):
 def prism(poly,z0,z1,mat,name):
  b.prism(poly,z0,z1,lambda x,z,d:(x,-d,z),mat,name)
 # The central opening remains walkable. Three narrow grooves cut the face of the western pier.
 west_inner=-4.81;west_outer=-5.85;west_front=-.37;upper=3.42;thickness=.30
 b.box(((west_outer+west_inner)/2,west_front+thickness/2+.015,upper/2),(west_inner-west_outer,thickness-.03,upper),STONE,label='west pier/solid back and reveals')
 face=box(west_outer,0,west_inner,upper)
 for i,x in enumerate([-5.80,-5.42,-5.10]):face=face.difference(box(x-.020,.17,x+.020,2.51))
 prism(face,-west_front-.035,-west_front,STONE,'west pier/three recessed vertical grooves')
 b.box((-5.30,west_front-.014,2.76),(.44,.028,.126),GREEN,label='west pier/green lane number plate')
 # The name wall has a raised stone trough at its foot. The open centre is filled below the lip.
 # Its frontage endpoints are surveyed. Depth and the curb return are estimated from the street view.
 x0,x1=.0,2.845;front=-.34;rear=.219;z=.40
 b.box(((x0+x1)/2,(front+rear)/2,.085),(x1-x0+.06,rear-front+.04,.17),EDGE,label='planter/continuous plinth')
 b.box(((x0+x1)/2,front+.035,.253),(x1-x0,.070,.190),STONE,label='planter/front face')
 b.box(((x0+x1)/2,rear-.035,.253),(x1-x0,.069,.189),STONE,label='planter/rear face')
 for side,x in [('west',x0+.035),('east',x1-.035)]:
  b.box((x,(front+rear)/2,.254),(.070,rear-front-.138,.189),STONE,label='planter/'+side+' end')
 profile=box(x0-.04,front-.022,x1+.04,rear+.018).difference(box(x0+.08,front+.078,x1-.08,rear-.074))
 b.plan_prism(profile,.344,z,EDGE,'planter/overhanging rim around planting bed')
 b.box(((x0+x1)/2,(front+rear)/2,.270),(x1-x0-.162,rear-front-.158,.054),SOIL,label='planter/exposed soil')
 # The two gates swing into the lane as photographed. The hinge offsets are measured
 # from the pier returns. The angular positions can change when residents use the lane.
 for side,hinge,sign,angle in [('west',west_inner+.065,1,80.),('east',.13,-1,103.)]:
  span=2.35;theta=math.radians(angle);along=np.asarray([sign*math.cos(theta),math.sin(theta),0]);out=np.asarray([along[1],-along[0],0]);up=np.asarray([0,0,1])
  root=np.asarray([hinge,west_front+.28 if side=='west'else .55,0.])
  def xyz(s,z,d=0.):return root+along*s+up*z+out*d
  def rail(points,r,label):
   b.tube([xyz(s,z) for s,z in points],r,IRON,6 if depth else 10,'gate '+side+'/'+label)
  def crown(s):
   u=s/span;return 2.22+.14*(.5-.5*math.cos(2*math.pi*u))
  for j,u in enumerate([0,1]):
   s=span*u;rail([(s,.105),(s,crown(s))],.028,'stile '+str(j+1))
  for j,z0 in enumerate([.12,.48,.89]):
   rail([(0,z0),(span,z0)],.014 if j!=0 else .023,'horizontal rail '+str(j+1))
  ss=np.linspace(0,span,10 if depth else 25);rail([(s,crown(s))for s in ss],.023,'wave head')
  for j in range(1,12):
   s=span*j/12;rail([(s,.13),(s,crown(s)-.009)],.010,'upright '+str(j))
  for band in range(4):
   start=span*band/4;end=span*(band+1)/4;middle=(start+end)/2
   rail([(start,.478),(middle,.13),(end,.478),(middle,.853),(start,.478)],.008,'lower diamond '+str(band+1))
  # Three curved bars turn through the panel between the middle rail and the outer stile.
  for j in range(3):
   vals=np.linspace(0,math.pi/2,8 if depth else 18);r=.44+.17*j
   rail([(span-r*math.cos(t),.90+r*math.sin(t))for t in vals],.011,'lower scroll '+str(j+1))
   rail([(span-r*math.cos(t),2.255-r*math.sin(t))for t in vals],.011,'upper scroll '+str(j+1))
 return b

def assemble(b,lod):
 data=json.loads((H/'street-scale.json').read_bytes());sx,bx=data['initial_x_to_metres'];sz,bz=data['initial_z_to_metres'];y0=data['adjusted_curb_face_y_m']
 lamps=[];ground='wall/stepped sunburst silhouette'
 for part in b.parts:
  a=np.asarray(part['vertices']);original=a.copy()
  a[:,[0,2]]=wall_plane.plane_xz(a[:,[0,2]]);a[:,1]=a[:,1]*.80+y0
  if part['label']==ground:a[original[:,2]<0,2]=.005
  part['vertices']=a.tolist()
  if part['label'].startswith('lantern/'):lamps.append(part)
 b.palette.update({IRON:{'color':[.075,.081,.078],'roughness':.52},GREEN:{'color':[.072,.266,.170],'roughness':.60},SOIL:{'color':[.188,.147,.114],'roughness':.97},PAVE:{'color':[.51,.48,.442],'roughness':.90}})
 # The two wall fixtures have matching frames. Translate from the east light to the west
 # one with the observed level difference and the measured offset between the grey walls.
 for i,part in enumerate(lamps):
  p=np.asarray(part['vertices']);p+=np.asarray([-5.35,-.60,-.035])
  b.add(p,part['triangles'],part['material'],part['label'].replace('lantern/','west lantern/'))
 return pier_details.add(frontage(b,lod),lod)
