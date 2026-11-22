"""Model the photographed right-hand garden bay of the Ying residence in local metres."""
from pathlib import Path
from math import sin, cos, pi
import numpy as np
from shapely.geometry import Polygon, LineString, Point
from profile_tools import BRICK as STONE, slab, cb, bricks_uv

RADIUS = 3.55
HALF = 1.88
CAST = 'Weathered projecting stone'
RELIEF = 'Carved ribbon and garland'
SASH = 'Painted olive shutter frame'
LOUVRE = 'Dark horizontal shutter blades'
SHADE = 'Recess behind shutters'
BALUSTER = 'Pale turned stone balusters'
PALETTE = {}
for name,rgb in [(STONE,(255,255,255)),(CAST,(174,169,151)),(RELIEF,(190,183,161)),
                 (SASH,(84,83,72)),(LOUVRE,(74,76,69)),(SHADE,(42,44,39)),(BALUSTER,(181,177,160))]:
    PALETTE[name]=dict(color=[(v/255)**2.2 for v in rgb],roughness=.83)
PALETTE[STONE]['texture']=str(Path(__file__).with_name('finish.png'))

def curved(x,y,z):
    angle=x/RADIUS
    return ((RADIUS-y)*sin(angle), RADIUS-(RADIUS-y)*cos(angle), z)

def panel(b,left,right,front,back,bottom,top,mat,label,segments=1):
    """A solid band follows the bow, including continuous front, back and top surfaces."""
    v=[];f=[]
    for i in range(segments+1):
        t=left+(right-left)*i/segments
        v.extend([(t,front,bottom),(t,front,top),(t,back,top),(t,back,bottom)])
        j=4*i
        if i:
            f.extend([(j-4,j,j+1,j-3),(j-3,j+1,j+2,j-2),(j-2,j+2,j+3,j-1),(j-1,j+3,j,j-4)])
    end=4*segments
    f.extend([(0,1,2,3),(end+3,end+2,end+1,end)])
    b.add(v,f,mat,label)

def relief_line(b,points,width,face,back,name,res):
    shape=LineString(points).buffer(width,quad_segs=res,cap_style='round',join_style='round')
    slab(b,shape,face,back,RELIEF,name)

def swag_z(t):
    return .891-.278*(1-(2*t-1)**2)

def bow(b,x,detail):
    # Two open bow loops and folded ribbon ends hang from each tie in the photograph.
    for sign in (-1,1):
        pts=[(x,.895),(x+.084*sign,.950),(x+.142*sign,.942),(x+.126*sign,.873),(x+.073*sign,.876),(x,.895)]
        relief_line(b,pts,.016,-.111,-.042,'Folded bow loop',detail)
        slab(b,Polygon([(x,.88),(x+.028*sign,.90),(x+.070*sign,.769),(x+.045*sign,.794),(x+.035*sign,.762)]),-.106,-.043,RELIEF,'Split ribbon tail')
    slab(b,Point(x,.889).buffer(.037,quad_segs=detail+2),-.117,-.041,RELIEF,'Ribbon knot')
    for dx,zt in [(-.038,.70),(0,.64),(.040,.70)]:
        relief_line(b,[(x,.765),(x+dx,zt)],.010,-.09,-.041,'Tie and pendant',detail)
        slab(b,Point(x+dx,zt).buffer(.031,quad_segs=detail+1),-.098,-.04,RELIEF,'Pendant terminal')

def model(b,lod=False):
    arc=12 if lod else 28
    panel(b,-HALF,HALF,0,.27,.06,1.20,STONE,'Bowed stone spandrel',arc)
    for z0,z1,front,limit in [(0,.075,-.097,1.91),(.12,.165,-.049,1.88),(1.165,1.225,-.083,1.91),
                              (3.21,3.31,-.089,1.91),(3.31,3.43,-.16,1.96),(3.43,3.49,-.22,1.99)]:
        panel(b,-limit,limit,front,.25,z0,z1,CAST,'Curved horizontal sill or cornice',arc)
    for x in (-HALF+.09,0,HALF-.09):
        half=.085 if x==0 else .092
        panel(b,x-half,x+half,-.004,.27,1.19,3.22,STONE,'Stone jamb between the shutter bays',2)
    for side in (-1,1):
        left,right=(-1.69,-.086) if side<0 else (.086,1.69)
        for z,hi in [(1.25,2.56),(2.72,3.135)]:
            panel(b,left,right,.160,.207,z,hi,SHADE,'Shaded backing visible between blades',6)
            for edge in (left+.027,right-.027):
                panel(b,edge-.027,edge+.027,.064,.153,z,hi,SASH,'Outer shutter stile')
            middle=(left+right)/2
            panel(b,middle-.031,middle+.031,.063,.154,z,hi,SASH,'Meeting stile between shutter leaves')
            for rail_z in (z+.033,hi-.033):
                panel(b,left,right,.059,.149,rail_z-.032,rail_z+.032,SASH,'Shutter top and toe rails',5)
            count=(12 if lod else 22) if hi-z>1 else (4 if lod else 7)
            for j in range(count):
                base_z=z+.076+j*(hi-z-.12)/count;blade_h=(hi-z-.12)/count*.72
                for lo,up in [(left+.057,middle-.033),(middle+.032,right-.057)]:
                    # Front tips are lower than back edges, giving every slat a real return.
                    vs=[(xx,yy,zz) for xx in (lo,up) for yy,zz in [(.083,base_z),(.080,base_z+.011),(.140,base_z+blade_h),(.144,base_z+blade_h-.010)]]
                    b.add(vs,[(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0),(0,1,2,3),(7,6,5,4)],LOUVRE,'Tilted solid shutter slat')
        for z0,z1 in [(1.21,1.25),(2.56,2.72),(3.135,3.215)]:
            panel(b,left,right,-.005,.27,z0,z1,STONE,'Curved stone transom and window surround',8)
    for x in (-1.54,0,1.54):bow(b,x,2 if lod else 4)
    for left,right in [(-1.54,0),(0,1.54)]:
        pts=[(left+(right-left)*u,swag_z(u)) for u in np.linspace(0,1,11 if lod else 23)]
        relief_line(b,pts,.032,-.084,-.003,'Suspended carved garland cord',2)
        for i,t in enumerate(np.linspace(.12,.88,7 if lod else 14)):
            cx=left+(right-left)*t;cz=swag_z(t)
            for sign in (-1,1):
                poly=Polygon([(cx-.065,cz-.012),(cx-.017,cz+.029*sign),(cx+.060,cz+.070*sign),(cx+.045,cz+.012*sign),(cx-.013,cz-.025)])
                slab(b,poly,-.094-.006*(i%2),-.032,RELIEF,'Paired overlapping carved laurel leaves')
    # The balcony is set back from the bent cornice, with a solid central pedestal.
    panel(b,-1.75,1.75,-.12,.23,3.48,3.56,CAST,'Balcony bottom rail',arc)
    for x in (-1.66,0,1.66):
        panel(b,x-.083,x+.083,-.117,.12,3.55,4.0,STONE,'Balcony pedestal',2)
        panel(b,x-.115,x+.115,-.148,.145,3.95,4.025,CAST,'Balcony pedestal cap',2)
    spin=[(3.55,.056),(3.596,.067),(3.623,.044),(3.668,.045),(3.718,.068),
          (3.756,.075),(3.823,.053),(3.89,.036),(3.93,.058),(3.968,.069),(4,.062)]
    for sign in (-1,1):
        for u in [.297,.61,.922,1.237,1.47]:
            b.lathe((sign*u,-.003),spin,BALUSTER,8 if lod else 18,label='Turned stone balcony baluster')
    panel(b,-1.77,1.77,-.135,.14,3.97,4.03,CAST,'Lower lip of sweeping handrail',arc)
    panel(b,-1.79,1.79,-.168,.16,4.03,4.087,STONE,'Bowed stone handrail',arc)
    # Form the cylindrical projection after the flat profiles have been cut.
    for part in b.parts:
        part['vertices']=[curved(x,y,z) for x,y,z in part['vertices']]
    bricks_uv(b)
