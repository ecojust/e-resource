"""Two nine-bay balcony fronts on building 3, Sichuan North Road 975–987.

Ornament centre lines are transcribed from the 2018 photograph. Distances
in the rectified ornament drawing run right and down from the top left.
"""
from functools import lru_cache
import math

from shapely import set_precision
from shapely.affinity import affine_transform
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from gongyi_materials import STONE, TRIM, paint

IRON = 'Balcony | blackened wrought iron'
SLAB = 'Balcony | mineral deck and nosing'
PALETTE = {
    IRON: paint((52, 52, 47), .72, .28),
    SLAB: paint((163, 154, 135), .94),
    STONE: paint((161, 151, 132), .93),
    TRIM: paint((196, 184, 158), .86),
}


@lru_cache(maxsize=2)
def rail_drawing(lod):
    """Fused flat iron with open cells. The drawing is 670 by 176 units."""
    strokes = []
    def line(points, width=2.6):
        strokes.append(LineString(points).buffer(width / 2, cap_style=3, join_style=2))
    def arc(x, y, rx, ry, start, stop, steps, width=2.6):
        angles = [start + (stop-start)*i/steps for i in range(steps+1)]
        line([(x+rx*math.cos(t), y+ry*math.sin(t)) for t in angles], width)
    def fold(x, y, sx, sy, size):
        # Four folded square ends, joined to the two long straps of the panel.
        path = [(0,0),(size,0),(size,size),(size*.27,size)]
        if not lod:
            path.append((size*.27,size*.34))
        line([(x+sx*a,y+sy*b) for a,b in path])

    for y, width in [(2,3.6),(21,3.2),(153,3.6),(174,3.6)]:
        line([(1.8,y),(668.2,y)], width)
    for x in [3,28,83,101,117,132,148,163,180,195,211,
              259,287,391,411,468,483,498,513,529,545,560,576,593,642,667]:
        line([(x,22),(x,153)], 2.25)
    # The intermediate panels occur twice on either side of the six-spoke centre.
    for x in (56,235,436,617):
        for v in (1,-1):
            y = 39 if v==1 else 135
            line([(x-17,y+v*16),(x-17,y),(x+17,y),(x+17,y+v*16)])
            fold(x-16,y+v*12,1,v,9)
            fold(x+16,y+v*12,-1,v,9)
        for dx in (-9,9):
            line([(x+dx,48),(x+dx,125)], 2.35)
    # Inverted U ends at the outer edges of each shallow upright panel.
    for x in (16,272,402,654):
        arc(x,66,10,20,math.pi,math.tau,5 if lod else 9)
        for dx in (-10,10):
            line([(x+dx,66),(x+dx,151)],2.25)
    for x in (56,235,436,617):
        line([(x,21),(x,26)],2.3)
        line([(x,149),(x,154)],2.3)
        for y in (31,144):
            arc(x,y,4.3,6.8,0,math.tau,4 if lod else 14,2.0)
    for x in (109,190,338,488,568):
        for y in (10,164):
            arc(x,y,6.4,9,0,math.tau,5 if lod else 14,2.1)
    for x in (325,352):
        rise=27.4*math.sqrt(1-((x-339)/20.3)**2)
        line([(x,21),(x,88-rise)],2.75)
        line([(x,88+rise),(x,152)],2.75)
    # The centre stays open between its six spokes. The bounding vertical
    # straps stop on the hoop, while the horizontal tie continues past it.
    for x in (308,370):
        line([(x,59),(x,116)],2.45)
    line([(308,88),(370,88)],2.6)
    for x in (293,384):
        for y in (54,121):
            arc(x,y,4.1,5.9,0,math.tau,5 if lod else 12,2.15)
            line([(x-7,y),(x-3.8,y)],2.1)
            line([(x+3.8,y),(x+8,y)],2.1)
    for sx in (-1,1):
        for sy in (-1,1):
            y = 40 if sy==1 else 137
            line([(339,y),(339+sx*38,y),(339+sx*38,y+sy*23)])
            fold(339+sx*38,y+sy*21,-sx,-sy,9)
    ring_centre = (339,88)
    arc(*ring_centre,20.3,27.4,0,math.tau,16 if lod else 30,3.2)
    for i in range(6):
        a=i*math.pi/3
        line([ring_centre,(339+20.3*math.cos(a),88+27.4*math.sin(a))],2.65)
    # Keep line ends on the cill/handrail planes. Snapping removes sub-pixel
    # slivers where separate parts of a real iron pattern meet.
    outline=set_precision(unary_union(strokes), .08).simplify(.46 if lod else .09)
    return affine_transform(outline, (1.,0.,0.,-1.,0.,176.))


def _front_prism(b, poly, back, front, material, label):
    b.prism(poly, back, front, lambda x,z,d:(x,-d,z), material, label)


def _corbels(b, axis, width, depth, floor, lod, label):
    """Two consoles with a clear slot. Y–Z is the traced side profile."""
    reach=depth-.035
    bottom=floor-.19
    drop=min(.82, reach*.87)
    p=[(.025,bottom),(-reach,bottom),(-reach,bottom-.09)]
    steps=5 if lod else 11
    # The curved underside is nearly level at the rail end, then turns steeply
    # down against the masonry. The square neck is visible in the Commons view.
    for i in range(1,steps+1):
        a=i*math.pi/(2*steps)
        outward=.06+(reach-.06)*(1-math.sin(a))
        z=bottom-.09-(drop-.09)*(1-math.cos(a))
        p.append((-outward,z))
    p.extend([(.025,bottom-drop)])
    console=Polygon(p)
    for sign in (-1,1):
        x=axis+sign*width*.249
        half=width*.138
        b.prism(console,x-half,x+half,lambda y,z,along:(along,y,z),
                STONE,label+(' south console' if sign<0 else ' north console'))


def _pier(b, x, width, front, z, height, lod, name):
    def block(w,y0,y1,z0,z1,material,part):
        b.box((x,-(y0+y1)/2,(z0+z1)/2),(w,y1-y0,z1-z0),material,label=name+' '+part)
    back=front-width*.76
    block(width,back,front,z-.006,z+height*.887,STONE,'body')
    block(width*1.105,back-.014,front+.020,z+height*.887,z+height*.936,TRIM,'neck cap')
    block(width*1.22,back-.033,front+.043,z+height*.936,z+height,TRIM,'overhanging cap')
    # On the photographed pier the rectangular recessed field is framed by
    # shallow raised strips. Three scalloped drops descend below its crown.
    field_low=z+.11*height
    field_top=z+.85*height
    for sign in (-1,1):
        dx=sign*width*.35
        b.box((x+dx,-front-.009,(field_low+field_top)*.5),
              (width*.064,.019,field_top-field_low),TRIM,label=name+' field side '+str(sign))
    b.box((x,-front-.009,field_top),(width*.75,.019,.034),TRIM,label=name+' field head')
    for row in range(3):
        r=width*(.162-row*.020)
        rz=height*(.052-row*.006)
        y=z+height*(.825-row*.049)
        samples=6 if lod else 12
        arc=[(x+r*math.cos(i*math.pi/samples),y-rz*math.sin(i*math.pi/samples))
             for i in range(samples+1)]
        face=LineString(arc).buffer(.012 if row==0 else .010,cap_style=2,join_style=2)
        _front_prism(b,face,front+.001,front+.024,TRIM,name+' scallop '+str(row+1))


def add_balconies(b,lod,layout):
    edges=layout['bay_edges']
    if len(edges)!=10 or len(layout['balcony_z'])!=2:
        raise ValueError('Building 3 has ten pier axes at each of its two balcony levels')
    spans=[r-l for l,r in zip(edges,edges[1:])]
    if min(spans)<=0:
        raise ValueError('Pier axes must increase from south to north')
    span=sorted(spans)[4]
    body=span*.097
    depth=layout['balcony_depth']
    h=span*.235
    # Each floor has one continuous deck. Its stepped outside face carries
    # the ten piers. The two underside consoles meet the back of each pier.
    for level,z in enumerate(layout['balcony_z'],2):
        tag=f'Balcony {level}'
        lo,hi=edges[0]-body*.5,edges[-1]+body*.5
        for bottom,top,extent,mat,part in [
                (z-.195,z-.046,depth,SLAB,'deck'),
                (z-.046,z,depth+.026,TRIM,'nosing')]:
            b.box(((lo+hi)*.5,-extent*.5,(bottom+top)*.5),
                  (hi-lo,extent,top-bottom),mat,label=tag+' '+part)
        for index,x in enumerate(edges,1):
            name=f'{tag} pier {index:02}'
            _pier(b,x,body,depth+.028,z,h,lod,name)
            _corbels(b,x,body,depth,z,lod,name)
        for index,(a,c) in enumerate(zip(edges,edges[1:]),1):
            left=a+body/2
            right=c-body/2
            rail_back=depth-body*.43
            low=z+h*.033
            high=z+h*.858
            def place(u,v,d):
                return left+u*(right-left)/670,-d,low+v*(high-low)/176
            name=f'{tag} bay {index:02}'
            b.prism(rail_drawing(bool(lod)),rail_back,rail_back+.021,place,IRON,name+' open iron')
            b.box((.5*(a+c),-rail_back-.012,high+.031),
                  (right-left,body*.405,.062),TRIM,label=name+' handrail')
