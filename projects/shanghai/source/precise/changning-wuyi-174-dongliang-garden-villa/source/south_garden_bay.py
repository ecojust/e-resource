"""South garden storefront and balcony photographed at the October 2024 opening."""
from math import cos, hypot, pi, sin, sqrt

from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from wuyi_fabric import DARK, DOOR, FABRIC, FRAME, IRON, SOFFIT, STONE, WALL, paint, slab, wall

SHOP_GLASS = '174 | south shop glazing'
DOOR_GLASS = '174 | south timber door glazing'
PALETTE = {
    SHOP_GLASS: paint((150, 121, 79), .22, .16),
    DOOR_GLASS: paint((79, 67, 49), .24, .17),
}

HALF_CURVE = 2.36947
SHOULDER = 1.78127
OUT = 2.12
FASCIA = .55760
DOOR_PITCH = 1.70685
DOOR_WIDTH = 1.02482
RAIL_HEIGHT = .99718
# Left and right mirror only across the stable storefront joints in photograph 08.
# Each pair is (horizontal offset from centre, distance from the rear wall).
GLASS = [(.73653, 2.052), (1.23860, 1.993), (1.85937, 1.858), (2.43, 1.63)]


def round_edge(x):
    sag = OUT - SHOULDER
    radius = (HALF_CURVE ** 2 + sag ** 2) / (2 * sag)
    return OUT - radius + sqrt(max(0, radius ** 2 - x * x))


def local_plan(x, out, layout):
    return layout.get('south_bay_centre_x', 9.55) - x, layout.get('south_wall_y', 13.60) + out


def south_openings(layout=None):
    """Wall openings in the local X/Z chart, looking from the garden, X positive to the east."""
    layout = layout or {}
    deck = layout.get('south_deck_z', 2.96)
    sill = deck + .035
    soffit = layout.get('south_bay_soffit_z', 5.22)
    head = min(deck + 2.175, soffit - .085, layout.get('south_eave_z', 5.57) - .11)
    return {
        'storefront': box(-GLASS[-1][0], .026, GLASS[-1][0], deck - FASCIA),
        **{f'upper-door-{i}': box(x - DOOR_WIDTH / 2, sill, x + DOOR_WIDTH / 2, head)
           for i, x in enumerate((-DOOR_PITCH, 0., DOOR_PITCH), 1)},
    }


def local_face(b, polygon, outward, depth, material, label, layout):
    a = local_plan(0., outward, layout)
    c = local_plan(1., outward, layout)
    wall(b, polygon, a, c, 0., depth, material, label)


def window_grid(b, a, c, opening, cols, rows, *, thick, stile, material, glass, label):
    left, base, right, head = opening.bounds
    margin = thick
    inner = box(left + margin, base + margin, right - margin, head - margin)
    wall(b, opening.difference(inner), a, c, .002, .062, material, label + ' outer frame')
    l, z, r, h = inner.bounds
    cuts = [l + (r-l)*i/cols for i in range(cols + 1)]
    rails = [z + (h-z)*j/rows for j in range(rows + 1)]
    for i, x in enumerate(cuts[1:-1], 1):
        width = stile * (1.5 if i * 2 == cols else 1.)
        wall(b, box(x-width/2, z, x+width/2, h), a, c, .014, .051, material, label + ' upright')
    for i, (x, end) in enumerate(zip(cuts, cuts[1:])):
        x += (stile * (.75 if 2*i == cols else .5)) if i else 0
        end -= (stile * (.75 if 2*(i+1) == cols else .5)) if i+1 < cols else 0
        for j, (lo, hi) in enumerate(zip(rails, rails[1:])):
            if j:
                wall(b, box(x, lo-.008, end, lo+.008), a, c, .021, .047, material, label+' glazing bar')
                lo += .008
            if j+1 < rows:
                hi -= .008
            wall(b, box(x, lo, end, hi), a, c, .052, .059, glass, label+' pane')


def upper_doors(b, layout, deck):
    openings = south_openings(layout)
    for i, x in enumerate((-DOOR_PITCH, 0., DOOR_PITCH), 1):
        bounds = openings[f'upper-door-{i}'].bounds
        l, base, r, head = bounds
        a, c = local_plan(l, -.10, layout), local_plan(r, -.10, layout)
        # The two timber leaves meet on a substantial stile; each leaf has two columns.
        label = 'south terrace timber door '+str(i)
        jamb = .034
        perimeter = box(0,base,r-l,head).difference(box(jamb,base+jamb,r-l-jamb,head-jamb))
        wall(b, perimeter, a, c, .0, .085, DOOR, label+' jamb and head')
        for j in range(2):
            start = jamb+(r-l-2*jamb)*j/2+.002
            end = jamb+(r-l-2*jamb)*(j+1)/2-.002
            window_grid(b,a,c,box(start,base+.024,end,head-.035),2,6,thick=.029,stile=.017,
                        material=DOOR,glass=DOOR_GLASS,label=label+' leaf '+str(j+1))
        # Sloping fabric with visible lower hanging hem. Far side behind the fabric is unrecorded.
        hem = deck + 1.833
        profile = Polygon([(0,head+.068),(.33,hem+.034),(.33,hem),
                           (.30,hem),(.30,hem+.026),(0,head+.04)])
        width = DOOR_WIDTH * 1.15
        def mapper(d,z,across):
            wx, wy = local_plan(x+across, d, layout)
            return wx, wy, z
        # d cross Z points east, i.e. negative global X. Reverse polygon d axis for the extrusion.
        b.prism(profile,-width/2,width/2,lambda d,z,n:mapper(d,z,-n),FABRIC,label+' pale folding awning')


def lower_storefront(b, layout, deck):
    points = [(-x,d) for x,d in reversed(GLASS)] + GLASS
    upper = deck-FASCIA-.025
    for i, (start, end) in enumerate(zip(points,points[1:])):
        a,c=local_plan(*start,layout),local_plan(*end,layout)
        length=hypot(c[0]-a[0],c[1]-a[1])
        name='south folded storefront face '+str(i+1)
        if i in (0,1,5,6):
            base=.34
            mid=deck-1.03
            # A stone upright divides each pair of oblique lights.
            jamb=.050
            openings=[box(jamb,base,length-jamb,mid-.045),box(jamb,mid+.045,length-jamb,upper)]
            frame=box(0,.03,length,upper+.008).difference(unary_union(openings))
            wall(b,frame,a,c,.0,.125,STONE,name+' sloping sill and transom shell')
            wall(b,box(.009,.040,length-.009,base-.066),a,c,-.008,.001,WALL,name+' roughcast apron')
            for j,opening in enumerate(openings):
                window_grid(b,a,c,opening,2,1 if j else 4,thick=.022,stile=.014,
                            material=FRAME,glass=SHOP_GLASS,label=name+' '+('upper' if j else 'lower'))
        else:
            window_grid(b,a,c,box(0,.04,length,upper),4 if i==3 else 2,6,thick=.026,
                        stile=.016,material=FRAME,glass=SHOP_GLASS,label=name)
    # Two stone jambs with roughcast returns. The existing building closes the back at both sides.
    for x in (-GLASS[-1][0],GLASS[-1][0]):
        a,c=local_plan(x,0.,layout),local_plan(x,GLASS[-1][1],layout)
        if x<0:a,c=c,a
        wall(b,box(0,.025,GLASS[-1][1],upper),a,c,.005,.105,WALL,'south bay side return')


def curled_pair(l, r, z0, z1, lod):
    centre=(l+r)*.5
    middle=(z0+z1)*.5
    span=(r-l)*.43
    high=(z1-z0)*.435
    loops=[]
    for side in (-1,1):
        for up in (-1,1):
            p=[(centre+side*.012, middle)]
            # Four open C scrolls which curl back into the middle of the adjacent lobe.
            count=13 if lod else 26
            for j in range(count+1):
                t=j/count
                theta=t*1.76*pi
                radius=1.-.72*t
                p.append((centre+side*(.018+span*.5*(1.-radius*cos(theta))),
                          middle+up*(.040+high*(.42+.42*radius*sin(theta)-.42*radius*cos(theta)))))
            loops.append(LineString(p).buffer(.0105,cap_style='square',join_style='round',quad_segs=1))
    return unary_union(loops)


def basket_panel(l,r,z0,z1,lod):
    spans=[]
    width=r-l
    inset=.024
    x0,x1=l+inset,r-inset
    low=z0+.026;high=z1-.03
    rim=box(x0,low,x1,high).difference(box(x0+.013,low+.014,x1-.013,high-.014))
    for j in range(1,5):
        x=x0+(x1-x0)*j/5
        spans.append(box(x-.006,low+.052,x+.006,high-.068))
        for z in (low+.075,high-.09):
            spans.append(Polygon([(x,z-.035),(x+.014,z),(x,z+.035),(x-.014,z)]))
    for band,sg in [(low+.048,1),(high-.058,-1)]:
        count=4 if lod else 5
        step=(x1-x0)/count
        for j in range(count):
            x=x0+step*(j+.5)
            p=[(x+step*.46*cos(2*pi*i/12),band+sg*.031*sin(2*pi*i/12)) for i in range(13)]
            spans.append(LineString(p).buffer(.0065,cap_style='flat',join_style='round',quad_segs=1))
    return unary_union([rim,*spans])


def railing(b, stations, layout, deck, lod):
    bottom=deck+.083;top=deck+RAIL_HEIGHT
    for i, ((xa,da),(xb,db),style) in enumerate(stations):
        a=local_plan(xa,da,layout);c=local_plan(xb,db,layout)
        width=hypot(c[0]-a[0],c[1]-a[1])
        def metal(profile,name):
            wall(b,profile,a,c,-.012,.015,IRON,'south garden rail '+str(i+1)+' '+name)
        for z,h in [(bottom,.028),(top-.135,.023),(top-.031,.035)]:
            metal(box(0,z,width,z+h),'horizontal bar')
        for x in (0.,width):
            if x and i+1!=len(stations):continue
            metal(box(x-.012,bottom-.07,x+.012,top+.005),'square standard')
            metal(box(x-.025,deck+.011,x+.025,bottom-.018),'standard foot')
        halves=1 if style=='basket' else 2 if style=='return' else 1
        for j in range(halves):
            l=width*j/halves;r=width*(j+1)/halves
            pattern=(basket_panel if style=='basket' else curled_pair)(l,r,bottom+.029,top-.124,lod)
            metal(pattern,'framed vertical castwork' if style=='basket' else 'paired scrolls')
            if style in ('scroll','return'):
                for frac in (.13,.87):
                    s=l+(r-l)*frac
                    metal(box(s-.006,bottom+.029,s+.006,top-.033),'picket')
        for j in range(1,4):
            s=width*j/4
            ring=[(s+.032*cos(2*pi*k/10),top-.079+.036*sin(2*pi*k/10)) for k in range(11)]
            metal(LineString(ring).buffer(.006,quad_segs=1),'open upper frieze')


def add_south_bay(b,lod=False,layout=None):
    """Build the 5.78 m south wall and its bow; the adjoining gables stay outside the two end joints."""
    layout=layout or {};deck=layout.get('south_deck_z',2.96)
    eave=layout.get('south_eave_z',5.57)
    left,right=-2.89,2.89
    openings=south_openings(layout)
    main=box(left,.015,right,eave).difference(unary_union(list(openings.values())))
    local_face(b,main,0.,.245,WALL,'south garden rendered wall with four openings',layout)
    upper_doors(b,layout,deck);lower_storefront(b,layout,deck)
    # The continuous light cover above the three cloth awnings has a separately estimated depth.
    cornice=layout.get('south_bay_soffit_z',5.22)
    footprint=Polygon([local_plan(x,d,layout)for x,d in
                       [(left+.015,-.012),(right-.015,-.012),(right-.015,.32),(left+.015,.32)]])
    slab(b,footprint,cornice,cornice+.075,SOFFIT,'south continuous pale overhang beneath tiled roof')

    n=20 if lod else 48
    arc=[(x,round_edge(x))for x in [-HALF_CURVE+2*HALF_CURVE*i/n for i in range(n+1)]]
    outline=[(left,0),(left,SHOULDER),*arc,(right,SHOULDER),(right,0)]
    shape=Polygon([local_plan(x,y,layout) for x,y in outline])
    slab(b,shape,deck-FASCIA,deck-.025,STONE,'south balcony continuous curved fascia')
    slab(b,shape,deck-.025,deck,STONE,'south balcony rounded coping')
    slab(b,shape.buffer(-.028,join_style='mitre'),deck-FASCIA-.018,deck-FASCIA,SOFFIT,'south balcony soffit')
    end=2.82
    xs=[-HALF_CURVE+2*HALF_CURVE*i/9 for i in range(10)]
    posts=[(-end,.10),(-end,SHOULDER-.055),*[(x,round_edge(x)-.055) for x in xs],
           (end,SHOULDER-.055),(end,.10)]
    kinds=['return','basket',*['scroll' if i%2==0 else 'basket' for i in range(9)],'basket','return']
    railing(b,[(a,c,k) for a,c,k in zip(posts,posts[1:],kinds)],layout,deck,lod)
