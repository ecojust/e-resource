"""Ten exterior steps, stone balustrades and the arched front of the garden porch."""
import math
import numpy as np
from shapely.geometry import Polygon,box
from scipy.optimize import least_squares
from photo_architecture import Facade
from register_porch import PorchFrame
from fit_porch import DATA

STONE='325 porch | mottled grey stair stone'
EDGE='325 porch | worn pale tread edge'
BASE='325 porch | darker grey plinth course'
RAIL='325 porch | sandy carved balustrade stone'
TOP='325 porch | weathered handrail top'
RENDER='325 garden | pale ochre pebble finish'
RETURN='325 porch | shaded arch return'
PALETTE={STONE:{'color':[.35,.335,.300],'roughness':.91},
         EDGE:{'color':[.49,.471,.421],'roughness':.86},
         BASE:{'color':[.296,.283,.256],'roughness':.85},
         RAIL:{'color':[.52,.482,.37],'roughness':.93},
         TOP:{'color':[.514,.498,.447],'roughness':.83},
         RENDER:{'color':[.65,.55,.34],'roughness':.94},
         RETURN:{'color':[.462,.409,.299],'roughness':.91}}

def arch_aperture(f,lod):
    picks=DATA['front_arch_intrados_px']
    centres=np.array([f.plane(uv)for uv in picks[2:-1]])
    left=f.plane(picks[0])[0];right=f.plane(picks[-1])[0]
    def loss(p):
        x,z,span,rise=p
        return ((centres[:,0]-x)/span)**2+((centres[:,1]-z)/rise)**2-1
    centre,z,rx,rz=least_squares(loss,[(left+right)/2,3.03,(right-left)/2,1.44],
                                 bounds=([-.20,2.91,1.55,1.30],[.22,3.14,1.79,1.57])).x
    arc=[(centre+rx*math.cos(t),z+rz*math.sin(t))for t in np.linspace(np.pi,0,31 if lod else 65)]
    return Polygon([(centre-rx,f.landing_z-.02),*arc,(centre+rx,f.landing_z-.02)])

def add_porch_arch(b,f,lod):
    l,_=f.plane((458,812));r,_=f.plane((889,812))
    z1=f.plane((615,629))[1]
    surface=Facade(b,f.xyz(-1,0,0)[:2],f.xyz(1,0,0)[:2],'325 rear porch')
    opening=arch_aperture(f,lod)
    body=box(l,f.landing_z-.02,r,z1).difference(opening)
    surface.prism(body,-.237,0,RENDER,'curved head and two plastered jambs')
    arch_band=opening.buffer(.029,join_style=2).difference(opening).intersection(box(l,f.landing_z+.035,r,z1))
    surface.prism(arch_band,-.257,-.237,RETURN,'slightly recessed rear arris of arch')
    for x0,x1 in [(l,opening.bounds[0]),(opening.bounds[2],r)]:
        surface.prism(box(x0,f.landing_z-.004,x1,f.landing_z+.115),-.242,.009,BASE,'darker base at foot of jamb')

def plan(b,f,poly,lo,hi,mat,name):
    b.prism(poly,lo,hi,lambda x,y,z:f.xyz(x,y,z),mat,'325 porch / '+name)

def cross_section(b,f,points_yz,x0,x1,mat,name):
    b.prism(Polygon(points_yz),x0,x1,lambda y,z,x:f.xyz(x,y,z),mat,'325 porch / '+name)

def frame_coordinates(f,index):
    d=f.data;t=index/9
    mid=-d['flight_lateral_shift_m']*(1-t)
    span=d['axis_span_m']*(1-t)+d['upper_axis_span_m']*t
    return mid,span,-d['porch_offset_from_bottom_m']+index*d['tread_m']

def add_steps(b,f):
    d=f.data;rise=d['rise_m'];going=d['tread_m']
    for n in range(10):
        centre,span,y=frame_coordinates(f,n);z=(n+1)*rise
        end=y+going if n<9 else .48
        width=span+.10
        floor=box(centre-width/2,y,centre+width/2,end)
        plan(b,f,floor,0,z-.027,STONE,f'stair {n+1:02} body')
        # Real rows show a thin projecting nose with a lighter worn arris and
        # separate stone joints. Extend the landing to the arched threshold.
        joints=[-.53,.31] if n%2 else [-.32,.51]
        cuts=[-1,*joints,1]
        for j,(a,c) in enumerate(zip(cuts,cuts[1:])):
            l=centre+width*a/2+.0014;r=centre+width*c/2-.0014
            slab=box(l,y-.022,r,end-.001) if n<9 else box(l,y-.022,r,end)
            plan(b,f,slab,z-.027,z,STONE,f'nosing course {n+1:02}, stone {j+1}')
            plan(b,f,box(l,y-.026,r,y-.022),z-.023,z-.006,EDGE,f'worn arris {n+1:02}, stone {j+1}')
    # A separately visible flush paving joint just beyond the bottom rise.
    cx,span,y=frame_coordinates(f,0)
    plan(b,f,box(cx-span/2-.29,y-.31,cx+span/2+.29,y),-.035,.002,BASE,'stone pavement before foot of stair')

def turned(b,f,x,y,profile,mat,name,segments):
    centre=f.xyz(x,y,0)[:2]
    verts=[(centre[0]+r*math.cos(t),centre[1]+r*math.sin(t),z)
           for z,r in profile for t in np.arange(segments)*2*math.pi/segments]
    rings=len(profile);faces=[tuple(reversed(range(segments))),tuple(range((rings-1)*segments,rings*segments))]
    for k in range(rings-1):
        for j in range(segments):
            a=k*segments+j;q=k*segments+(j+1)%segments;faces.append((a,q,q+segments,a+segments))
    b.add(verts,faces,mat,'325 porch / '+name)

def newel(b,f,x,y,ground,cap,upper,lod):
    half=.15 if upper else .19
    # The foot of the lower newel curves forward and then draws in toward its
    # square shaft. Every section is attached to the same stone body.
    outline=[(y-half-.09,ground),(y+half+.025,ground),(y+half,cap-.1),
             (y-half,cap-.1),(y-half,ground+.58),(y-half-.035,ground+.43),
             (y-half-.084,ground+.27),(y-half-.106,ground+.11)]
    cross_section(b,f,outline,x-half,x+half,RAIL,'upper square newel' if upper else 'lower swept stone newel')
    for z0,z1,h in [(cap-.13,cap-.095,half+.014),(cap-.095,cap-.035,half+.033),(cap-.035,cap,half+.055)]:
        plan(b,f,box(x-h,y-h,x+h,y+h),z0,z1,TOP,'stepped cap on newel')
    if upper:
        radius=.154;z0=cap+.022
        profile=[(z0+radius+radius*math.sin(t),max(.001,radius*math.cos(t)))for t in np.linspace(-1.568,1.568,12 if lod else 20)]
        turned(b,f,x,y,profile,RAIL,'upper stone ball',12 if lod else 24)
    else:
        # A bowl has two faces. The shallow depression remains visible from above.
        profile=[(cap,.101),(cap+.023,.120),(cap+.049,.107),(cap+.063,.075),
                 (cap+.133,.067),(cap+.151,.109),(cap+.167,.140),(cap+.195,.166),
                 (cap+.217,.237),(cap+.251,.286),(cap+.289,.321),(cap+.313,.338),
                 (cap+.323,.335),(cap+.323,.305),(cap+.302,.276),(cap+.276,.211),
                 (cap+.260,.115),(cap+.254,.025)]
        turned(b,f,x,y,profile,TOP,'shallow dish and short stone stem',16 if lod else 32)

def add_balustrades(b,f,lod):
    lo_mid,lo_span,y0=frame_coordinates(f,0);hi_mid,hi_span,y1=frame_coordinates(f,9)
    # The right cap lies slightly higher in the photo than an equal-height
    # copy of the left cap at this camera pose. Read each cap independently.
    for side,lower_pixel,upper_pixel in [(-1,(378,893),(469,792)),(1,(842,892),(887,791))]:
        left_cap=f.plane(lower_pixel,y0)[1];top_cap=f.plane(upper_pixel,y1)[1]
        x0=lo_mid+side*lo_span/2;x1=hi_mid+side*hi_span/2
        newel(b,f,x0,y0,.004,left_cap,False,lod)
        newel(b,f,x1,y1,f.landing_z,top_cap,True,lod)
        # Projected end faces differ by only a few centimetres in plan.
        # Interpolate the measured centres along each stone rail.
        def at(y):return x0+(x1-x0)*(y-y0)/(y1-y0)
        def top(y):return left_cap+(top_cap-left_cap)*(y-y0)/(y1-y0)
        a,bh=y0+.185,y1-.147
        for label,half,down,up,mat in [('sloped cap',.148,-.136,0.,TOP),('under-rail',.092,-.185,-.136,RAIL)]:
            contour=Polygon([(a,top(a)+down),(bh,top(bh)+down),(bh,top(bh)+up),(a,top(a)+up)])
            b.prism(contour,-half,half,lambda y,z,offset:f.xyz(at(y)+offset,y,z),mat,'325 porch / '+label)
        for i in range(1,6):
            y=a+(bh-a)*i/6
            step=f.data['rise_m']*(1+int((y-y0)/f.data['tread_m']))
            ztop=top(y)-.183
            h=ztop-step
            # Visible cast uprights flare at their foot and head.
            ys=[(.0,.092),(.09,.096),(.19,.087),(.31,.058),(.54,.045),(.82,.060),(.95,.085),(1.,.089)]
            polygon=[(y-r,step+t*h)for t,r in ys]+[(y+r,step+t*h)for t,r in reversed(ys)]
            cross_section(b,f,polygon,at(y)-.077,at(y)+.077,RAIL,'stone upright under sloping cap')

def add_porch_stone(b,frame=None,lod=False):
    f=frame or PorchFrame()
    add_steps(b,f)
    add_balustrades(b,f,lod)
    add_porch_arch(b,f,lod)
