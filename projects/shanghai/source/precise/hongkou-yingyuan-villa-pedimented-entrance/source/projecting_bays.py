"""The rounded corner turret and the canted stair window visible in both street photographs."""
import math
from shapely.geometry import Polygon,box
from photo_architecture import Facade,opening
from mineral_render import CAST
from villa_joinery import BRICK,LIGHT_BRICK,MORTAR,LIMESTONE,WOOD,GLASS,SECOND,DARK,IRON,STONE

TILE='Dark red clay tile';WORN_TILE='Weathered clay tile';EAVE='Painted dark eaves'


def floor_slab(b,poly,low,high,mat,name):
    b.prism(poly,low,high,lambda x,y,z:(x,y,z),mat,name)


def arc_xy(cx,cy,r,theta):
    t=math.radians(theta);return (cx+r*math.cos(t),cy+r*math.sin(t))


def curved_band(b,cx,cy,rad,width,a0,a1,z0,z1,mat,name,lod):
    count=max(2,math.ceil((a1-a0)/(9 if lod else 3)))
    angles=[a0+(a1-a0)*i/count for i in range(count+1)]
    poly=Polygon([arc_xy(cx,cy,rad,a)for a in angles]+[arc_xy(cx,cy,rad-width,a)for a in reversed(angles)])
    floor_slab(b,poly,z0,z1,mat,name)


def taper(b,lower,upper,z0,z1,mat,name):
    count=len(lower);assert count==len(upper) and count>=3
    verts=[(x,y,z0)for x,y in lower]+[(x,y,z1)for x,y in upper]
    faces=[tuple(reversed(range(count))),tuple(range(count,2*count))]
    faces.extend((i,(i+1)%count,count+(i+1)%count,count+i)for i in range(count))
    b.add(verts,faces,mat,name)


def post(b,cx,cy,r,z0,z1,mat,names,lod):
    angles=[i*360/(12 if lod else 24) for i in range(12 if lod else 24)]
    for a,c,z,h in [(r*1.16,r*1.16,z0,.075),(r*1.14,r,z0+.075,.105),(r,r*.94,z0+.18,z1-z0-.36),(r*.94,r*1.19,z1-.18,.112),(r*1.20,r*1.20,z1-.068,.068)]:
        taper(b,[arc_xy(cx,cy,a,t)for t in angles],[arc_xy(cx,cy,c,t)for t in angles],z,z+h,mat,names)


def turret(b,d,lod):
    cx=d['measured_u']['turret_finial'];cy=2.587;r=d['frontage_outer_radius_m'];end0,end1=-194.,14.
    bands=[(0,.84,r-.07,CAST),(.84,1.01,r+.025,LIMESTONE),(3.17,3.32,r+.077,LIMESTONE),(3.32,3.48,r+.105,BRICK),
           (3.48,4.53,r-.018,CAST),(4.53,4.69,r+.075,LIMESTONE),(4.69,4.80,r+.13,LIMESTONE),(6.63,7.17,r-.01,CAST),
           (7.17,7.28,r+.075,LIMESTONE),(7.28,7.43,r+.14,CAST),(7.43,7.52,r+.03,LIMESTONE),(7.52,7.82,r+.06,CAST),
           (7.82,7.92,r+.20,LIMESTONE),(7.92,8.01,r+.25,EAVE)]
    for low,high,radius,mat in bands:
        curved_band(b,cx,cy,radius,.35,end0,end1,low,high,mat,'Turret/curved sill and cornice',lod)
    panels=[(-173,-123),(-115,-65),(-57,-7)];piers=[(end0,-173),(-123,-115),(-65,-57),(-7,end1)]
    for z0,z1 in [(1.01,3.17),(4.80,6.63)]:
        for lo,hi in piers:
            curved_band(b,cx,cy,r,.29,lo,hi,z0,z1,CAST,'Turret/curved waist piers',lod)
        for i,(lo,hi)in enumerate(panels):
            a=arc_xy(cx,cy,r,lo);c=arc_xy(cx,cy,r,hi);f=Facade(b,a,c,'Turret/sash '+str(i+1))
            panel=box(-f.length/2,z0,f.length/2,z1);inner=panel.buffer(-.075,join_style=2)
            f.prism(panel.buffer(.008,join_style=2),-.122,-.107,SECOND if i==2 else GLASS,'Glass')
            f.prism(panel.difference(inner),-.068,-.019,WOOD,'Timber surround')
            f.box(0,(z0+z1)/2,.042,z1-z0-.13,.056,-.049,WOOD,'Meeting stile')
            if not lod:f.box(0,z1-.20,f.length-.12,.022,.044,-.052,WOOD,'Head glazing bead')
        for ang in (-177,-119,-61,-3):
            x,y=arc_xy(cx,cy,r-.012,ang);post(b,x,y,.092,z0,z1,LIMESTONE,'Turret/round window colonettes',lod)
    # Roof pitch is visible above the left-hand circular bay in the winter panorama.
    span=2.41;nr=32 if lod else 64;rows=9 if lod else 15;segments=18 if lod else 34
    aa=[i*360/nr for i in range(nr)];roofbase=d['turret_eave'];crown=d['turret_cone_top']
    taper(b,[arc_xy(cx,cy,span,a)for a in aa],[arc_xy(cx,cy,.039,a)for a in aa],roofbase-.018,crown,TILE,'Turret/conical roof bed')
    for row in range(rows):
        t0=row/rows;t1=(row+1)/rows;z0=roofbase+(crown-roofbase)*t0;z1=roofbase+(crown-roofbase)*t1
        r0=(span-.065)*(1-t0)+.065;r1=(span-.065)*(1-t1)+.065
        count=max(7,round(segments*(1-.58*t0)));stagger=.5*(row%2)
        for k in range(count):
            a=(k+stagger+.01)*360/count;az=(k+stagger+.99)*360/count
            angles=[a+(az-a)*j/(2 if lod else 4) for j in range(3 if lod else 5)]
            lo=[arc_xy(cx,cy,r0+.015+(.027 if i%2 else .008),v)for i,v in enumerate(angles)]
            up=[arc_xy(cx,cy,r1+.009+(.015 if i%2 else 0),v)for i,v in enumerate(angles)]
            verts=[(*xy,zz) for ring,zz in [(lo,z0+.025),(up,z1+.025),(lo,z0-.018),(up,z1-.018)]for xy in ring];ln=len(lo)
            faces=[]
            for i in range(ln-1):
                faces.extend([(i,i+1,ln+i+1,ln+i),(2*ln+i,3*ln+i,3*ln+i+1,2*ln+i+1),
                              (i,2*ln+i,2*ln+i+1,i+1),(ln+i+1,3*ln+i+1,3*ln+i,ln+i)])
            faces.extend([(0,ln,3*ln,2*ln),(ln-1,3*ln-1,4*ln-1,2*ln-1)])
            b.add(verts,faces,WORN_TILE if (row*3+k)%7==0 else TILE,'Turret/staggered curved tiles')
    for rad0,rad1,z0,z1 in [(.12,.105,crown-.028,crown+.075),(.106,.072,crown+.075,crown+.162),(.065,.013,crown+.162,d['turret_finial'])]:
        taper(b,[arc_xy(cx,cy,rad0,a)for a in aa],[arc_xy(cx,cy,rad1,a)for a in aa],z0,z1,EAVE,'Turret/metal apex')


def projecting_window(b,f,cx,d,lod):
    # Two oblique glazed faces meet at the deep pale central mullion.
    profile=[(-.945,.023),(-.835,-.22),(-.205,-.531),(.205,-.531),(.835,-.22),(.945,.023)]
    sill=d['oriel_sill'];head=d['oriel_head'];name='Stair oriel/'
    def shape(scale):
        p=[(cx+x*scale,y*scale)for x,y in profile];return p+[(cx+.945*scale,.19),(cx-.945*scale,.19)]
    for factor,z,h,mat in [(.31,sill-.52,.079,LIMESTONE),(.49,sill-.441,.080,CAST),(.64,sill-.361,.081,LIMESTONE),(.78,sill-.28,.094,CAST),(.92,sill-.186,.069,LIMESTONE),(1.045,sill-.117,.117,MORTAR),(1.052,head,.075,LIMESTONE),(1.112,head+.075,.127,MORTAR)]:
        floor_slab(b,Polygon(shape(factor)),z,z+h,mat,name+'moulded corbels and caps')
    for j,(a,c)in enumerate(zip(profile,profile[1:])):
        v=Facade(b,(cx+a[0],a[1]),(cx+c[0],c[1]),'Stair oriel/facet '+str(j+1))
        p=box(-v.length/2,sill,v.length/2,head)
        if j==2:
            v.prism(p,-.135,.018,CAST,'Broad central pier')
        elif j in (0,4):
            v.prism(p,-.098,.020,MORTAR,'Outer brick jamb bed')
            n=27 if lod else 48
            for k in range(n):
                h=(head-sill)/n
                v.box(0,sill+(k+.5)*h,v.length+.005,h-.008,.035,.040,BRICK,'Outer brick reveals')
        else:
            inner=box(-v.length/2+.030,sill+.036,v.length/2-.030,head-.051)
            v.prism(p.difference(inner),-.126,.01,WOOD,'Fixed sash')
            v.prism(inner.buffer(.004,join_style=2),-.146,-.111,SECOND if j==3 else GLASS,'Recessed glazing')
            v.prism(inner.difference(inner.buffer(-.037,join_style=2)),-.099,-.055,WOOD,'Window bead')
            for z in (sill+.27*(head-sill),sill+.57*(head-sill),sill+.79*(head-sill)):
                v.box(0,z,v.length-.054,.042,.052,-.069,WOOD,'Horizontal glazing bars')
            v.box(0,(sill+head)/2,.048,head-sill-.085,.059,-.078,WOOD,'Intermediate mullion')
    # A shallow round-hipped hood projects over the glazing. A curved row of
    # upright brick headers is visible in both the 2020 and 2021 photographs.
    aa=[-180+180*i/(18 if lod else 42)for i in range((18 if lod else 42)+1)]
    plan=[(cx+1.08*math.cos(math.radians(q)),.054+.68*math.sin(math.radians(q)))for q in aa]
    cap=plan+[(cx+1.08,.16),(cx-1.08,.16)]
    floor_slab(b,Polygon(cap),head+.135,head+.253,MORTAR,name+'curved hood fascia')
    for a,c in zip(plan,plan[1:]):
        v=Facade(b,a,c,'Stair oriel/curved hood')
        v.box(0,head+.197,v.length-.006,.098,.041,.023,LIGHT_BRICK,'Upright brick')
    # Build one continuous hipped solid. Adjacent radial panels share their
    # ridge vertex instead of extruding a duplicate vertical cap at every seam.
    span=len(cap);z0=head+.24
    verts=[(x,y,z0+.023)for x,y in cap]+[(cx,.085,head+.62)]+[(x,y,z0-.025)for x,y in cap]
    peak=span;floor=span+1;faces=[tuple(reversed(range(floor,floor+span)))]
    for i in range(span):
        following=(i+1)%span
        faces.append((i,following,peak))
        faces.append((i,floor+i,floor+following,following))
    b.add(verts,faces,LIMESTONE,name+'shallow hipped hood')
    # The low arched light is visible between the sill corbels and the planting.
    low=opening(cx,.61,.76,.92,.265,14 if lod else 32)
    surround=low.buffer(.085,join_style=1).difference(low)
    f.prism(surround,-.014,.119,BRICK,'Stair oriel/low arched reveal');f.prism(low,-.231,-.21,DARK,'Stair oriel/arched subwindow')
    f.prism(low.difference(low.buffer(-.052,join_style=2)),-.175,-.132,WOOD,'Stair oriel/subwindow liner')
    for side in (-1,1):f.box(cx+side*.136,1.008,.029,.697,.055,-.155,IRON,'Stair oriel/subwindow bars')

