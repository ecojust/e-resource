"""Build the documented exterior of St Nicholas on Gaolan Road (current principal church)."""
from pathlib import Path
import json
import math
import sys

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
from package_architectural_model import build
from photo_architecture import Facade, opening

P = json.loads((HERE / 'plan-parameters.json').read_bytes())
SCALE = P['uniform_m_per_reduced_plan_px']
DX, DY = P['plan_anchor_px']
SOUTH = P['southern_threshold_y_m']


def xy(x, y):
    return ((x - DX) * SCALE, SOUTH + (DY - y) * SCALE)


CX, CY = xy(350, 349)
COLOURS = {
    'glazed ivory brick': (.84, .815, .737), 'limestone beds': (.68, .661, .617),
    'buff reveals': (.783, .747, .647), 'very pale brick': (.876, .85, .78),
    'blue grey moulding': (.34, .378, .425), 'cornice light': (.47, .485, .498),
    'cornice shadow': (.229, .25, .283), 'green leaded glass': (.196, .282, .282),
    'amber drum glass': (.472, .435, .27), 'deep mullions': (.192, .206, .208),
    'cobalt window jamb': (.312, .363, .455), 'gold dome': (.792, .642, .294),
    'gold sheet seam': (.664, .537, .267), 'apse roof': (.405, .42, .424),
    'roof metal': (.344, .356, .376), 'threshold stone': (.477, .463, .439),
}
PALETTE = {name: {'color': list(rgb), 'roughness': .46 if 'gold' in name else .82,
                  'metallic': .44 if 'gold' in name else .05} for name, rgb in COLOURS.items()}
META = {
    'id': 'huangpu-gaolan-st-nicholas-church', 'name': '皋兰路圣尼古拉斯堂主堂',
    'status': 'photo-informed-exterior', 'viewer_page': 'gaolan-st-nicholas-church.html',
    'audit_directory': 'data/audit/gaolan-st-nicholas-v1/',
    'scope': 'Contemporary cross-shaped church, Gaolan Road open belfry and portal, curved side stair, nave, apse and gold onion dome. Public renovation plans and 1995–2021 photographs supply the geometric evidence.',
    'model_scope_zh': '皋兰路侧门楼、门窗与翼廊，十字形主堂、东端圆弧、叠层弧尖山花及当代金色主顶。高度和屋后收口按公开图纸及照片比例估算。历史九顶、院界、相邻商铺、后勤房及书店内装单列。',
    'coordinate_convention': 'Local glTF X east along Gaolan Road, Y up, +Z towards the street at 162.76 degrees true.',
    'map_reference_license': 'OpenStreetMap and Overture Maps, ODbL-1.0.', 'interiors_modeled': False,
}


def gable(width, spring, crown, segments, street=False):
    """Two cubic shoulders rise to the ogee tip. The belfry has outward-turning feet."""
    t = np.linspace(0, 1, segments + 1)
    if street:
        x1,y1,x2,y2=.66,.83,.62,.075
    else:
        x1,y1,x2,y2=.34,.73,.96,.90
    xs=3*(1-t)**2*t*x1+3*(1-t)*t*t*x2+t**3
    zs=(1-t)**3+3*(1-t)**2*t*y1+3*(1-t)*t*t*y2
    side=[(float(x*width/2),float(spring+(crown-spring)*z))for x,z in zip(xs,zs)]
    return [(-x,z) for x,z in reversed(side[1:])]+side


def curve_bands(face, profile, bands, label):
    """Separate projecting courses rise over each arch and meet continuously at the tip."""
    for shift, thickness, depth, mat in bands:
        line = LineString([(x, h + shift) for x, h in profile])
        face.prism(line.buffer(thickness / 2, cap_style='flat', join_style='round'), -.045, depth, mat, label)


def masonry(face, shape, lod):
    """Shallow courses and staggered perpendicular joints follow the real cutouts."""
    if shape.is_empty or face.length < .62:
        return
    left, bottom, right, top = shape.bounds
    step = .34 if lod else .20
    # Horizontal joints retained in the LOD; sparse vertical joints suffice beyond near range.
    rows = list(np.arange(bottom + .16, top - .04, step))
    parts = []
    for j, z in enumerate(rows):
        strips = [box(left, z, right, z + (.014 if lod else .012))]
        if not lod:
            for x in np.arange(left + (.27 if j % 2 else .49), right, .55):
                strips.append(box(x, z + .012, x + .012, min(z + step, top)))
        line = unary_union(strips).intersection(shape)
        if not line.is_empty and line.area > .00005:
            parts.append(line)
    if parts:
        face.prism(unary_union(parts), .0025, .0065, 'limestone beds', 'coursed light brickwork')


def glazed(face, form, cols, rows, material, rim, label):
    face.prism(form.buffer(.014), -.259, -.227, material, label + ' / recessed panes')
    x0, z0, x1, z1 = form.bounds
    outer = form.buffer(-.016)
    inside = form.buffer(-.072)
    lines = []
    for k in range(1, cols):
        x = x0 + k * (x1 - x0) / cols
        lines.append(box(x - .019, z0, x + .019, z1))
    for k in range(1, rows):
        z = z0 + k * (z1 - z0) / rows
        lines.append(box(x0, z - .020, x1, z + .020))
    panes = inside.difference(unary_union(lines))
    face.prism(outer.difference(panes), -.20, -.137, 'deep mullions', label + ' / frame and bars')
    face.prism(form.buffer(.098, join_style='round').difference(form).intersection(box(x0-.31,.015,x1+.31,z1+.31)), -.065, .062, rim, label + ' / reveal')


def lower_window(face, u, lod):
    win = opening(u, .46, .82, 2.16, .39, 10 if lod else 19)
    glazed(face, win, 2, 3, 'green leaded glass', 'cobalt window jamb', 'street paired glazing')
    for side in (-1, 1):
        x = u + side * .49
        base = face.point(x, 0, .083)
        face.builder.lathe(base[:2], [(.42,.116),(.55,.115),(.58,.093),(1.25,.087),
                                     (1.31,.125),(1.39,.126),(1.44,.087),(2.49,.085),
                                     (2.56,.117),(2.63,.125)], 'cobalt window jamb',
                           8 if lod else 16, 'Street windows/painted jamb colonnettes')
    hood = gable(1.24, 2.69, 3.32, 7 if lod else 15)
    hood = [(u + x, z) for x, z in hood]
    face.prism(Polygon([(hood[0][0],2.65),*hood,(hood[-1][0],2.65)]), -.025, .09,
               'buff reveals','window pointed tympanum')
    curve_bands(face, hood, [(0,.115,.157,'cobalt window jamb'),(-.107,.065,.13,'cornice light')], 'modelled window hood')
    centre = face.point(u,2.955,.11)
    t = face.t
    for ang in np.arange(0,2*math.pi,math.pi/3):
        ux, uz = .071*math.cos(ang), .071*math.sin(ang)
        axis = [tuple(centre), tuple(centre + t*ux + np.array([0.,0.,uz]))]
        face.builder.tube(axis,.021,'cobalt window jamb',5,'Street windows/six-lobed rosettes')
    return win


def gate_door(face, u, lod):
    form = opening(u,.075,1.54,2.82,.77,14 if lod else 30)
    glazed(face,form,2,3,'green leaded glass','buff reveals','arched double entrance door')
    # Distinct radial fanlight above the doors, visible in the 2020 straight street image.
    spring = .075 + 2.82 - .77
    for angle in np.linspace(0,math.pi,6):
        x = u+.682*math.cos(angle); z=spring+.682*math.sin(angle)
        face.line((u,spring,-.114),(x,z,-.114),.024,'deep mullions',6,'sunburst fanlight')
    face.prism(form.buffer(.19).difference(form.buffer(.12)).intersection(box(u-1.3,.015,u+1.3,3.3)), -.012, .112,'very pale brick','portal outer archivolt')
    face.prism(form.buffer(.276).difference(form.buffer(.22)).intersection(box(u-1.3,.015,u+1.3,3.3)), -.015, .075,'buff reveals','portal second archivolt')
    return form


def hall_and_apse(b, lod):
    polygons = {k: orient(Polygon(q),sign=1) for k,q in P['parts_photo_plan_xy_m'].items()}
    # The north-west service rooms and outside café are distinct in the published diagram.
    outline = orient(unary_union([polygons[k] for k in
        ('main','western_entry','east_apse','south_east_stair','northeast_chamber')]),sign=1)
    b.plan_prism(outline,0,.105,'threshold stone','Church/ground plinth')
    b.plan_prism(outline,3.72,3.84,'roof metal','Church/lower roof')
    walls=list(outline.exterior.coords)
    front_windows = [xy(296,525)[0],xy(351,525)[0]]
    door_x = xy(403,525)[0]
    for j,(a,c) in enumerate(zip(walls,walls[1:])):
        face = Facade(b,a,c,'Lower exterior '+str(j+1))
        south = face.n[1] < -.99
        west = face.n[0] < -.99
        holes = []
        if south and max(abs(a[1]-SOUTH), abs(c[1]-SOUTH))<.015:
            for x in front_windows:
                u = x - face.center[0]
                holes.append(lower_window(face,u,lod))
            holes.append(gate_door(face,door_x-face.center[0],lod))
        elif south and abs(a[1]-xy(0,435)[1])<.015 and face.length>1.7:
            holes.append(lower_window(face,-.06,lod))
        elif west and face.length>4.5:
            holes.append(gate_door(face,0,lod))
        elif face.n[0]>.3 and face.length>.7 and 2.3<face.center[0]<6.48 and a[1]<2.0 and c[1]<2.0:
            if not lod and face.length>1.15:
                recessed=opening(0,.91,.43,1.52,.20,10)
                glazed(face,recessed,1,2,'green leaded glass','buff reveals','apse narrow window')
                holes.append(recessed)
        skin=face.wall(.10,3.75,holes,.24,'glazed ivory brick')
        if face.length>.6:masonry(face,skin,lod)
        if face.length>.25:
            face.beam(3.70,.13,.11,'blue grey moulding')
            face.beam(3.82,.08,.15,'cornice light')
    return polygons


def open_portal(b,lod):
    """Upper bell opening has visible back wall, sill, two posts and an independent ogee silhouette."""
    x=xy(403,525)[0]; w=2.75; y=SOUTH-.022
    face=Facade(b,(x-w/2,y),(x+w/2,y),'Street gate / open belfry')
    opening_upper=opening(0,4.63,1.94,1.79,.91,14 if lod else 28)
    peak=gable(w+.14,6.15,7.76,10 if lod else 22,street=True)
    silhouette=Polygon([(-w/2-.07,3.77),(w/2+.07,3.77),*reversed(peak)])
    face.wall(3.77,7.76,[opening_upper],.36,'glazed ivory brick',outline=silhouette)
    masonry(face,silhouette.difference(opening_upper),lod)
    inner=opening(0,4.74,1.44,1.33,.69,12 if lod else 22)
    face.prism(opening_upper.difference(inner),-.98,-.91,'buff reveals','recess back wall and inner arch')
    face.prism(inner.buffer(.105).difference(inner),-.93,-.85,'very pale brick','inner belfry archivolt')
    face.prism(inner,-1.26,-1.23,'roof metal','shadow in inner belfry recess')
    face.box(0,4.81,1.40,.055,.46,-.94,'buff reveals','low recessed sill')
    face.box(0,4.61,1.98,.13,1.11,-.46,'buff reveals','deep belfry sill')
    for side in (-1,1):
        for offset in (-.08,.08):
            u=side*(1.03+offset); p=face.point(u,0,.04)
            b.lathe(p[:2],[(4.57,.132),(4.73,.136),(4.81,.109),(5.34,.093),(5.52,.119),(5.66,.139)],
                    'buff reveals',8 if lod else 16,'Street gate/paired round posts')
    curve_bands(face,peak,[(0,.15,.16,'blue grey moulding'),(-.12,.083,.10,'cornice light')],'belfry curved crown')
    face.box(0,3.77,w+.18,.13,.46,0,'blue grey moulding','continuous gate ledge')
    for side in (-1,1):
        b.box((x+side*(w/2-.12),y+.54,5.05),(.24,1.07,2.56),'glazed ivory brick',label='Street gate/side returns')
    b.box((x,y+.52,6.23),(w,1.0,.16),'roof metal',label='Street gate/recess roof')
    for i in range(3):
        face.box(0,.035*(i+1),1.90-.06*i,.07*(i+1),.15,.34-i*.115,'threshold stone','entry steps')


def top_assembly(b,lod):
    half=3.11; shoulder=1.58
    corners=[(CX+x,CY+y)for x,y in [(-shoulder,-half),(shoulder,-half),(half,-shoulder),(half,shoulder),
                                     (shoulder,half),(-shoulder,half),(-half,shoulder),(-half,-shoulder)]]
    b.plan_prism(Polygon(corners),9.55,9.64,'roof metal','Crossing/upper roof below drum')
    for j,(a,c) in enumerate(zip(corners,corners[1:]+corners[:1])):
        face=Facade(b,a,c,'Crossing / arch '+str(j+1)); width=face.length
        diagonal=j%2==1
        spring,top=(9.10,10.68) if diagonal else (8.15,10.64)
        peak=gable(width,spring,top,10 if lod else 22)
        outline=Polygon([(-width/2,3.8),(width/2,3.8),*reversed(peak)])
        windows=[]
        if not diagonal:
            win=opening(0,4.99,1.23,4.18,.615,14 if lod else 28)
            glazed(face,win,3,6,'green leaded glass','buff reveals','tall arched light');windows.append(win)
        skin=face.wall(3.8,top,windows,.27,'glazed ivory brick',outline)
        masonry(face,skin,lod)
        curve_bands(face,peak,[(0,.168,.18,'blue grey moulding'),(-.12,.059,.135,'cornice light'),
                              (-.205,.067,.08,'cornice shadow')],'crossing ogee cornices')
        if diagonal:
            # Each diagonal return carries a second taller ogee, behind the first.
            peak2=[(u*.96,z+.55) for u,z in peak]
            lip=Polygon([(-width*.48,spring-.04),(width*.48,spring-.04),*reversed(peak2)])
            face.prism(lip,-.22,-.075,'glazed ivory brick','upper diagonal kokoshnik')
            for dz,mat in [(0,'blue grey moulding'),(-.121,'cornice light')]:
                line=LineString([(u,z+dz)for u,z in peak2]).buffer(.064,cap_style='flat')
                face.prism(line,-.12,-.002,mat,'second row of pointed shoulders')
            # Square corner piers end below the diagonal gables in the 2011 and 2021 views.
            signx=1 if face.center[0]>CX else -1;signy=1 if face.center[1]>CY else -1
            px,py=CX+signx*2.395,CY+signy*2.395
            b.box((px,py,5.99),(1.43,1.43,4.40),'glazed ivory brick',label='Crossing/square projecting corner pilaster')
            for h,sz,mat in [(8.14,1.55,'cornice shadow'),(8.24,1.63,'cornice light'),(8.32,1.69,'cornice shadow')]:
                b.box((px,py,h),(sz,sz,.085),mat,label='Crossing/layered pilaster cap')
            for axis in (0,1):
                for k in range(5):
                    u=-.54+k*.27
                    b.box((px+(u if axis==0 else signx*.755),py+(signy*.755 if axis==0 else u),8.045),
                          (.11,.11,.16),'cornice shadow',label='Crossing/individual cornice dentils')
        # Return the curved wall into the roof; the inner end disappears under the upper drum.
        vertices=[];faces=[]
        for u,z in peak:
            vertices.extend([face.point(u,z-.02,-.01),face.point(u*.60,10.42,-1.27)])
        for k in range(len(peak)-1):
            i=2*k;faces.append((i,i+2,i+3,i+1))
        b.add(vertices,faces,'roof metal','Crossing/barrel roof returns')
    count=8; angles=[(i-.5)*2*math.pi/count-math.pi/2 for i in range(count)]
    r=2.405;points=[(CX+r*math.cos(v),CY+r*math.sin(v))for v in angles]
    b.plan_prism(Polygon(points),12.35,12.44,'roof metal','Drum/upper deck')
    for j,(a,c) in enumerate(zip(points,points[1:]+points[:1])):
        face=Facade(b,a,c,'Drum / facet '+str(j+1));width=face.length
        tip=gable(width,12.25,12.99,8 if lod else 17)
        contour=Polygon([(-width/2,9.95),(width/2,9.95),*reversed(tip)])
        o=opening(0,10.57,.68,1.51,.31,10 if lod else 20)
        face.wall(9.95,12.99,[o],.17,'glazed ivory brick',contour)
        # Alternating glazed and blind facets appear in the post-renovation southwest view.
        if j%2==0:glazed(face,o,2,3,'amber drum glass','buff reveals','upper glazed arch')
        else:face.prism(o,-.125,-.10,'buff reveals','shallow blind arch')
        masonry(face,contour.difference(o),lod)
        curve_bands(face,tip,[(0,.13,.14,'blue grey moulding'),(-.13,.072,.09,'cornice light')],'drum gable mouldings')
        # The gold onion sits on an independent collar. These continuous returns close the
        # spaces behind the eight scalloped cap fronts while retaining each silhouette.
        rim=[];roof_faces=[]
        for u,z in tip:
            rim.extend([face.point(u,z-.014,-.025),face.point(u*.57,13.13,-.83)])
        for k in range(len(tip)-1):
            q=k*2;roof_faces.append((q,q+2,q+3,q+1))
        b.add(rim,roof_faces,'cornice light','Drum/continuous sloping crown behind gables')
    return half


def onion(b, xy_pos, z, radius, height, small, lod):
    # 2021 shows rounded gilt shoulders and an almost spherical crown; the long historic point is absent.
    prof=[(0,.54),(.095,.66),(.23,.88),(.43,1.0),(.61,1.0),(.77,.90),(.88,.72),(.955,.46),(.99,.16),(1,.035)]
    seg=12 if small and lod else (20 if small or lod else 48)
    sections=[(z+v*height,radius*r)for v,r in prof]
    b.lathe(xy_pos,sections,'gold dome',seg,'Upper crown/gilt copper skin')
    n=6 if small else (12 if lod else 24)
    if not (small and lod):
        for j in range(n):
            a=2*math.pi*j/n
            b.tube([(xy_pos[0]+r*math.cos(a),xy_pos[1]+r*math.sin(a),h) for h,r in sections],
                   .006 if small else .012,'gold sheet seam',4 if lod else 6,'Upper crown/fine sheet seams')
    b.lathe(xy_pos,[(z+height-.02,.026 if small else .045),(z+height+.12,.009 if small else .012)],
            'gold sheet seam',8,'Upper crown/short pin')


def assemble(b,lod):
    hall_and_apse(b,lod)
    # East apse and the round-ended stair both have their own projecting cap in the 2020 axonometric.
    for name,z in [('east_apse',3.82),('south_east_stair',6.15)]:
        p=orient(Polygon(P['parts_photo_plan_xy_m'][name]),sign=1)
        if name=='south_east_stair':
            start=list(p.exterior.coords)
            for j,(a,c)in enumerate(zip(start,start[1:])):
                face=Facade(b,a,c,'Stair return '+str(j+1))
                if not j%3 and face.length>1.3:
                    o=opening(0,4.14,.44,1.27,.22,12);face.wall(3.81,z,[o],.16,'glazed ivory brick')
                    glazed(face,o,1,3,'green leaded glass','buff reveals','stair arch')
                else:face.wall(3.81,z,[],.16,'glazed ivory brick')
        b.plan_prism(p.buffer(.102),z,z+.12,'blue grey moulding','Round returns/cap eaves')
        core=p.centroid;edge=np.array(p.exterior.coords[:-1]);centre=np.array(core.coords[0])
        profile=[(0,1.02),(.18,.997),(.38,.91),(.54,.74),(.65,.42),(.70,.035)]
        ring_count=len(edge);vertices=[(x,y,z+.11+h)for h,sc in profile for x,y in centre+(edge-centre)*sc]
        faces=[]
        for k in range(len(profile)-1):
            for i in range(ring_count):
                j=(i+1)%ring_count;faces.append((k*ring_count+i,k*ring_count+j,(k+1)*ring_count+j,(k+1)*ring_count+i))
        faces.append(tuple((len(profile)-1)*ring_count+i for i in range(ring_count)))
        b.add(vertices,faces,'apse roof','Round returns/continuous curved metal cap')
    west_x=xy(199,349)[0];x1,y1=xy(199,435);x2,y2=xy(199,261)
    west_face=Facade(b,(west_x,y2),(west_x,y1),'West entrance gable')
    g=gable(west_face.length,3.85,5.47,10 if lod else 20,street=True)
    form=Polygon([(-west_face.length/2,3.80),(west_face.length/2,3.80),*reversed(g)])
    holes=[opening(k,3.89,.40,.78,.20,14)for k in (-.37,.37)]
    oculus=Point(0,5.0).buffer(.18,quad_segs=8 if lod else 16)
    west_face.wall(3.80,5.47,holes+[oculus],.23,'glazed ivory brick',form)
    for win in holes:glazed(west_face,win,1,2,'green leaded glass','buff reveals','twin porch gable lights')
    west_face.prism(oculus,-.18,-.14,'buff reveals','round medallion')
    west_face.prism(oculus.buffer(.075).difference(oculus),0,.10,'cornice light','round medallion rim')
    curve_bands(west_face,g,[(0,.12,.14,'blue grey moulding'),(-.09,.05,.08,'cornice light')],'west gable trim')
    open_portal(b,lod)
    top_assembly(b,lod)
    b.lathe((CX,CY),[(12.35,1.56),(12.55,1.59),(12.70,1.52),(13.11,1.49),(13.20,1.55)],
            'buff reveals',24 if lod else 56,'Crown/neck below gold dome')
    onion(b,(CX,CY),13.13,1.63,2.83,False,lod)
    # Two small gilt terminals are visible together in the modern southwest photograph.
    # Only the two independently visible western/drum shoulder positions are represented.
    for angle in (-3*math.pi/4,3*math.pi/4):
        c=(CX+2.20*math.cos(angle),CY+2.20*math.sin(angle))
        b.lathe(c,[(12.57,.24),(12.76,.26),(12.82,.22)],'cornice light',12,'Drum/finial bases')
        onion(b,c,12.79,.285,.48,True,lod)


if __name__=='__main__':
    from final_preview import package
    package(build,HERE,META,PALETTE,assemble)
