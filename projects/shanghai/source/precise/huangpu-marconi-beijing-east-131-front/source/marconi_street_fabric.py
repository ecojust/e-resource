"""Street masonry, adjacent bays, projecting cornices and two dormers photographed in 2015 and 2017."""
import math
import numpy as np
from shapely.geometry import Polygon,box,LineString
from shapely.ops import unary_union
from marconi_photo_plane import on_wall,pixel
from marconi_windows import openings
from marconi_arched_portal import portal_wall_cut
from material_names import MATERIAL
RED='Street front | weathered red brick bands'
REDSTONE='Street front | moulded red terracotta'
GREY='Street front | pale stone arrises'
DARK='Street front | recessed interior'
WOOD='Street front | brown window frames'
GLASS='Street front | subdued glazing'
BLUE='Street front | blue green opaque glazing'
IRON='Street front | steel bars'
REVEAL='Street front | shaded masonry in window reveals'
METAL='Street front | painted downpipes'
ROOF='Street front | dark roof flashing'
PLASTER='Dormers | off-white render'
TILE='Street front | pale shop facing'
STONE='Street front | dark base stones'
def rgb(a):
 t=np.array(a)/255.;return np.where(t<=.04045,t/12.92,((t+.055)/1.055)**2.4).tolist()
def mat(c,r=.83,m=0.):return dict(color=rgb(c),roughness=r,metallic=m)
PALETTE={REVEAL:mat([107,98,88]),RED:mat([149,100,95]),REDSTONE:mat([145,92,86]),GREY:mat([177,165,145]),DARK:mat([39,39,37]),WOOD:mat([97,72,62]),GLASS:mat([85,98,98],.36,.18),BLUE:mat([79,104,100],.42,.15),IRON:mat([62,64,63],.61,.23),METAL:mat([183,179,166],.61,.11),ROOF:mat([63,60,56]),PLASTER:mat([208,203,190]),TILE:mat([187,186,176]),STONE:mat([101,105,104])}
def block(b,l,r,f,k,lo,hi,m,title):
 if min(r-l,k-f,hi-lo)>1.e-5:b.box([(l+r)/2,(f+k)/2,(lo+hi)/2],[r-l,k-f,hi-lo],m,label=title)
def skin(b,poly,f,k,m,name):
 if not poly.is_empty:b.prism(poly,-k,-f,lambda x,z,d:(x,-d,z),m,name)
def board(u,v,y=0.,view='2017_front'):
 # Measured in the 610 x 896 rectified board of the principal facade.
 a=-11.5+u*1043/610/70;z=21.5-v*1533/896/70
 return np.array(on_wall(*pixel([a,0,z],view),y,view))
def rectangle(l,t,r,d,y=0.):
 pts=[board(u,v,y) for u,v in ((l,d),(r,d),(r,t),(l,t))]
 return Polygon([tuple(p[::2]) for p in pts])
def plain_window(b,extent,y,nx,nz,name,glass=GLASS,mid=None,rail=.06):
 l,lo,r,hi=extent;block(b,l,r,y+.07,y+.10,lo,hi,glass,name+' | glass')
 for j,x in enumerate(np.linspace(l,r,nx+1)):block(b,x-rail/2,x+rail/2,y,y+.08,lo,hi,WOOD,name+f' | upright {j+1}')
 bars=[lo,*(mid if mid is not None else np.linspace(lo,hi,nz+1)[1:-1]),hi]
 for j,z in enumerate(bars):block(b,l,r,y-.004,y+.085,z-rail/2,z+rail/2,WOOD,name+f' | rail {j+1}')
def evidence(b,lod):
 west,east=-15.85,2.68;top=18.19
 p0=portal_wall_cut()
 # Recess walls follow the original camera rays from the photographed mouths to the timber seats.
 row_polys=[Polygon(o['polygon'])for o in openings()]
 for i,(o,hole) in enumerate(zip(openings(),row_polys)):
  h=Polygon([tuple(on_wall(*pixel([x,o['front_y'],z]),0.)[::2])for x,z in list(hole.exterior.coords)[:-1]])
  row_polys[i]=h.union(hole).convex_hull.buffer(.04,join_style=2)
 broad_top=rectangle(87,206,268,343);broad_mid=rectangle(87,431,266,552)
 left_top=box(west,13.18,-11.85,16.47);left_mid=box(west,8.03,-11.85,10.92)
 high=rectangle(413,197,540,292)
 ground=box(west,.12,-2.78,6.10)
 apertures=[p0,*row_polys,broad_top,broad_mid,left_top,left_mid,high,ground]
 wall=box(west,.01,east,top).difference(unary_union(apertures))
 skin(b,wall,.0,.31,MATERIAL,'Front wall | pierced grey brick')

 # Join each photographed opening to its inset frame. The 2017 outer edge was traced on
 # the aperture plane; project it onto the forward wall and loft back to that physical lip.
 for item in openings():
  lip = item['front_y']
  aperture = Polygon(item['polygon'])
  left,bottom,right,top = aperture.bounds
  outer = box(left-.31,bottom-.32,right+.31,top+.32)
  surround = outer.difference(aperture)
  def profile(x,z,depth):
   y = -depth
   return on_wall(*pixel((x,lip,z)),y) if y < lip else (x,y,z)
  label = 'Arched opening '+item['key']
  b.prism(surround,-lip,-.006,profile,REVEAL,label+' | outward brick reveal')
  skin(b,surround,lip,item['frame_y']+.105,REVEAL,label+' | inset frame bearing')
 for lo,hi in [(1.89,2.11),(4.25,4.49),(6.39,6.58),(9.74,10.08),(16.85,17.87)]:
  skin(b,wall.intersection(box(west,lo,east,hi)),-.027,-.008,RED,'Red brick | horizontal course')
 for lo,hi in [(.02,.63),(6.23,6.34),(17.81,18.13)]:
  skin(b,wall.intersection(box(west,lo,east,hi)),-.072,-.005,STONE if lo<1 else GREY,'Front wall | base and pale mouldings')
 for index,(l,r) in enumerate([(-10.10,-9.68),(-4.71,-2.95)]):
  for t,bt in [(194,360),(379,590)]:
   z0=board(302,bt)[2];z1=board(300,t)[2]
   block(b,l,r,-.109,.045,z0,z1,MATERIAL,f'Brick pier {index+1} | front')
   for lo,hi in [(9.74,10.08),(16.85,17.10)]:
    if z0<lo<z1:block(b,l,r,-.131,-.105,lo,min(hi,z1),RED,'Pier | band continued across projection')
 roofline=18.15
 for j,(base,height,front,material)in enumerate([(17.38,.10,-.12,REDSTONE),(17.57,.16,-.16,REDSTONE),(17.78,.28,-.23,GREY),(18.06,.12,-.28,ROOF)]):
  block(b,west,east,front,.3,base,base+height,material,'Eaves | street course '+str(j+1))
 # The wavy horizontal cornice rises above the single high arch, returning to the same datum at its shoulders.
 def spline_z(x):
  a=abs(x-.015)
  return 12.52 + .48*max(0.,(1.-(a/1.89)**2))**1.5
 xx=np.unique(np.r_[west,-11.9,-9.7,-4.7,-2.95,np.linspace(-2.0,2.0,37 if lod else 69),east])
 for off,h,front,m in [(-.18,.20,-.165,REDSTONE),(.02,.09,-.205,GREY),(.11,.055,-.16,RED)]:
  pts=[(x,spline_z(x)+off)for x in xx];shape=Polygon(pts+[(x,z+h)for x,z in reversed(pts)])
  skin(b,shape,front,.03,m,'Cornice | curved head over high window')
 # Two repeated wide office bays. On the extreme east, both years cut the neighboring bay in the image.
 for idx,(upper,lower)in enumerate([(broad_top,broad_mid),(left_top,left_mid)]):
  for zkey,panel in [('upper',upper),('middle',lower)]:
   l,lo,r,hi=panel.bounds;y=.84 if zkey=='upper' else .67
   block(b,l-.03,r+.03,y+.35,y+.40,lo-.18,hi+.18,DARK,f'Office {idx+1} {zkey} | shade')
   for x in (l,r):block(b,x-.034,x+.034,.22,y+.37,lo,hi,MATERIAL,'Office opening | deep jamb')
   block(b,l,r,-.09,y+.38,lo-.09,lo+.019,GREY,'Office opening | outward stone sill')
   block(b,l,r,.24,y+.38,hi-.01,hi+.045,DARK,'Office opening | soffit')
   if zkey=='upper':
    for k,(a,c)in enumerate([(l+.06,l+.33*(r-l)),(l+.66*(r-l),r-.05)]):
     if idx==0:continue
     plain_window(b,(a,lo+.16,c,hi-.04),y,2,3,f'Office {idx+1} upper sash {k+1}')
     # The center of the photographed bay is a solid panel between the two timber windows.
    block(b,l+.33*(r-l),l+.66*(r-l),y,y+.13,lo,hi,MATERIAL,'Upper office | solid centre panel')
   else:
    plain_window(b,(l+.044,lo+.055,r-.04,hi-.04),y,6,2,f'Office {idx+1} middle sash',BLUE,[lo+.60*(hi-lo)],.055)
 from broad_office_sashes import add_broad_sashes
 add_broad_sashes(b)
 # Upper arcade with paired red piers flanking its two lights and one central brick mullion.
 l,lo,r,hi=high.bounds;c=(l+r)/2.;y=.58
 for ix,(a,k) in enumerate([(l+.04,c-.15),(c+.15,r-.04)]):
  plain_window(b,(a,lo+.05,k,hi-.08),y+.09,2,2,'Upper open gallery | back casement '+str(ix+1))
 block(b,c-.14,c+.14,.31,.83,lo,hi,MATERIAL,'Upper open gallery | brick pier')
 block(b,l-.09,r+.09,-.19,.80,lo-.10,lo+.02,GREY,'Upper gallery | projecting sill')
 for j,x in enumerate([l-.77,l-.38,r+.37,r+.78]):
  base=15.16;z1=16.99
  for low,high_,a,front in [(base,base+.08,.175,-.15),(base+.08,base+.17,.14,-.13),(base+.17,z1-.19,.082,-.09),(z1-.19,z1-.10,.128,-.13),(z1-.10,z1,.168,-.16)]:
   block(b,x-a,x+a,front,.025,low,high_,REDSTONE,'Upper gallery | red engaged pier '+str(j+1))
 for zz,th in [(13.8,.023),(14.03,.026)]:
  block(b,l,r,-.22,-.185,zz,zz+th,IRON,'Upper gallery | guard rail')
 # Local arches are laid as separate brick voussoirs around each measured opening.
 for o in openings():
  key=o['key'];poly=Polygon(o['polygon']);points=np.array(list(poly.exterior.coords)[2:-1])[::-1];points=points[np.argsort(points[:,0])]
  y=o['front_y'];near=[on_wall(*pixel([x,y,z]),.015) for x,z in points]
  if key=='upper':band=.16;shade=MATERIAL
  else:band=.095;shade=REDSTONE
  for a,d in zip(near[:-1],near[1:]):
   dx=d[0]-a[0];gap=min(.025,.020/max(.05,dx))
   x0=a[0]+dx*gap;x1=d[0]-dx*gap
   z0=a[2]+.068;z1=d[2]+.068
   if x1>x0:skin(b,Polygon([(x0,z0),(x1,z1),(x1+.003,z1+band),(x0-.003,z0+band)]),-.035,.005,shade,'Window | segmental arch bricks '+key)
 # Ground levels recorded in both photographs show a continuous steel grille over paneled shop fronts.
 l,lo,r,hi=ground.bounds
 block(b,l,r,.38,.45,lo,hi,DARK,'Ground floor | shaded frontage')
 for z0,z1 in [(3.42,3.47),(5.84,5.89),(6.09,6.16)]:block(b,l,r,-.24,.4,z0,z1,IRON,'Shop grille | horizontal frame')
 for j,x in enumerate(np.arange(-15.55,r,.54)):block(b,x-.012,x+.012,-.183,-.153,3.48,6.09,IRON,'Shop grille | steel upright')
 for z in np.arange(3.62,6.07,.245):block(b,l,r,-.184,-.163,z-.011,z+.011,IRON,'Shop grille | steel rail')
 for j,(a,k)in enumerate([(l,-12.),(-11.98,-8.64),(-8.62,-6.36),(-6.34,-4.70),(-4.68,r)]):
  block(b,a,k,.16,.25,.10,3.39,TILE,'Lower shop | pale facing')
  if j in (1,2):
   for z in np.arange(.26,3.37,.125):block(b,a,k,.148,.158,z,z+.013,GREY,'Lower shop | shutter slat')
  if j==3:plain_window(b,(a+.14,.18,k-.12,3.03),.05,1,2,'Shop facing | timber door',WOOD,[1.96],.075)
 block(b,west,east,-.17,.28,6.12,6.23,GREY,'Shopfront | pale lintel')
 for x in (-10.91,2.57):
  b.tube([[x,-.23,1.02],[x,-.23,16.98],[x+.11,-.25,17.12],[x,-.26,17.28],[x,-.26,17.91]],.052,METAL,6 if lod else 10,'Street | downpipe')
 # The photograph records a plain brick return at the visible west corner. The surface ends at its photograph limit.
 block(b,east-.07,east+.02,.10,2.45,.08,top,MATERIAL,'West return | photograph limit')
 for z0,z1 in [(1.89,2.11),(4.25,4.49),(6.39,6.58),(9.74,10.08),(16.85,17.87)]:
  block(b,east+.018,east+.035,.10,2.45,z0,z1,RED,'West return | continuing red courses')
 block(b,west,east,.22,3.95,18.03,18.18,ROOF,'Roof | visible support behind gutter')
 for i,(lc,peak,rc,face) in enumerate([((-11.,36),(-113.,20),(-209.,40),1.04),((73.,40),(148.,18),(231.,42),.98)]):
  # Left dormer marks are read on the expanded rectification using the oblique and front originals.
  if i==0:
   xa,xc,xb=-15.80,-14.00,-12.14;zb,zt=21.58,22.12
  else:
   point=[board(*p,face)for p in (lc,peak,rc)]
   xa,xc,xb=[q[0]for q in point];zb=min(point[0][2],point[2][2]);zt=point[1][2]
  floor=18.15
  rim=Polygon([(xa,floor),(xb,floor),(xb,zb),(xc,zt),(xa,zb)])
  w=(xb-xa)*.48;l=xc-w/2;r=xc+w/2;lo=floor+.29;hi=zb-.20
  skin(b,rim.difference(box(l,lo,r,hi)),face,face+.16,PLASTER,'Dormer '+str(i+1)+' | pierced gabled end')
  plain_window(b,(l,lo,r,hi),face+.18,2,2,'Dormer '+str(i+1)+' | two timber lights')
  for n,(x0,z0,x1,z1)in enumerate([(xa-.105,zb-.02,xc,zt+.04),(xc,zt+.04,xb+.105,zb-.02)]):
   poly=Polygon([(x0,z0),(x1,z1),(x1,z1+.13),(x0,z0+.13)])
   skin(b,poly,face-.14,3.92,REDSTONE,'Dormer '+str(i+1)+' | sloping tiled eave')
  for x in (xa+.04,xb-.04):block(b,x-.055,x+.055,face+.10,3.90,floor,zb,PLASTER,'Dormer '+str(i+1)+' | exposed cheek')
