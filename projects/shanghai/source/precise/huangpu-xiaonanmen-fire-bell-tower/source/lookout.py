"""Spiral stair, open observation deck, glazed watch room and low roof balustrade."""
from math import cos, sin, pi
from shapely.geometry import Point, Polygon, box
from tower_frame import MASONRY, BORDER, LIP, IRON, CAB, GALLERY, EAVE, SIDES, half, face, skin, oval_band

CAGE = 'Dark oxidised stair cage'
STEPS = 'Worn metal stair tread'
WINDOW = 'Watch room glazing'
SASH = 'Dark painted window frames'
DECK = 'Weathered observation deck'


def stair(builder,lod):
    stop=28.96
    # The open guard surrounds the steps of the photographed iron spiral stair.
    # Its pitch and tread angle are estimates; individual risers cannot be counted in every span.
    steps=148;rise=stop/steps;turn=2*pi/15
    # The 2017 views straight up and down the shaft show daylight through an open well.
    # Each tread spans between the smaller inner cylindrical guard and the outer cage.
    radius=1.16;inner=.48;sub=2 if lod else 4
    all_vertices=[];all_faces=[]
    for i in range(steps):
        z=(i+1)*rise
        start=i*turn;end=(i+1)*turn+.009
        ring=[(r*cos(t),r*sin(t))for r,ts in [(radius,range(sub+1)),(inner,reversed(range(sub+1)))]
              for j in ts for t in [start+(end-start)*j/sub]]
        offset=len(all_vertices);count=len(ring)
        all_vertices.extend([(x,y,z-.044)for x,y in ring]+[(x,y,z)for x,y in ring])
        for j in range(sub):
            k=count-1-j
            a,b,c,d=(offset+j,offset+j+1,offset+k-1,offset+k)
            all_faces.extend([(d,c,b,a),(a+count,b+count,c+count,d+count)])
        for j in range(count):
            k=(j+1)%count
            all_faces.append((offset+j,offset+k,offset+k+count,offset+j+count))
    builder.add(all_vertices,all_faces,STEPS,'spiral stair/individual wedge treads')
    # The photographs show flat strips, periodic rivets and iron hoop bands.
    # Cylindrical rods would close too little of the view upward through this shaft.
    import numpy as np
    sides=22 if lod else 40
    for guard_radius,count,width,label in [(1.23,26,.065,'outer'),(.465,18,.052,'inner')]:
        for i in range(count):
            theta=i*2*pi/count
            radial=np.array([cos(theta),sin(theta),0.])
            tangent=np.array([-sin(theta),cos(theta),0.])
            builder.box([guard_radius*radial[0],guard_radius*radial[1],stop/2],
                        [.021,width,stop],CAGE,basis=[radial,tangent,[0,0,1]],
                        label='spiral stair/'+label+' cage flat verticals')
        for j in range(43):
            z=.11+j*(stop-.12)/42
            # Thin vertical strips overlap the continuous hoop on its outside face.
            ring=[(guard_radius*cos(t*2*pi/sides),guard_radius*sin(t*2*pi/sides),z)
                  for t in range(sides+1)]
            builder.tube(ring,.025 if label=='inner' else .031,CAGE,5 if lod else 7,
                         'spiral stair/'+label+' cage hoops')
            if not lod and j%3==0:
                for k in range(0,count,2):
                    t=2*pi*k/count
                    # Rivet heads are visible where the straps overlap a hoop.
                    a=[(guard_radius+.008)*cos(t),(guard_radius+.008)*sin(t),z]
                    b=[(guard_radius+.030)*cos(t),(guard_radius+.030)*sin(t),z]
                    builder.tube([a,b],.027,IRON,7,'spiral stair/rivet heads')
    if not lod:
        pts=[(.51*cos(i*turn/3),.51*sin(i*turn/3),i*rise/3+.80)for i in range(3*(steps-5))]
        builder.tube(pts,.028,IRON,7,'spiral stair/inner continuous handrail')


def slab(b,h,halfwidth,width,hole,material,label):
    sq=box(-halfwidth,-halfwidth,halfwidth,halfwidth)
    if hole:
        sq=sq.difference(Point(0,0).buffer(hole,quad_segs=12))
    b.plan_prism(sq,h-width,h,material,label)


def railing(b,side,z,h,lod,roof):
    if roof:
        radius=1.82
        def p(u,at,depth):
            x,y = ((u,-radius-depth),(radius+depth,u),(-u,radius+depth),(-radius-depth,-u))[side]
            return x,y,at
        end=radius-.075
        group='roof parapet'
    else:
        radius=half(z)-.30
        end=radius-.14
        def p(u,at,depth):
            x,y=((u,-radius-depth),(radius+depth,u),(-u,radius+depth),(-radius-depth,-u))[side]
            return x,y,at
        group='open watch deck'
    for height,thickness,depth in [(z+.12,.18,.13),(z+h-.075,.15,.105)]:
        b.prism(box(-end,height-thickness/2,end,height+thickness/2),-.10,depth,p,LIP,SIDES[side]+'/'+group+' hand and footrails')
    count=9 if roof else 14
    for i in range(count):
        u=-end+(i+.5)*2*end/count
        # Each upright is separate, with the wider cast foot and cap visible in the photographs.
        w=.062 if roof else .065
        shape=box(u-w,z+.19,u+w,z+h-.145)
        b.prism(shape,-.055,.055,p,MASONRY,SIDES[side]+'/'+group+' balusters')
        if not lod:
            for at in (z+.21,z+h-.18):
                b.prism(box(u-w-.022,at-.037,u+w+.022,at+.037),-.064,.072,p,BORDER,SIDES[side]+'/'+group+' baluster collars')


def watch_room(b,lod):
    # Every photograph shows the panels and rectangular windows. Its original bell is absent.
    slab(b,GALLERY+.045,half(GALLERY)-.012,.17,1.30,DECK,'open watch deck/floor with stairwell')
    slab(b,CAB-.02,half(CAB)-.03,.15,1.27,DECK,'watch room/lookout floor and central aperture')
    for side in range(4):
        railing(b,side,GALLERY+.04,1.00,lod,False)
        window=box(-1.36,31.23,1.36,32.54)
        # Follow the converging corner posts instead of extending wall slices beyond the taper.
        shell=Polygon([(-half(CAB)+.30,CAB-.02),(half(CAB)-.30,CAB-.02),
                       (half(EAVE)-.29,EAVE-.12),(-half(EAVE)+.29,EAVE-.12)])
        skin(b,side,shell.difference(window),-.25,-.055,MASONRY,'watch room/cast wall with real window')
        skin(b,side,window.buffer(.075,join_style=2).difference(window),-.065,.015,BORDER,'watch room/window reveal')
        skin(b,side,window,-.228,-.202,WINDOW,'watch room/recessed glazing')
        for u in (-1.33,-.45,.45,1.33):
            skin(b,side,box(u-.044,31.23,u+.044,32.54),-.161,-.102,SASH,'watch room/three-sash mullions')
        for z in (31.25,32.50):
            skin(b,side,box(-1.36,z-.04,1.36,z+.04),-.168,-.102,SASH,'watch room/window head and sill')
        # Over the three windows the surviving narrow frieze carries another row of cast ovals.
        skin(b,side,box(-1.68,32.67,1.68,33.04),-.050,.024,BORDER,'watch room/frieze backing')
        oval_band(b,side,32.87,.070,lod)
        for u in (-1.73,1.73):
            skin(b,side,Polygon([(u-.09,32.20),(u+.09,32.20),(u+.12,EAVE-.10),(u-.12,EAVE-.10)]),-.005,.18,BORDER,'watch room/cornice brackets')
    slab(b,EAVE-.044,2.43,.19,0,BORDER,'roof/under-eave moulding')
    slab(b,EAVE+.052,2.61,.105,0,LIP,'roof/overhanging square coping')
    for side in range(4):railing(b,side,EAVE+.047,1.24,lod,True)
    for sx in (-1,1):
        for sy in (-1,1):
            x,y=sx*1.82,sy*1.82
            for lo,hi,width,mat in [(EAVE+.055,34.83,.40,MASONRY),(34.83,34.92,.45,BORDER),
                                    (34.92,35.10,.48,MASONRY),(35.10,35.20,.51,LIP)]:
                b.box([x,y,(lo+hi)/2],[width,width,hi-lo],mat,label='roof/four squared finial piers')
