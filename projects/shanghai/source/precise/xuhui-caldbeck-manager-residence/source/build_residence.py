"""Reconstruct the photographed garden and Wukang Road elevations of the 1928 residence."""
import json
import math
import sys
from pathlib import Path

import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import LineString, Polygon, box
from shapely.ops import split, unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
from package_architectural_model import build
from photo_architecture import Facade

P = json.loads((HERE / 'parameters.json').read_bytes())
RING = np.array(P['source_local_outline_m'])
MODEL = P['id']
COLORS = {
    'ivory roughcast': (.814, .786, .69), 'garden brick': (.46, .251, .173),
    'shaded brick': (.33, .169, .136), 'brick sill': (.571, .357, .247),
    'oxidized Tudor timber': (.337, .176, .138), 'vermilion window joinery': (.418, .217, .168),
    'shaded window': (.221, .302, .319), 'light window': (.344, .407, .395),
    'recessed door wood': (.236, .179, .142), 'worn stone': (.587, .55, .476),
    'terracotta tile bed': (.477, .214, .131), 'baked tile': (.578, .279, .168),
    'tile ridge': (.52, .242, .145), 'charcoal flue': (.157, .137, .119),
    'balcony wood': (.280, .20, .145), 'reddish clay panels': (.498, .24, .153),
}
PALETTE = {name: {'color': list(value), 'roughness': .38 if 'window' in name else .78}
           for name, value in COLORS.items()}
META = {
    'id': MODEL, 'name': '武康路99号正广和大班住宅', 'status': 'photo-informed-exterior',
    'viewer_page': 'caldbeck-manager-residence.html', 'audit_directory': 'data/audit/caldbeck-manager-residence-v1/',
    'scope': 'Principal L-shaped house, south garden porch and terrace, west-facing balcony, timber gables, attic dormers and grouped brick chimneys. Other houses, interiors and the street enclosure are outside this model.',
    'model_scope_zh': '正广和大班住宅临武康路的西侧阳台、南园露木山墙、砖柱敞廊、透花砖栏、陡坡红瓦屋面、两处老虎窗和砖烟囱。北、东墙按单栋足印简化。街门门牌作为地址证据，院界、附属用房及室内分列。',
    'coordinate_convention': 'Local X follows the garden elevation east-northeast, glTF Y is up and +Z faces south-southeast.',
    'map_reference_license': 'OpenStreetMap and Overture Maps, ODbL-1.0. Model dimensions from the registered footprint, municipal material and photo proportions.',
    'interiors_modeled': False,
}
EAVE = P['estimated_south_eaves_m']
RIDGE = P['estimated_main_ridge_m']
YRIDGE = .65
WEST_AXIS = -6.03
WEST_CROWN = 10.87
OUTLINE = Polygon(RING)
# Long ridge follows the street block. A transverse roof covers the projecting southwest wing.
def main_height(x, y):
    return RIDGE - .851 * abs(y - YRIDGE)


def wing_height(x, y):
    return WEST_CROWN - 1.004 * abs(x - WEST_AXIS)


def roof_at(x, y):
    if y < YRIDGE:
        return max(main_height(x, y), wing_height(x, y))
    return main_height(x, y)


def roof_cells():
    roof = OUTLINE.buffer(.285, join_style=2)
    # Split the whole footprint with throughgoing lines. Clipping lines to the roof
    # first leaves some endpoints microscopically inside the boundary, allowing
    # a triangulated face to span both sides of a ridge or valley.
    lines = [LineString([(x, -40), (x, 40)]) for x in (-2.26, WEST_AXIS)]
    lines.extend(LineString([(-40, y), (40, y)]) for y in (2., YRIDGE))
    for sign_x in (-1, 1):
        for sign_y in (-1, 1):
            def line_y(x):
                return YRIDGE+(RIDGE-WEST_CROWN+1.004*sign_x*(x-WEST_AXIS))/(.851*sign_y)
            lines.append(LineString([(-40, line_y(-40)), (40, line_y(40))]))
    cells = [roof]
    for line in lines:
        cells = [part for cell in cells for part in split(cell, line).geoms if part.area > 1e-7]
    assert abs(sum(c.area for c in cells)-roof.area) < 1e-5
    for cell in cells:
        for triangle in constrained_delaunay_triangles(cell).geoms:
            corners=list(triangle.exterior.coords)[:-1]
            center=triangle.centroid
            assert abs(sum(roof_at(x,y) for x,y in corners)/3-roof_at(center.x,center.y))<.001
    return cells


def section_height(t, face):
    return roof_at(*face.point(t, 0)[:2])


def wall_outline(face, cells):
    length = face.length
    edge = LineString([face.a[:2], face.b[:2]])
    us = {-length/2, length/2}
    for cell in cells:
        crossed = edge.intersection(cell.boundary)
        for part in getattr(crossed, 'geoms', [crossed]):
            if not part.is_empty and part.geom_type in ('Point', 'LineString'):
                for coord in part.coords:
                    u = float(np.dot(np.asarray(coord)-face.center[:2], face.t[:2]))
                    us.add(float(np.clip(u, -length/2, length/2)))
    upper = [(u, section_height(u, face)) for u in sorted(us, reverse=True)]
    return Polygon([(-length/2, .12), (length/2, .12), *upper]).buffer(0)


def band_segment(a, b, width):
    return LineString([a, b]).buffer(width/2, cap_style='flat', join_style='mitre')


def apply_plaster_wall(face, contour, holes, timbers):
    wall = face.wall(.12, RIDGE, holes, .19, 'ivory roughcast', contour)
    if timbers:
        raised = unary_union(timbers).intersection(wall)
        face.prism(raised, .003, .078, 'oxidized Tudor timber', 'planted timber boards')
    return wall


def window(face, u, low, high, width, lights, lod, label, exterior=True):
    shape = box(u-width/2, low, u+width/2, high)
    face.prism(shape, -.235, -.211, 'shaded window' if lights>=3 else 'light window', label+' glazing')
    inner = shape.buffer(-.067, join_style=2)
    vertical = []
    for step in range(1, lights):
        x = u+width*(step/lights-.5)
        vertical.append(box(x-.035, low, x+.035, high))
    cross = low+(high-low)*.69
    vertical.append(box(u-width/2, cross-.021, u+width/2, cross+.021))
    if not lod and width/lights>.54:
        for i in range(lights):
            x=u+width*((i+.5)/lights-.5)
            vertical.append(box(x-.013,low,x+.013,high))
    face.prism(shape.difference(inner.difference(unary_union(vertical))), -.16, -.09, 'vermilion window joinery', label+' casements')
    if exterior:
        face.box(u, low-.055, width+.17, .11, .245, .025, 'brick sill', label+' stone sill')
    return shape


def studs(bounds, coordinates, low, high):
    return [box(x-.071,low,x+.071,high) for x in coordinates if bounds[0]<x<bounds[1]]


def quoin(face, u, z0, z1, lod, label):
    count = max(1, int((z1-z0)/.20))
    for i in range(count):
        h=(z1-z0)/count; size=.20 if i%2 else .37
        direction=1 if u<0 else -1
        face.box(u+direction*size/2,z0+(i+.5)*h,size,h-.010,.062,.034,'garden brick' if i%3 else 'brick sill',label)


def plinth(face, lo, hi):
    face.box((lo+hi)/2,.365,hi-lo,.50,.135,.01,'garden brick','low brick base')
    face.box((lo+hi)/2,.626,hi-lo,.06,.157,.026,'brick sill','plinth capping')


def west_garden_gable(builder, cells, lod):
    face=Facade(builder,RING[5],RING[4],'South garden projecting wing')
    g=wall_outline(face,cells);h=face.length/2
    rows=[(0,1.02,2.77,3.40,4),(0,4.09,5.99,3.57,4),(0,7.24,8.67,2.67,3)]
    holes=[window(face,*row,lod,f'Garden gable level {i+1}')for i,row in enumerate(rows)]
    trim=[box(-h,3.18,h,3.39),box(-h,6.49,h,6.69),box(-h,8.75,h,8.92)]
    trim+=studs((-h,h),[-h+.09,-2.47,-1.93,-.67,.68,1.93,2.49,h-.1],3.28,10.96)
    trim.extend([band_segment((-h+.1,6.61),(-1.88,4.98),.17),band_segment((h-.1,6.61),(1.88,4.98),.17),
                 band_segment((-2.95,7.06),(-1.42,8.76),.14),band_segment((2.95,7.06),(1.42,8.76),.14),
                 band_segment((-1.55,8.84),(0,10.55),.14),band_segment((1.55,8.84),(0,10.55),.14)])
    apply_plaster_wall(face,g,holes,trim);plinth(face,-h,h)
    for edge in (-h+.02,h-.02):quoin(face,edge,.65,3.21,lod,'brick quoins')
    for u in np.linspace(-1.85,1.85,19 if not lod else 11):
        face.box(u,6.424,.098,.13,.114,.057,'oxidized Tudor timber','individually cut dentil')
    return face


def west_street_face(builder,cells,lod):
    # Wukang Road photographs show a broad plaster gable with two balcony openings.
    face=Facade(builder,RING[0],RING[5],'West Wukang Road balcony')
    half=face.length/2; contour=wall_outline(face,cells)
    rows=[(-1.28,3.64,5.67,1.30,2),(1.43,3.68,5.60,1.40,2)]
    windows=[window(face,*row,lod,'West balcony opening '+str(i+1))for i,row in enumerate(rows)]
    upper_u=-1.03
    windows.append(window(face,upper_u,7.32,8.43,1.30,2,lod,'attic west gable window'))
    trim=[box(-half,6.89,half,7.05),box(-half+.05,3.27,-half+.26,7.05),box(half-.28,3.22,half-.07,7.1)]
    apply_plaster_wall(face,contour,windows,trim);plinth(face,-half,half)
    left,right=-3.07,3.32
    face.box((left+right)/2,3.30,right-left,.20,1.05,.41,'worn stone','west balcony slab')
    for u in (left+.08,right-.08):
        face.box(u,1.61,.27,3.15,.28,.78,'garden brick','balcony support')
    for z in (3.52,4.29):
        face.box((left+right)/2,z,right-left,.088,.12,.87,'balcony wood','street balcony rail')
    for u in np.linspace(left+.09,right-.09,31 if not lod else 21):
        face.box(u,3.90,.069,.72,.078,.87,'balcony wood','square turned baluster')
    for u in (left-.01,right+.01):
        face.box(u,4.29,.107,.085,.93,.45,'balcony wood','return handrail')
    return face


def pierced_brick_panel(face, a, b, z, lod):
    width=b-a
    panel=box(a,z,b,z+.82)
    bays=max(2,round(width/.68)); openings=[]
    for k in range(bays):
        x=a+(k+.5)*width/bays;semi=(width/bays)*.36
        # Paired arches and diamond-shaped spandrels in the garden photograph.
        pts=[(x-semi,z+.16),(x-semi,z+.41)]
        for t in np.linspace(math.pi,0,8 if lod else 16):
            pts.append((x+semi*math.cos(t),z+.40+.253*math.sin(t)))
        pts.extend([(x+semi,z+.16),(x,z+.30)])
        openings.append(Polygon(pts))
    face.prism(panel.difference(unary_union(openings)),.008,.172,'garden brick','perforated geometric brickwork')
    face.box((a+b)/2,z+.841,width+.05,.081,.23,.093,'brick sill','terrace coping')
    face.box((a+b)/2,z+.04,width,.08,.18,.080,'shaded brick','brick terrace base')


def terrace(builder,cells,lod):
    face=Facade(builder,RING[3],RING[2],'Garden terrace and east bay')
    half=face.length/2
    left=-half+.10; right=half-2.21; recess_depth=2.06; openings=[]
    # The terrace occupies the recess between two wings. Both floors are closed behind
    # the columns, keeping the floor of the lower open porch visible from the garden.
    openings.append(box(left,.13,right,6.69))
    east=right+(half-right)*.52
    openings.extend([window(face,east,1.03,2.65,1.18,2,lod,'east ground casement'),
                     window(face,east,4.12,5.91,1.28,2,lod,'east upper casement')])
    timber=[box(-half,3.21,half,3.40),box(-half,6.56,half,6.79)]
    timber+=studs((-half,half),np.arange(right,half+.01,.56),3.32,6.68)
    apply_plaster_wall(face,wall_outline(face,cells),openings,timber)
    plinth(face,right,half)
    back=Facade(builder,face.point(left,0,-recess_depth)[:2],face.point(right,0,-recess_depth)[:2],'Covered south porch')
    width=back.length;dw=1.63
    holes=[box(-dw/2,.15,dw/2,2.70)]
    back.prism(holes[0],-.22,-.17,'recessed door wood','recessed garden door')
    for x in (-.60,-.20,.20,.60):
        back.box(x,1.15,.23,1.30,.046,-.14,'oxidized Tudor timber','door inset')
    for x in (-width*.32,width*.32):
        holes.append(window(back,x,1.03,2.56,1.57,2,lod,'sheltered lower window',False))
    for x in np.linspace(-width*.34,width*.34,4):
        holes.append(window(back,x,3.95,5.93,1.54,2,lod,'terrace window',False))
    apply_plaster_wall(back,box(-width/2,.13,width/2,6.76),holes,[box(-width/2,3.25,width/2,3.46),*studs((-width/2,width/2),np.arange(-width/2+.19,width/2,.63),3.39,6.76)])
    for u in (left,right):
        edge=Facade(builder,face.point(u,0,-recess_depth)[:2],face.point(u,0,0)[:2],'Porch return')
        edge.wall(.14,6.73,[],.14,'ivory roughcast')
    face.box((left+right)/2,.115,right-left,.12,recess_depth+.12,-recess_depth/2,'worn stone','walkable porch floor')
    face.box((left+right)/2,3.30,right-left,.21,recess_depth+.23,-recess_depth/2+.035,'worn stone','terrace deck')
    columns=np.linspace(left+.14,right-.14,4)
    for u in columns:
        face.box(u,1.67,.36,3.05,.40,-.045,'garden brick','open porch brick pier')
        face.box(u,.29,.43,.31,.47,-.045,'shaded brick','porch pier foot')
        face.box(u,3.12,.44,.18,.49,-.035,'brick sill','porch pier capital')
        face.box(u,3.83,.30,.93,.31,.09,'garden brick','terrace pier')
        face.box(u,4.34,.38,.13,.39,.09,'worn stone','terrace pier cap')
    for l,r in zip(columns,columns[1:]):pierced_brick_panel(face,l+.155,r-.155,3.435,lod)
    return face


def roof_patch(builder,polygon,height,lod,label,run):
    if polygon.is_empty:return
    polygons=[g for g in getattr(polygon,'geoms',[polygon]) if g.geom_type=='Polygon' and g.area>.002]
    for part in polygons:
        for tri in constrained_delaunay_triangles(part).geoms:
            xy=list(tri.exterior.coords)[:-1]
            if not tri.exterior.is_ccw:xy.reverse()
            builder.add([(x,y,height(x,y))for x,y in xy],[(0,1,2)],'terracotta tile bed',label+'/tile surface')
        lo=part.bounds[run];hi=part.bounds[run+2];spacing=.318 if lod else .175
        for step in range(math.ceil(lo/spacing),math.floor(hi/spacing)+1):
            t=step*spacing
            line=LineString([(t,-25),(t,25)] if run==0 else [(-25,t),(25,t)])
            cross=line.intersection(part)
            lines=[s for s in getattr(cross,'geoms',[cross]) if s.geom_type=='LineString'and s.length>.06]
            for seg in lines:
                pts=[(x,y,height(x,y)+.015)for x,y in [seg.coords[0],seg.coords[-1]]]
                builder.tube(pts,.031 if lod else .039,'baked tile' if step%3 else 'tile ridge',5 if lod else 7,label+'/tile rolls')


def dormer(builder,center,front,span,low,eave,crown,hip,lod):
    back=YRIDGE-.15
    face=Facade(builder,(center-span/2,front),(center+span/2,front),'Hipped dormer' if hip else 'Timber gabled dormer')
    gable_height=eave if hip else crown
    contour=Polygon([(-span/2,low),(span/2,low),(span/2,eave),(0,gable_height),(-span/2,eave)])
    hole=window(face,0,low+.16,eave-.12,span*.75,3 if hip else 4,lod,'attic dormer lights')
    apply_plaster_wall(face,contour,[hole],[box(-span/2,low,span/2,low+.09)])
    if not hip:
        for z in np.arange(eave+.055,crown-.05,.115 if not lod else .24):
            half=span*.5*(crown-z)/(crown-eave)
            face.box(0,z,max(.02,2*half),.075,.071,.038,'reddish clay panels','stepped gable cladding')
    half=span/2+.095
    for sign in (-1,1):
        x=center+sign*span/2
        cheek=Facade(builder,(x,front),(x,back),'Dormer roof cheek')
        yjoin=YRIDGE-(RIDGE-eave)/.851
        if yjoin>front:
            a0=-(back-front)/2;u1=yjoin-(front+back)/2
            tri=Polygon([(a0,low),(u1,eave),(a0,eave)])
            cheek.prism(tri,-.057,.057,'oxidized Tudor timber','triangular cheek')
    rise=(crown-eave)/half
    # The dormer slopes meet the main roof along their own true height contour.
    for sign in (-1,1):
        xl,xr=sorted([center,center+sign*half])
        top=lambda x,y:crown-rise*abs(x-center)
        def joined(x):return YRIDGE-(RIDGE-top(x,0))/.851
        front_left=front-.07;front_right=front-.07
        if hip:
            slope=(crown-eave)/.82
            fy=lambda x:front-.07+(top(x,0)-eave)/slope
            front_left,front_right=fy(xl),fy(xr)
        poly=Polygon([(xl,front_left),(xr,front_right),(xr,joined(xr)),(xl,joined(xl))])
        roof_patch(builder,poly,top,lod,'Dormer pitches',1)
    if hip:
        tri=Polygon([(center-half,front-.07),(center+half,front-.07),(center,front+.75)])
        roof_patch(builder,tri,lambda x,y:eave+(y-front+.07)*(crown-eave)/.82,lod,'Dormer hipped front',0)
    else:
        for sign in (-1,1):
            face.line((sign*half,eave,.078),(0,crown,.078),.054,'oxidized Tudor timber',6,'dormer bargeboard')


def main_roof(builder,cells,lod):
    dormers=[(0.13,-3.75,2.6,8.32,9.44,10.46,True),(6.66,-3.92,3.47,8.23,9.43,11.13,False)]
    for cell in cells:
        x,y=cell.representative_point().coords[0]
        wing=y < YRIDGE and wing_height(x,y)>main_height(x,y)
        func=wing_height if wing else main_height
        shape=cell
        for center,front,span,low,eave,crown,hip in dormers:
            # Underlying roof is cut only inside the dormer's two observable cheeks.
            bounds=[(center-span/2,front),(center+span/2,front),(center+span/2,YRIDGE-(RIDGE-eave)/.851),(center,YRIDGE-(RIDGE-crown)/.851),(center-span/2,YRIDGE-(RIDGE-eave)/.851)]
            shape=shape.difference(Polygon(bounds))
        roof_patch(builder,shape,func,lod,'Cross wing' if wing else 'Main roof',1 if wing else 0)
    for row in dormers:dormer(builder,*row,lod)
    # Real, broad verge boards run along the roof contour on all four sides.
    for a,b in zip(RING,np.roll(RING,-1,axis=0)):
        face=Facade(builder,b,a,'Eaves')
        contour=wall_outline(face,cells);upper=[(u,z)for u,z in contour.exterior.coords if z>3]
        upper.sort(key=lambda q:q[0]);clean=[]
        for pt in upper:
            if not clean or math.dist(clean[-1],pt)>.017:clean.append(pt)
        if len(clean)>1:builder.tube([face.point(u,z,.20)for u,z in clean],.087,'oxidized Tudor timber',7 if not lod else 5,'Eaves/continuous verge')
        for u in np.linspace(-face.length/2+.21,face.length/2-.21,max(2,int(face.length/(.48 if not lod else .92)))):
            face.box(u,section_height(u,face)-.13,.102,.19,.31,.083,'oxidized Tudor timber','exposed rafter tail')
    join_y=YRIDGE-(RIDGE-WEST_CROWN)/.851
    builder.tube([(WEST_AXIS,-8.53,WEST_CROWN),(WEST_AXIS,join_y,WEST_CROWN)],.077,'tile ridge',8 if not lod else 6,'Cross wing capped ridge')
    builder.tube([(-10.02,YRIDGE,RIDGE),(11.26,YRIDGE,RIDGE)],.085,'tile ridge',8 if not lod else 6,'Main ridge cap')


def chimney(builder,x,y,z0,height,count,lod,name):
    width=count*.34+.16;depth=.48;top=z0+height
    builder.box((x,y,z0+height*.33),(width,depth,height*.66),'garden brick',label=name+'/tall shaft')
    # The stepped plan and the gaps between flues are visible against the sky.
    for i in range(count):
        xx=x-width/2+.25+(i*.34);yy=y+(i%2-.5)*.135
        builder.box((xx,yy,z0+height*.76),(.337,.43,height*.48),'garden brick' if i%2 else 'shaded brick',label=name+'/interlocking flue')
        builder.box((xx,yy,top-.065),(.39,.47,.135),'brick sill',label=name+'/cap')
        builder.box((xx,yy,top+.006),(.19,.26,.014),'charcoal flue',label=name+'/open flue')
    if not lod:
        for z in np.arange(z0+.26,top-.25,.226):
            builder.box((x,y-depth*.50-.009,z),(width-.018,.019,.015),'shaded brick',label=name+'/mortar courses')


def assemble(builder,lod):
    cells=roof_cells()
    front=Facade(builder,RING[3],RING[2],'South porch footprint')
    left=-front.length/2+.10;right=front.length/2-2.21
    recess=Polygon([front.point(u,0,d)[:2]for u,d in ((left,.04),(right,.04),(right,-2.06),(left,-2.06))])
    builder.plan_prism(OUTLINE.difference(recess),0,.14,'worn stone','Registered house footprint')
    west_garden_gable(builder,cells,lod)
    west_street_face(builder,cells,lod)
    terrace(builder,cells,lod)
    for index in (0,1,3):
        q=RING[index];r=RING[(index+1)%len(RING)]
        face=Facade(builder,r,q,'Rear, east or wing return '+str(index));contour=wall_outline(face,cells)
        apply_plaster_wall(face,contour,[],[]);plinth(face,-face.length/2,face.length/2)
        for edge in (-face.length/2+.03,face.length/2-.03):quoin(face,edge,.64,3.2,lod,'brick corner dressing')
    main_roof(builder,cells,lod)
    chimney(builder,-6.45,2.18,9.95,3.12,3,lod,'Western chimney')
    chimney(builder,3.55,1.34,10.95,2.70,4,lod,'Four joined central brick flues')


if __name__=='__main__':
    from final_preview import package
    package(build,HERE,META,PALETTE,assemble)
