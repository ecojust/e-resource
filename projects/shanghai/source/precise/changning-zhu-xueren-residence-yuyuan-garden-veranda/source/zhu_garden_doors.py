"""Door recesses at the rear of the garden gallery and its two open ends."""
from math import cos,pi,sin
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from zhu_garden_materials import GLASS,MASONRY,PLASTER,REVEAL,STONE,STONE_EDGE,WOOD
from zhu_garden_veranda import garden_face


def door_set(b,opening,plane,label):
    left,bottom,right,top=opening.bounds
    jamb=.060
    interior=box(left+jamb,bottom+jamb,right-jamb,top-jamb)
    mid=(left+right)/2
    transom=top-(top-bottom)*.205
    frame=unary_union([opening.difference(interior),
                       box(mid-.022,bottom,mid+.022,top),
                       box(left,transom-.027,right,transom+.027),
                       box(left,bottom,right,bottom+.11)])
    garden_face(b,frame,plane,-.155,-.074,WOOD,label+' | timber')
    garden_face(b,opening.difference(frame),plane,-.168,-.153,GLASS,label+' | glazing')
    casing=opening.buffer(.075,join_style=2).difference(opening)
    garden_face(b,casing,plane,-.010,.017,STONE,label+' | surrounds')


def add_gallery_back(b,layout):
    plane=layout['rear_gallery_wall_y']
    width=layout['east_x']
    upper=layout['balcony_z']+.025
    rows=[(layout['landing_z'],layout['gallery_soffit_z'],layout['garden_ground_doors']),
          (upper,layout['upper_soffit_z']+.13,layout['garden_upper_doors'])]
    for level,(bottom,top,doors) in enumerate(rows,1):
        openings=[]
        for index,(x0,x1,z0,z1) in enumerate(doors,1):
            hole=box(x0,z0,x1,z1)
            openings.append(hole)
            door_set(b,hole,plane,'Gallery '+str(level)+' | opening '+str(index))
        span=box(0,bottom-.12,width,top)
        garden_face(b,span.difference(unary_union(openings)),plane,-.32,0,PLASTER,
                    'Gallery rear | storey '+str(level))
        skirt=box(0,bottom,width,bottom+.12).difference(unary_union(openings))
        garden_face(b,skirt,plane,-.01,.019,STONE_EDGE,'Gallery rear | low skirting')
    for x0,x1 in [(0,layout['bay_edges'][1]),(layout['bay_edges'][2],width)]:
        b.plan_prism(box(x0,0,x1,plane),layout['gallery_soffit_z']-.030,layout['gallery_soffit_z'],
                     PLASTER,'Gallery ceiling | side bays')


def end_arch(b,layout,east,lod):
    name='East' if east else 'West'
    x=layout['east_x']if east else 0.
    depth=layout['veranda_depth']
    bottom=layout['landing_z']
    top=layout['gallery_soffit_z']
    sign=1 if east else -1
    reach=depth+.10
    u0,u1=(0,reach)if east else(-reach,0)
    def mapped(u,z,d):
        return x+sign*d,sign*u,z
    lo,hi=(.40*depth,.965*depth)if east else(-.965*depth,-.40*depth)
    mid=(lo+hi)/2
    shoulder=bottom+2.14
    pts=[(lo,bottom-.01),(hi,bottom-.01),(hi,shoulder)]
    segments=14 if lod else 32
    # The camera looks into the east return in photo 11. The top is a broad,
    # shallow arch with a pronounced vertical reveal above the four balusters.
    for i in range(1,segments):
        a=pi*i/segments
        pts.append((mid+(hi-lo)*.5*cos(a),shoulder+.49*sin(a)))
    pts.append((lo,shoulder))
    hole=Polygon(pts)
    wall=box(u0,0,u1,top).difference(hole)
    b.prism(wall,-layout['south_wall_thickness'],0,mapped,MASONRY,name+' end | gallery arch')
    reveal=hole.buffer(.071,join_style=2).difference(hole).intersection(box(u0,bottom+.08,u1,top))
    b.prism(reveal,-.023,.025,mapped,REVEAL,name+' end | arch margin')
    if east:
        for v0,v1 in [(lo,.526*depth),(.852*depth,hi)]:
            b.prism(box(v0,bottom,v1,1.42),-.22,-.015,mapped,MASONRY,'East end | balustrade solid ends')
            b.prism(box(v0-.018,1.411,v1+.018,1.477),-.245,.004,mapped,STONE,'East end | return sill caps')
    upper=box(u0,layout['balcony_z'],u1,layout['upper_soffit_z'])
    upper_hole=box(lo,layout['balcony_z']-.01,hi,layout['upper_soffit_z']+.02)
    b.prism(upper.difference(upper_hole),-.37,0,mapped,MASONRY,name+' end | upper piers')
    b.box((x,reach*.5,layout['balcony_z']-.10),(.19,reach,.16),STONE_EDGE,
          label=name+' end | floor band')


def add_approach_and_envelope(b,layout,lod):
    width=layout['east_x'];back=layout['rear_y'];end=layout['veranda_depth']
    b.plan_prism(box(.04,0,width-.04,back-.02),-.07,.003,STONE,'Base | main house')
    b.box((.13,(end+back)/2,layout['upper_soffit_z']/2),(.26,back-end,layout['upper_soffit_z']),
          PLASTER,label='West | simplified garden return')
    b.box((width*.5,back-.14,layout['upper_soffit_z']/2),(width,.28,layout['upper_soffit_z']),
          PLASTER,label='North | main roof enclosure')
    for is_east in [False,True]:
        end_arch(b,layout,is_east,lod)
    for x0,x1 in [(1.1,1.836),(4.999,5.64),(13.04,13.559),(16.507,17.77)]:
        front=0.
        b.box(((x0+x1)/2,front+.16,(.70+1.42)/2),(x1-x0,.22,.72),
              MASONRY,label='Lower side bays | solid railing ends')
        b.box(((x0+x1)/2,front+.16,1.427),(x1-x0+.025,.27,.064),
              STONE,label='Lower side bays | sill returns')


def add_eastern_section(b,layout):
    """A cut through the undated rear extension, immediately behind its measured skin.

    The red main roof has its own traced northern eave. A short recessed grey
    closure supports the observed east dormer and ends inside the rounded wall.
    Its plane represents the limit of this reconstruction.
    """
    import json
    from pathlib import Path
    from zhu_garden_materials import GROOVE,STONE_EDGE
    from zhu_residence_roof import east_apron_z,roof_features
    data=json.loads((Path(__file__).resolve().parents[1]/'measurements/east-entrance-surface-and-openings.json').read_bytes())
    frame=data['world'];axis=frame['axis_spacing_m']
    def world(u,v):
        return (frame['column_X']-axis*v,frame['southern_column_Y']+axis*u)
    path=[]
    for name in ('door-recess','round-return'):
        for point in data['surface_paths'][name]:
            xy=world(*point)
            if not path or xy!=path[-1]:path.append(xy)
    inner_x=16.43
    inside=[(x-.23,y)for x,y in path]
    northern_y=inside[-1][1]
    section=Polygon([*inside,(inner_x,northern_y-.38),(inner_x,inside[0][1])])
    top=layout['south_eave_z']-.34
    # The setback keeps the photographed perforated exterior, sills and cornices
    # in front of this section. It is not an estimate of the whole north wing.
    b.plan_prism(section,.01,top,GROOVE,'East extension | recessed section')
    b.plan_prism(section,top,top+.035,STONE_EDGE,'East extension | upper cut surface')
    _,_,dormers=roof_features(layout)
    observed=next(row for row in dormers if row['side']=='east')
    local=observed['loc']
    def under(u,v):
        return local(u,v,east_apron_z(observed['base'],v)-.09)
    lower=[under(-1.48,-1.08),under(1.64,-1.08),under(1.64,1.20),under(-1.48,1.20)]
    vert=[*( (x,y,top+.025) for x,y,z in lower),*lower]
    faces=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    if Polygon([(v[0],v[1])for v in lower]).exterior.is_ccw is False:
        faces=[tuple(reversed(f))for f in faces]
    b.add(vert,faces,STONE_EDGE,'East dormer | local backing to cut surface')
