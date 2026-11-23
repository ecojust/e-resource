"""Two wide louvred windows, the double door and two small windows on the street wall."""
from pathlib import Path
import json

from shapely.geometry import Polygon, box

from materials import DEEP, GLASS, IRON, LOUVER, WOOD
from photo_plane import opening, hit

RECORD = json.loads((Path(__file__).resolve().parents[1] / 'measurements/shutter-panel-observations.json').read_bytes())

def apertures():
    """Shapely rectangles in the u,z plane of the street facing wall."""
    scale = 800 / RECORD['photo']['pixels'][0]
    return {name: opening(*[(u*scale,v*scale) for u,v in corners])
            for name,corners in RECORD['opening_quads_native_tl_tr_br_bl'].items()}

def frame(f, rect, border_u, border_z, label, back=-.024, front=.004):
    u0,z0,u1,z1 = rect.bounds
    inset = box(u0+border_u,z0+border_z,u1-border_u,z1-border_z)
    f.solid(rect.difference(inset),back,front,WOOD,label)
    return inset

def scan_heights(scan):
    x=sum(scan['column_average_x'])/2
    z=[hit(x*800/3968,y*800/3968,.030)[1] for y in scan['bright_edges_y']]
    # Regular packing is estimated individually for each photographed tier.
    steps=sorted(abs(a-b) for a,b in zip(z,z[1:]))
    pitch=steps[len(steps)//2]
    centre=sum(z)/len(z)
    return [centre+((len(z)-1)/2-i)*pitch for i in range(len(z))],pitch

def blades(f,left,right,scan,label):
    heights,pitch=scan_heights(scan)
    for centre in heights:
        profile=Polygon([(.012,centre-pitch*.36),(.048,centre+pitch*.20),
                         (.048,centre+pitch*.36),(.012,centre-pitch*.20)])
        f.b.prism(profile,left,right,lambda d,h,u:f.point(u,d,h),LOUVER,label+' | slats')

def add_wide(f, rect, label):
    u0,z0,u1,z1=rect.bounds
    inside=frame(f,rect,.030*(u1-u0),.046*(z1-z0),label+' | outer frame')
    f.solid(inside,-.11,-.095,DEEP,label+' | shade')
    l,b,r,t=inside.bounds
    step=(r-l)/4
    for column in range(4):
        start=l+column*step
        inner=frame(f,box(start,b,start+step,t),step*.075,(t-b)*.018,label+' | leaf '+str(column+1))
        a,c,e,g=inner.bounds
        scans=RECORD['wide_windows'][label]
        for top,below in zip(scans,scans[1:]):
            tlevels,pitch=scan_heights(top)
            blevels,_=scan_heights(below)
            centre=(tlevels[-1]+blevels[0])/2
            f.rect(a,e,centre-pitch*.33,centre+pitch*.33,-.023,.003,WOOD,label+' | rails')
        for scan in scans:
            blades(f,a,e,scan,label+' | leaf '+str(column+1))

def add_small(f, rect, label):
    u0,z0,u1,z1=rect.bounds
    inner=frame(f,rect,.034*(u1-u0),.075*(z1-z0),label+' | outer frame')
    l,b,r,t=inner.bounds
    f.solid(inner,-.061,-.052,GLASS,label+' | two panes')
    mid=(l+r)/2
    f.rect(mid-.026,mid+.026,b,t,-.047,.001,WOOD,label+' | centre stile')

def add_door(f,rect):
    u0,z0,u1,z1=rect.bounds
    width,height=u1-u0,z1-z0
    def x(n):return u0+width*n
    def z(n):return z0+height*n
    f.solid(rect,-.110,-.096,DEEP,'entry | shade')
    f.rect(u0,u1,z0,z(.064),-.075,.003,WOOD,'entry | sill')
    # The frame of the transom overhangs two independently hinged doors.
    frame(f,rect,.038*width,.036*height,'entry | outer casing')
    working=lambda xx,yy:hit(xx*800/3968,yy*800/3968)
    left,right=[working(i,1878)[0] for i in (2398,2841)]
    transom=box(left,z(.790),right,z(1))
    face=transom
    scans=RECORD['door']['scan']
    ranges=RECORD['door']['transom_light_bounds_native']
    top_levels,pitch=scan_heights(scans[0])
    for l,r in ranges:
        a,e=working(l,1878)[0],working(r,1878)[0]
        pane=box(a,min(top_levels)-pitch*.48,e,max(top_levels)+pitch*.48)
        face=face.difference(pane)
        blades(f,a,e,scans[0],'entry | transom')
    f.solid(face,-.024,.004,WOOD,'entry | transom rails and stiles')
    # Both leaves have a solid lower skirt and two columns above their paired pulls.
    middle=working(2625,2140)[0]
    leaves=((left,middle-.005),(middle+.005,right))
    for n,(a,e) in enumerate(leaves):
        wooden=box(a,z(.065),e,z(.790))
        for x1,x2 in RECORD['door']['leaf_light_bounds_native'][n*2:n*2+2]:
            L=working(x1,1987)[0]
            R=working(x2,1987)[0]
            for scan in scans[1:]:
                levels,pitch=scan_heights(scan)
                pane=box(L,min(levels)-pitch*.48,R,max(levels)+pitch*.48)
                wooden=wooden.difference(pane)
                blades(f,L,R,scan,'entry | leaf '+str(n+1))
        f.solid(wooden,-.067,.003,WOOD,'entry | leaf '+str(n+1))
        panel=box(a+.035*width,z(.109),e-.035*width,z(.332))
        frame(f,panel,.025,.022,'entry | lower recessed panels',.003,.014)
        handle=working((2617,2644)[n],2155)[0]
        f.rail([(handle,-.003,z(.332)),(handle,-.052,z(.342)),(handle,-.052,z(.507)),(handle,-.003,z(.517))],
               .012,IRON,'entry | paired pulls',8)

def add_shutters(f,lod=False):
    parts=apertures()
    for label in ('small-left','small-right'):
        add_small(f,parts[label],label)
    for label in ('wide-left','wide-right'):
        add_wide(f,parts[label],label)
    add_door(f,parts['door'])
