"""Measured portal, continuous open lane and first attached street range."""
from math import cos, pi, sin
from pathlib import Path
import numpy as np
from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from sign_lettering import lettering_shapes
from gatehouse_finishes import (BOARD, BRICK, BRONZE, CLAY, CREAM, CREST, GLASS, OCHRE,
                               SHADE, SHEET, STONE, STREET, WEST, WOOD)
from exterior_sashes import opening_faces, opening_profiles
import east_balconies
from hengchang_roof import roof_dimensions

FONT = Path(__file__).with_name('entrance-name.otf')


def south(b, poly, front, thickness, material, name):
    b.prism(poly,-front-thickness,-front,lambda x,z,d:(x,-d,z),material,name)


def block(b,x0,x1,y0,y1,z0,z1,mat,name):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=name)


def archival_name(b, layout):
    H=np.asarray(layout['native_to_xz']['tower'])
    def traced(points):
        uv=np.asarray(points)*[5312/1100,2988/619]
        q=np.column_stack([uv,np.ones(len(uv))])@H.T
        return Polygon(q[:,:2]/q[:,2,None])
    outer=traced([(108,293),(222,295),(221,328),(108,327)])
    inner=outer.buffer(-.090,join_style=2)
    south(b,outer.difference(inner),-.115,.11,CREST,'2018 portal | raised border of the name tablet')
    south(b,inner,-.052,.054,BOARD,'2018 portal | recessed ochre name tablet')
    x,z=inner.centroid.coords[0]
    for char,shape in lettering_shapes('里昌亨',inner.bounds[2]-inner.bounds[0]-.26,.35,font=FONT):
        south(b,affinity.translate(shape,x,z),-.079,.027,BRONZE,'2018 portal | name '+char)
    for bottom,top,depth,mat in [(5.83,5.90,.14,STONE),(5.90,6.00,.19,CREAM)]:
        block(b,-.055,6.38,-depth,.11,bottom,top,mat,'2018 portal | lower ledge')


def west_return(b,layout,d,old,lod):
    # Profile of the wall under the rear cover, intermediate pitched roof and
    # street tower. No rear northern entrance building survives at Changning Road.
    end=layout['tower_depth']
    upper=[(0,11.915),(d['cap_back_y'],11.915),(d['cap_back_y'],d['upper_eave_z']+.04),
           (d['ridge_y'],d['ridge_z']-.03),(d['rear_cover_y0'],d['rear_cover_z']-.04),
           (end,d['rear_cover_z']+.03)]
    outer=Polygon([(0,0),(end,0),*reversed(upper)])
    # The single western return window is visible across the shop at 1386
    # and at the upper left edge of the 2025 municipal doorway photograph.
    center,width,base,spring=4.94,1.03,5.64,7.04
    radius=width*.5
    arc=[(center+radius*cos(a),spring+radius*sin(a)) for a in np.linspace(0,pi,12 if lod else 31)]
    opening=Polygon([(center-radius,base),(center+radius,base),*arc])
    def side(poly,lo,hi,mat,name):
        b.prism(poly,lo,hi,lambda y,z,x:(x,y,z),mat,name)
    side(outer.difference(opening),0,.26,OCHRE if old else WEST,'Tower | west return with side window')
    rim=opening.buffer(.055,join_style=2).difference(opening)
    side(rim,-.040,.016,CREAM,'Tower | side window surround')
    light=opening.buffer(-.05,join_style=2)
    side(opening.difference(light),.043,.097,WOOD,'Tower | side sash frame')
    side(light,.097,.113,GLASS,'Tower | side sash glass')
    side(light.intersection(box(center-.019,base,center+.019,spring+.49)),.052,.097,WOOD,'Tower | central side mullion')
    side(light.intersection(box(center-radius,spring-.025,center+radius,spring+.025)),.052,.097,WOOD,'Tower | side transom')
    block(b,-.34,.08,center-.71,center+.71,spring+.61,spring+.665,SHEET,'Tower | west sheet-metal window hood')
    block(b,-.34,-.31,center-.71,center+.71,spring+.53,spring+.61,SHEET,'Tower | west metal hood drip')
    # An outdoor air-conditioning unit under the west window appears in 2021 and 2025.
    block(b,-.34,-.04,center-.53,center+.39,base-.55,base-.035,CREAM,'West return | air conditioner chassis')
    for z in np.linspace(base-.48,base-.11,6 if lod else 13):
        block(b,-.365,-.34,center-.47,center+.33,z,z+.013,STONE,'West return | recessed condenser grille')
    if not old:
        # The west panel is oblique in the 2025 photograph. Its outline
        # survives the view, but the fine pictorial carving is unresolved.
        panel=Polygon([(1.28,.70),(3.93,.70),(3.93,3.28),(3.63,3.39),(3.22,3.44),
                       (2.65,3.42),(1.85,3.28),(1.28,3.03)])
        side(panel.difference(panel.buffer(-.052,join_style=2)),-.061,-.009,BRONZE,'West return | relief panel border')
        side(panel.buffer(-.052,join_style=2),-.034,-.005,STONE,'West return | relief field')
    # The street wing shares this boundary west of its southern eaves.
    side(outer,layout['portal']['width']-.25,layout['portal']['width'],SHADE,'Tower | east party wall')


def wing_end(b,layout,d):
    start,end=layout['front_y']['east'],d['rear_y']
    profile=Polygon([(start,0),(end,0),(end,d['rear_eave_z']-.04),
                     (d['ridge_y'],d['ridge_z']-.05),(d['shoulder_y'],d['upper_eave_z']-.05),
                     (d['shoulder_y'],d['shoulder_z']-.05),(start,d['low_eave_z']-.04)])
    x=layout['east_end']
    b.prism(profile,x-.23,x,lambda y,z,s:(s,y,z),WEST,'Street wing | eastern section wall')
    block(b,layout['portal']['width'],x-.23,end-.22,end,0,d['rear_eave_z']-.03,WEST,'Street wing | courtyard enclosure')


def add_envelope(b,lod,layout,shops):
    archived=str(layout['period']).startswith('2018')
    p=layout['portal'];g=p['width'];d=roof_dimensions(layout)
    profiles=opening_profiles(layout);faces=opening_faces(layout)
    holes=[poly for name,poly in profiles.items() if faces[name]=='east']
    tower_outline=Polygon([(0,0),(g,0),(g,12.145),(0,11.89)])
    tower_holes=unary_union([box(p['left'],-.5,p['right'],p['head']),profiles['tower']])
    wall=tower_outline.difference(tower_holes)
    if archived:
        south(b,wall,0,.31,OCHRE,'2018 portal | plaster front, open lane and arched window')
        archival_name(b,layout)
    else:
        sill=profiles['tower'].bounds[1]-.045
        lower=wall.intersection(box(-1,-1,g+1,sill))
        south(b,lower,0,.31,BRICK,'Portal | grey masonry framing the open lane')
        south(b,wall.difference(lower),0,.31,WEST,'Portal | rendered upper wall and sash reveal')
        for lo,hi,mat,depth in [(0,.17,STONE,.075),(.48,.59,CLAY,.022),(1.99,2.11,CLAY,.018),(3.73,3.84,CLAY,.018)]:
            course=box(0,lo,g,hi).intersection(lower)
            south(b,course,-depth,depth,mat,'Portal | pier plinth' if lo==0 else 'Portal | contrasting brick course')
    for h,projection,height in [(0,.145,.09),(.09,.235,.14),(.23,.27,.066)]:
        poly=Polygon([(-.055,11.65+h),(g+.055,11.90+h),(g+.055,11.90+h+height),(-.055,11.65+h+height)])
        south(b,poly,-projection,projection+.105,CREAM,'Tower | projecting eave above main window')
    east=layout['front_y']['east'];end=layout['east_end']
    front=box(g,0,end,d['low_eave_z']-.06)
    south(b,front.difference(unary_union(holes+list(shops.values())+list(east_balconies.openings().values()))),east,.31,OCHRE,'Street wing | continuously perforated street wall')
    west_return(b,layout,d,archived,lod)
    wing_end(b,layout,d)
    rear=layout['tower_depth']
    # Rear boundary retains the lane opening for foot traffic in both states.
    rear_wall=box(0,0,g,d['rear_cover_z']+.02).difference(box(p['left'],-.1,p['right'],3.53))
    south(b,rear_wall,rear-.23,.23,WEST,'Tower | northern opening in rear envelope')
    block(b,g,end,east,east+layout['wing_depth'],-.09,0,SHADE,'Street wing | foundation')
    # An inset edge sets the curb apart from the building. Nothing covers
    # the continuous clear area above the lane pavement.
    block(b,-.10,end+.10,-1.52,-.02,-.10,-.005,STREET,'Street | pavement in front of entrance')
    block(b,-.10,end+.10,-1.65,-1.52,-.17,-.008,STONE,'Street | stone curb')
