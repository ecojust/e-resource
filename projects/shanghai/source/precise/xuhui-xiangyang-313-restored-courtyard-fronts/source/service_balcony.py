"""Fixed fittings of the photographed left service elevation at Xiangyang South Road 313."""
from pathlib import Path
import json
import math
import sys

HERE = Path(__file__).resolve().parent
MEASUREMENTS = HERE.parent / 'measurements'
sys.path.insert(0, str(MEASUREMENTS))
from register_courtyard import Camera

OBS = json.loads((MEASUREMENTS / 'service-balcony-observations.json').read_bytes())
STEEL = 'Xiangyang 313 | dark grey balcony steel'
PALE = 'Xiangyang 313 | light painted diagonal rail'
BASE = 'Xiangyang 313 | grey balcony deck and bearers'
TIN = 'Xiangyang 313 | weathered corrugated sheet'
PINK = 'Xiangyang 313 | faded rose awning'
CASE = 'Xiangyang 313 | pale equipment housing'
FAN = 'Xiangyang 313 | recessed fan screen'
ZINC = 'Xiangyang 313 | galvanized support angles'
PALETTE = {
    STEEL: {'color':[.121,.131,.156], 'roughness':.76,'metallic':.34},
    PALE: {'color':[.68,.72,.75], 'roughness':.65,'metallic':.18},
    BASE: {'color':[.245,.242,.243], 'roughness':.84},
    TIN: {'color':[.155,.148,.145], 'roughness':.77,'metallic':.34},
    PINK: {'color':[.47,.285,.359], 'roughness':.88},
    CASE: {'color':[.60,.62,.605], 'roughness':.77},
    FAN: {'color':[.093,.105,.111], 'roughness':.70},
    ZINC: {'color':[.36,.36,.35], 'roughness':.65,'metallic':.42},
}
NAME = '313 service court | '
def rect(b,x0,x1,y0,y1,z0,z1,material,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=NAME+label)

def beam(b,p,q,width,thickness,material,label):
    delta=[q[n]-p[n] for n in range(3)]
    length=math.hypot(*delta);w=[v/length for v in delta]
    ref=(0.,0.,1.) if abs(w[2])<.85 else (0.,1.,0.)
    def cross(a,c):return [a[1]*c[2]-a[2]*c[1],a[2]*c[0]-a[0]*c[2],a[0]*c[1]-a[1]*c[0]]
    u=cross(ref,w);scale=math.hypot(*u);u=[t/scale for t in u];v=cross(w,u)
    b.box(tuple((x+y)/2 for x,y in zip(p,q)),(width,thickness,length),material,basis=(u,v,w),label=NAME+label)

def section_sheet(b,stations,material,label):
    """Each +X station runs from outer top to the wall, and back along its underside."""
    points=[p for station in stations for p in station];faces=[]
    for j in range(len(stations)-1):
        for i in range(4):
            a=j*4+i;c=j*4+(i+1)%4
            faces.extend(((a,a+4,c+4),(a,c+4,c)))
    j=(len(stations)-1)*4
    faces.extend(((0,1,2),(0,2,3),(j,j+2,j+1),(j,j+3,j+2)))
    b.add(points,faces,material,NAME+label)

def _balcony(b,c,wy,lod):
    m=OBS['balcony'];y=wy-m['front_depth_from_wall']
    left,right=[c.wall(uv,y)for uv in m['front_top']]
    l,r=left[0],right[0];z=(left[2]+right[2])/2
    rect(b,l,r,y,wy+.015,z-.095,z,BASE,'projecting deck')
    rect(b,l,r,y-.008,y+.058,z-.151,z-.020,STEEL,'deep front fascia')
    top=sum(c.wall(uv,y)[2] for uv in m['top_handrail'])/2
    waist=sum(c.wall(uv,y)[2] for uv in m['waist_rail'])/2
    posts=[l+.035]+[c.wall(uv,y)[0] for uv in m['front_post_bases'][1:-1]]+[r-.035]
    for x in posts:rect(b,x-.043,x+.043,y+.009,y+.10,z,top,STEEL,'front baluster')
    rect(b,l,r,y-.005,y+.098,top-.043,top+.010,STEEL,'dark front handrail')
    for bay,(a,d) in enumerate(zip(posts,posts[1:])):
        if bay==2:continue  # White pattern behind the rightmost laundry is unresolved.
        level=y+.068
        beam(b,(a+.043,level,z+.045),(d-.043,level,top-.063),.050,.061,PALE,'light rising diagonal')
        beam(b,(a+.043,level,top-.063),(d-.043,level,z+.045),.050,.061,PALE,'light falling diagonal')
        rect(b,a,d,level-.035,level+.035,waist-.030,waist+.030,PALE,'light middle rail')
    for j,x in enumerate((l+.04,r-.04)):
        rect(b,x-.035,x+.035,y+.035,wy,top-.04,top+.010,STEEL,'return handrail')
        rect(b,x-.040,x+.040,wy-.106,wy-.025,z,top+.005,STEEL,'return upright')
    for uv in m['bearing_centres']:
        x=c.wall(uv,wy-.087)[0]
        rect(b,x-.077,x+.077,y+.08,wy+.026,z-.258,z-.083,BASE,'square underside bearer')
        rect(b,x-.077,x+.077,wy-.095,wy+.026,z-.315,z-.084,BASE,'short wall seat')
    for x in (l+.17,r-.18):
        if not lod:rect(b,x-.037,x+.037,y+.21,y+.285,z-.123,z-.094,ZINC,'visible underside fixing')

def _upper_hood(b,c,wy,lod):
    m=OBS['upper_hood'];y=wy-m['front_depth_from_wall']
    pf=[c.wall(p,y)for p in m['front_edge']];pr=[c.wall(p,wy)for p in m['rear_edge']]
    l,r=pf[0][0],pf[1][0]
    outer=(pf[0][2]+pf[1][2])/2; rear=(pr[0][2]+pr[1][2])/2
    waves=max(12,round((r-l)/.11)); samples=waves*(4 if lod else 8)
    rings=[]
    for j in range(samples+1):
        t=j/samples;x=l+(r-l)*t;ridge=.013*math.cos(2*math.pi*waves*t)
        rings.append(((x,y,outer+ridge),(x,wy+.012,rear+ridge),(x,wy+.012,rear+ridge-.013),(x,y,outer+ridge-.013)))
    section_sheet(b,rings,TIN,'low rippled steel hood')
    for frac in (.11,.88):
        x=l+(r-l)*frac
        beam(b,(x,y+.03,outer-.031),(x,wy+.01,rear-.031),.044,.042,STEEL,'hood underside bearer')
        beam(b,(x,y+.15,outer-.045),(x,wy-.005,rear-.230),.020,.025,ZINC,'short hood diagonal bracket')
    rect(b,l+.022,r-.016,y+.15,y+.195,outer-.063,outer-.03,STEEL,'hood underside transverse rail')

def _rose_hood(b,c,wy,lod):
    m=OBS['lower_hood'];y=wy-m['front_depth_from_wall']
    pf=[c.wall(p,y)for p in m['front_shoulder']];pr=[c.wall(p,wy)for p in m['rear_edge']]
    l,r=pf[0][0],pf[1][0];outer=(pf[0][2]+pf[1][2])/2;rear=(pr[0][2]+pr[1][2])/2
    section_sheet(b,[((x,y,outer),(x,wy+.012,rear),(x,wy+.012,rear-.031),(x,y,outer-.031))for x in (l,r)],PINK,'lower rose awning')
    top=outer-.016;base=sum(c.wall(p,y)[2]for p in m['valance_bottom'])/len(m['valance_bottom'])
    n=13*(4 if lod else 8);rings=[]
    for j in range(n+1):
        t=j/n;x=l+(r-l)*t; bottom=base+.038*(1-2*abs(math.sin(math.pi*13*t)))
        rings.append(((x,y-.017,top),(x,y+.015,top),(x,y+.015,bottom),(x,y-.017,bottom)))
    section_sheet(b,rings,PINK,'scalloped hanging edge')
    rect(b,l,r,y-.02,y+.021,outer-.012,outer+.009,ZINC,'thin front roll')
    rect(b,l+.02,r-.02,wy-.06,wy+.015,rear-.014,rear+.012,ZINC,'upper fixing welt')

def _condenser(b,c,wy,m,lod):
    y=wy-.337;a,d=[c.wall(p,y)for p in m['front_rectangle']];centre=c.wall(m['fan'],y)
    l,r=sorted((a[0],d[0]));lo,hi=sorted((a[2],d[2]));x,z=centre[0],centre[2]
    name=m['name']+' condenser/'
    rect(b,l,r,y,wy-.033,lo,hi,CASE,name+'housing')
    radius=min((hi-lo)*.399,(r-l)*.275);n=16 if lod else 32
    # Dark disk inset behind the concentric wire guards on the pale housing.
    ring=[(x+radius*math.cos(2*math.pi*i/n),z+radius*math.sin(2*math.pi*i/n)) for i in range(n)]
    from shapely.geometry import Polygon
    b.prism(Polygon(ring),-y+.002,-y+.011,lambda u,v,p:(u,-p,v),FAN,NAME+name+'fan screen')
    for factor in ((.84,)if lod else (.52,.84)):
        gauge=.0045 if lod else .0054
        outside=[(x+(factor+gauge/radius)*(u-x),z+(factor+gauge/radius)*(v-z))for u,v in ring]
        inside=[(x+(factor-gauge/radius)*(u-x),z+(factor-gauge/radius)*(v-z))for u,v in ring]
        b.prism(Polygon(outside,[inside]),-y+.0115,-y+.016,lambda u,v,p:(u,-p,v),ZINC,NAME+name+'wire guard')
    if not lod:
        for a in (0,math.pi/3,2*math.pi/3):
            dx=.90*radius*math.cos(a);dz=.90*radius*math.sin(a)
            beam(b,(x-dx,y-.017,z-dz),(x+dx,y-.017,z+dz),.008,.006,ZINC,name+'grille spoke')
    for ux in m['support_axes']:
        bx=c.wall((ux,m['front_rectangle'][1][1]),y)[0]
        rect(b,bx-.022,bx+.022,y-.018,wy+.011,lo-.035,lo,ZINC,name+'angle horizontal leg')
        rect(b,bx-.022,bx+.022,wy-.027,wy+.011,lo-.195,lo+.025,STEEL,name+'wall foot')
        beam(b,(bx,y+.045,lo-.035),(bx,wy-.022,lo-.176),.017,.026,STEEL,name+'diagonal return')

def add_service_balcony(b,lod=False,*,wall_y=None,lower_hood=True):
    """Add the left-elevation fittings in case1 coordinates, with +Y entering the wall."""
    c=Camera('case1')
    wy=OBS['wall_y'] if wall_y is None else wall_y
    _balcony(b,c,wy,lod);_upper_hood(b,c,wy,lod)
    if lower_hood:_rose_hood(b,c,wy,lod)
    for m in OBS['condensers']:_condenser(b,c,wy,m,lod)
