"""No. 9. East lawn gable, long clay ridge, three south returns and two north returns."""
from shapely.geometry import Polygon, box
from hongji_roof_geometry import PEBBLE, STONE, PALETTE, height, roof_envelope, stack_box, strips_and_caps, triangular

DEFAULTS={'wall_width':7.27,'overhang':.51,'front_overhang':.76,'eave_z':5.53,'gable_rise':3.06,'ridge_depth':23.73}

def dimensions(layout):
    return {k:float(layout.get(k,v)) for k,v in DEFAULTS.items()}

def planes(layout):
    d=dimensions(layout);w=d['wall_width'];a=d['overhang'];depth=d['ridge_depth'];scale=depth/23.73
    e=d['eave_z'];crest=e+d['gable_rise']
    planes=triangular('east lawn gable','x',(-a,w/2,w+a),(-d['front_overhang'],depth),e,crest)
    # The three south gables in the independently photographed side elevation
    # have a different spacing to the pair on the north edge of the aerial.
    south=[(-3.480,2.303,2.715,5.591,7.422),
           (-3.034,10.791,2.898,5.956,7.934),
           (-3.233,18.525,3.730,5.794,7.871)]
    north=[(6.55,4.22,13.98)]
    for i,(outside,axis,half,side_eave,side_crest) in enumerate(south):
        u,c,v=[value*scale for value in (axis-half,axis,axis+half)]
        planes+=triangular(f'south return {i+1}','y',(u,c,v),(outside,w/2+.06),
                           e+(side_eave-5.53),crest+(side_crest-8.59))
    # A continuous lower tile slope is visible in the intervals between the
    # three street-facing rakes. It recedes behind their projecting grey tips.
    inner_edge=-2.36
    planes.append(('south connecting eave',box(inner_edge,0.,.08,depth),
                   (.40,0.,e-.46-.40*inner_edge)))
    for i,(axis,half,outside) in enumerate(north):
        u,c,v=[value*scale for value in (axis-half,axis,axis+half)]
        planes+=triangular(f'north return {i+1}','y',(u,c,v),(w/2-.06,w+(outside-7.45)),e-.13,crest-.39)
    # Two nested north gables: the narrow outer one and a higher gable
    # behind it. Their respective peaks are distinct in photograph 20.
    outer_x=w+(13.55-7.27); inner_x=w+(11.98-7.27)
    for label,x0,x1,y0,yc,y1,za,zc,zb,ridge_slope in [
        ('north inner gable',w/2-.06,inner_x,12.32,18.59,21.91,6.07,8.93,6.78,.055),
        ('north outer gable',inner_x-.75,outer_x,14.07,16.92,19.67,5.95,7.77,6.02,0.)]:
        for a,c,h,t in ((y0,yc,za,zc),(yc,y1,zc,zb)):
            sy=(t-h)/((c-a)*scale)
            planes.append((label,box(x0,a*scale,x1,c*scale),
                           (ridge_slope,sy,h+(e-5.53)-sy*a*scale-ridge_slope*x1)))
    # Above the north portico the red tiles start over the inset upper-window
    # wall. Keep the stone balcony in front of Y2.86 open. In the 2023 side
    # photograph the farther right shoulder is one course group lower.
    y0=2.86;z0=e-.035; pitch=.556
    foot=Polygon([(w-.03,y0),(12.66,y0),(12.66,6.13),
                  (11.07,6.13),(10.80,7.36),(w-.03,7.36)])
    planes.append(('stepped roof behind porch',foot,(0.,pitch,z0-pitch*y0)))
    return planes

def roof_sections(layout):
    """Visible tile faces as (label, XY polygon, (dz/dx,dz/dy,z_intercept)); thick 79 mm."""
    return roof_envelope(planes(layout))

def wall_head_at(x,y,layout):
    z=height(planes(layout),x,y)
    return None if z is None else z-.083

def rear_gable_infill(layout):
    """YZ wall between the small front roof and broad stepped-back north gable."""
    from shapely.ops import unary_union
    facets=planes(layout)
    d=dimensions(layout);scale=d['ridge_depth']/23.73
    x=d['wall_width']+(11.58-7.27)
    zs=lambda p,y:p[0]*x+p[1]*y+p[2]-.079
    strips=[]
    small=[p for p in facets if p[0]=='north outer gable']
    large=[p for p in facets if p[0]=='north inner gable']
    for _,sp,sd in small:
        for _,lp,ld in large:
            a=max(14.96*scale,sp.bounds[1],lp.bounds[1])
            c=min(19.04*scale,sp.bounds[3],lp.bounds[3])
            if c>a:
                strips.append(Polygon([(a,zs(sd,a)),(c,zs(sd,c)),(c,zs(ld,c)),(a,zs(ld,a))]))
    return unary_union(strips)


def add_roof(b,lod,layout):
    for name,values in PALETTE.items():b.palette.setdefault(name,values)
    from garden_shells import footprint
    strips_and_caps(b,roof_sections(layout),9,lod,footprint(9,dimensions(layout)))
    d=dimensions(layout);peak=d['eave_z']+d['gable_rise'];span=d['wall_width']
    # The front flue rises behind the lawn gable. Its unusually broad, thin cap
    # and the narrow edging on the cap are visible in both named photographs.
    x=float(layout.get('chimney_x',span*2.5126/7.27));y=float(layout.get('chimney_y',.006));ctr=(x,y)
    floor=height(planes(layout),x,y)-.72
    stack_box(b,ctr,(1.17,.60),floor,peak+.17,PEBBLE,'9 | roughcast chimney breast')
    stack_box(b,ctr,(1.331,.74),peak+.16,peak+.435,STONE,'9 | squared chimney cap')
    for i in (-1,1):
        for xx in (-.636,.636):
            b.tube([(x+xx,y+i*.345,peak+.437),(x+xx,y+i*.345,peak+.513)],.013,PEBBLE,6,'9 | cap edge upright')
        b.tube([(x-.636,y+i*.345,peak+.513),(x+.636,y+i*.345,peak+.513)],.013,PEBBLE,6,'9 | cap long edge')
        b.tube([(x+i*.636,y-.345,peak+.513),(x+i*.636,y+.345,peak+.513)],.013,PEBBLE,6,'9 | cap short edge')
