"""Three independently observed parts adjoining the west lawn gable of house eight."""
from math import ceil, cos, hypot, sin, sqrt

import json
from pathlib import Path
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from garden_fabric import BOARD, BRASS, BRICK, CREAM, METAL, PLINTH, TREAD, block, face, paint

GLAZING = 'Hongji 8 | dark garden glazing'
TIMBER = 'Hongji 8 | stained entrance timber'
TRIM = 'Hongji 8 | weathered off-white trim'
DECK = 'Hongji 8 | terrace and roof deck'
PALETTE = {GLAZING:paint((65,83,78),.28,.14), TIMBER:paint((119,78,48),.60),
           TRIM:paint((202,200,186)), DECK:paint((117,115,103))}


def wall(b, outline, a, c, front, back, material, tag):
    """Extrude a cut wall in local horizontal / vertical coordinates."""
    length = hypot(c[0]-a[0], c[1]-a[1])
    dx, dy = (c[0]-a[0])/length, (c[1]-a[1])/length
    def place(s,z,n):
        return (a[0]+dx*s+dy*n, a[1]+dy*s-dx*n, z)
    for poly in getattr(outline, 'geoms', [outline]):
        if poly.geom_type == 'Polygon' and poly.area > 1e-8:
            b.prism(poly,-back,-front,place,material,'8 | '+tag)


def slab(b, outline, bottom, top, material, tag):
    for poly in getattr(outline, 'geoms', [outline]):
        if poly.geom_type == 'Polygon' and poly.area > 1e-8:
            b.prism(poly,bottom,top,lambda x,y,z:(x,y,z),material,'8 | '+tag)


def arc_profile(mid, half, spring, crown, sill, steps):
    rise = crown - spring
    radius = (half*half+rise*rise)/(2*rise)
    zc = crown - radius
    edge=[]
    for i in range(steps+1):
        dx = half*(1.-2.*i/steps)
        edge.append((mid+dx,zc+sqrt(max(0.,radius*radius-dx*dx))))
    return Polygon([(mid-half,sill),(mid+half,sill),*edge])


def numeral(b, lod, y):
    reference = Path(__file__).resolve().parents[1] / 'measurements/eight-raised-brass-number.json'
    contours = json.loads(reference.read_bytes())['face_profile']
    # The numeral is slightly left of the plate center. Both irregular holes
    # follow the rectified close photograph, including their different sizes.
    rings = [[(10.235 + 1.122*u, 3.808 - 1.084*v) for u,v in contour]
             for contour in contours]
    shape = Polygon(rings[0], rings[1:])
    if lod:
        shape = shape.simplify(.008, preserve_topology=True)
    face(b,shape,y-.049,y-.012,BRASS,'8 | raised brass numeral with two counters')


def numbered_wing(b,lod):
    left,right=7.12,11.60
    front,rear=.095,6.52
    cap=4.23
    # The oblique photograph shows the corner on the numbered side. A
    # shallow crown and two brick-coloured returns close the cropped extent.
    outer=arc_profile(9.103,1.764,1.871,2.652,.060,24 if lod else 54)
    opening=arc_profile(9.103,1.540,1.790,2.432,.064,24 if lod else 54)
    face(b,box(left,0,right,cap).difference(outer),front,front+.181,BRICK,
         '8 | numbered wing brickwork around opening')
    face(b,outer.difference(opening),front-.034,front+.132,TRIM,
         '8 | segmental arch and full-height jambs')
    inner=opening.buffer(-.040,join_style=2)
    face(b,opening.difference(inner),front+.082,front+.131,METAL,'8 | arch glazing frame')
    xmin,_,xmax,_=inner.bounds
    for i in range(3):
        l=xmin+(xmax-xmin)*i/3
        r=xmin+(xmax-xmin)*(i+1)/3
        glazing=inner.intersection(box(l+.013,.0,r-.013,2.6))
        face(b,glazing,front+.159,front+.172,GLAZING,'8 | arched entrance glass '+str(i+1))
        if i:
            face(b,inner.intersection(box(l-.020,.04,l+.020,2.6)),front+.103,front+.154,
                 METAL,'8 | arched entrance transomless mullion '+str(i))
    for tag,x0,x1 in (('left',left,7.335),('right',10.872,right)):
        block(b,x0,x1,front-.027,front+.008,.01,.39,PLINTH,'8 | wing '+tag+' low plinth')
    block(b,right-.162,right,front+.182,rear,0,cap,BRICK,'8 | numbered wing south return')
    block(b,left,left+.15,front+.182,rear,0,cap,BRICK,'8 | numbered wing inner end')
    block(b,left+.15,right-.162,rear-.158,rear,0,cap,BRICK,'8 | numbered wing rear cut')
    block(b,left-.032,right+.050,front-.050,rear+.024,cap,cap+.142,TRIM,'8 | flat wing fascia')
    block(b,left-.050,right+.073,front-.062,rear+.035,cap+.142,cap+.189,CREAM,'8 | wing coping')
    block(b,left+.030,right-.042,front+.035,rear-.072,cap+.189,cap+.202,DECK,'8 | lowered roof finish')
    mount_y=front-.009
    block(b,10.235,11.357,mount_y-.053,mount_y,2.724,3.808,BOARD,'8 | square number backplate')
    numeral(b,lod,mount_y-.053)
    # A narrow black two-level threshold is visible through the garden hedge
    # in the 2016 original. Its risers have only an image-scale estimate.
    block(b,7.28,10.93,front-.37,front+.18,-.014,.031,TREAD,'8 | garden threshold outer step')
    block(b,7.32,10.89,front-.22,front+.19,.031,.064,METAL,'8 | dark entrance sill')


def diamond_panel(b,lod,a,c,low,high,step,name,depth=.055):
    length=hypot(c[0]-a[0],c[1]-a[1])
    envelope=box(0,low,length,high)
    outer=envelope.difference(box(.031,low+.033,length-.031,high-.034))
    lines=[]
    height=high-low
    ran=ceil(length/step)+4
    for i in range(-3,ran):
        x=i*step
        for direction in (-1,1):
            line=LineString([(x,low),(x+direction*.48*height,high)])
            lines.append(line.buffer(.009 if not lod else .010,cap_style=2))
    bars=unary_union(lines).intersection(box(.020,low+.021,length-.020,high-.021))
    # Keep the boundary and the two families of diagonal bars as a single
    # editable cast-iron field, with openings through to the deck.
    wall(b,outer.union(bars),a,c,0,depth,METAL,name)


def terrace(b,lod):
    left,right,front,back=-3.50,.004,1.22,4.88
    top=3.16
    h0,h1=box(-2.22,.113,-.83,2.12),box(.76,.10,2.18,2.17)
    face(b,box(left,0,right,top).difference(h0),front,front+.13,CREAM,'8 | flat terrace garden wall')
    face(b,h0.difference(h0.buffer(-.045,join_style=2)),front+.050,front+.098,METAL,'8 | terrace garden glazing edge')
    face(b,h0.buffer(-.044,join_style=2),front+.129,front+.144,GLAZING,'8 | tall terrace garden glazing')
    a,c=(left,back),(left,front)
    wall(b,box(0,0,back-front,top).difference(h1),a,c,0,.144,CREAM,'flat terrace north face')
    wall(b,h1.difference(h1.buffer(-.061,join_style=2)),a,c,.035,.099,TIMBER,'terrace return door frame')
    for j in range(2):
        l=.821+j*.649;r=l+.644
        light=box(l+.055,.26,r-.055,2.09)
        wall(b,box(l,.112,r,2.11).difference(light),a,c,.078,.125,TIMBER,'terrace return door leaf '+str(j+1))
        wall(b,light,a,c,.127,.142,GLAZING,'terrace return door light '+str(j+1))
    block(b,right-.12,right,front+.13,back,0,top,CREAM,'8 | terrace east wall')
    block(b,left+.14,right-.12,back-.125,back,0,top,CREAM,'8 | terrace inner closure')
    block(b,left-.042,right+.012,front-.053,back+.008,top-.070,top+.032,TRIM,'8 | terrace slab fascia')
    block(b,left-.068,right+.014,front-.074,back+.02,top+.032,top+.082,CREAM,'8 | terrace cap')
    block(b,left+.020,right-.04,front+.025,back-.06,top+.082,top+.096,DECK,'8 | visible terrace deck')
    low,high=top+.095,4.34
    for lab,p,q in [('lawn',(left+.025,front+.042),(right-.025,front+.042)),
                    ('north',(left+.025,back-.025),(left+.025,front+.042))]:
        count=3
        for i in range(count):
            start=tuple(v+(r-v)*i/count for v,r in zip(p,q));end=tuple(v+(r-v)*(i+1)/count for v,r in zip(p,q))
            diamond_panel(b,lod,start,end,low,high,.185,'terrace '+lab+' lattice '+str(i+1))


def north_wall_opening(layout):
    """Hole in the north-facing gable. Coordinates are local to house 8."""
    options = layout.get('north_entrance', {})
    return {'face_x': options.get('wall_x', -5.70),
            'y0': options.get('center_y', 9.80) - 2.10,
            'y1': options.get('center_y', 9.80) + 2.10,
            'z0': 0., 'z1': 4.78}


def occupied_footprints(layout):
    opening = north_wall_opening(layout)
    x, y0, y1 = opening['face_x'], opening['y0'], opening['y1']
    return {'numbered_red_wing': [7.12, .095, 11.60, 6.52],
            'lawn_white_terrace': [-3.50, 1.22, .004, 4.88],
            'north_faceted_porch': [x-1.09, y0, x+.24, y1],
            'north_door_opening': opening}


def faceted_porch(b, lod, layout):
    opening = north_wall_opening(layout)
    x, y0, y1 = opening['face_x'], opening['y0'], opening['y1']
    mid = (y0 + y1) / 2.
    # From high Y to low Y, the left-hand normal points inside the house.
    points = [(x, y1), (x-.94, mid+1.72), (x-.94, mid-1.17), (x, y0)]
    plan = Polygon(points)
    slab(b, plan, -.018, .075, TREAD, 'north porch threshold')
    slab(b, plan.buffer(.039, join_style=2), 2.685, 2.775,
         TRIM, 'north porch three-sided sill slab')
    slab(b, plan, 2.775, 2.805, DECK, 'north porch balcony floor')
    # The upper sash is on the gable plane, behind the projecting railing.
    rear = (x, y1), (x, y0)
    upper = box(1.69, 2.82, 2.815, 4.722)
    back_wall = box(0., 2.783, y1-y0, opening['z1']).difference(upper)
    wall(b, back_wall, *rear, 0., .118, CREAM, 'north gable balcony wall')
    sash = upper.buffer(-.070, join_style=2)
    wall(b, upper.difference(sash), *rear, .032, .100, METAL, 'north gable recessed sash')
    wall(b, sash, *rear, .114, .140, GLAZING, 'north gable upper window')

    for i, (a, c) in enumerate(zip(points, points[1:])):
        width = hypot(c[0]-a[0], c[1]-a[1])
        name = ('east bevel', 'front', 'west bevel')[i]
        center = width/2
        if i == 1:
            center += .09
            aperture = box(center-.937, .071, center+.937, 2.218)
            reveal = aperture.buffer(-.068, join_style=2)
            wall(b, aperture.difference(reveal), a,c,.034,.142,TIMBER,'north door surround')
            # One almost front-facing leaf and a second leaf turned into the
            # porch are visible together in the September 2023 photograph.
            leaf_width=.862
            for rank in range(2):
                hinge = center-.869 if rank == 0 else center+.869
                side = 1 if rank == 0 else -1
                angle = .02 if rank == 0 else .67
                left = (a[0]+.105,a[1]-hinge)
                end = (left[0]+leaf_width*sin(angle), left[1]-side*leaf_width*cos(angle))
                if rank:
                    left,end=end,left
                light=box(.061,.79,leaf_width-.058,2.082)
                leaf=box(0,.078,leaf_width,2.146)
                wall(b,leaf.difference(light),left,end,0,.041,TIMBER,'north wood door leaf '+str(rank+1))
                wall(b,light,left,end,.025,.041,GLAZING,'north glazed door leaf '+str(rank+1))
            b.box((x+.202,mid+.18,1.15),(.032,1.905,2.28),GLAZING,
                  label='8 | shaded recess behind open leaf')
            shade = Polygon([(x-.958,mid+1.48),(x-.958,mid-1.08),
                             (x-1.082,mid-1.08),(x-1.082,mid+1.48)])
            slab(b,shade,2.512,2.583,TRIM,'north porch blind case')
        else:
            aperture=box(center-.192,.38,center+.192,2.15)
            light=aperture.buffer(-.033,join_style=2)
            wall(b,aperture.difference(light),a,c,.074,.145,TIMBER,'north '+name+' sidelight frame')
            wall(b,light,a,c,.152,.165,GLAZING,'north '+name+' tall sidelight')
        wall(b,box(0,0,width,2.685).difference(aperture),a,c,0,.135,CREAM,'north porch '+name+' wall')
        # The rail fields really are open. The returns retain substantially
        # broader solid white ends where their short strips meet the wall.
        margins = (.29,.29) if i != 1 else (.145,.145)
        clear=box(margins[0],2.884,width-margins[1],3.706)
        surround=box(0,2.805,width,3.755).difference(clear)
        wall(b,surround,a,c,-.015,.097,CREAM,'north balcony '+name+' piers and rails')
        def along(distance):
            return (a[0]+(c[0]-a[0])*distance/width,a[1]+(c[1]-a[1])*distance/width)
        diamond_panel(b,lod,along(margins[0]),along(width-margins[1]),2.885,3.705,
                      .176,'north balcony '+name+' open diamonds')
        wall(b,box(0,3.755,width,3.803),a,c,-.053,.123,TRIM,'north balcony '+name+' coping')


def add_entrances(b, lod, layout):
    """Build the two low wings of the lawn front and the separate north door."""
    b.palette.update(PALETTE)
    numbered_wing(b,lod)
    terrace(b,lod)
    faceted_porch(b,lod,layout)
