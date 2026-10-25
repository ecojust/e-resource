"""Photo-interpreted perforated stone facades. All distances are inferred meters.
No solid mass is placed behind a window. Cells surrounding each aperture form
one thick wall mesh; cut-edge faces are actual stone reveals.
"""
import math
from mathutils import Vector

UP=Vector((0,0,1))

def thick_wall(b, origin, normal, width, z0, z1, openings, thickness=.72, mat=0):
    n=Vector(normal);u=Vector((-n.y,n.x,0));origin=Vector((*origin,0))
    xs=sorted(set([-width/2,width/2]+[q for hole in openings for q in hole[:2] if -width/2<q<width/2]))
    zs=sorted(set([z0,z1]+[q for hole in openings for q in hole[2:] if z0<q<z1]))
    nx,nz=len(xs),len(zs)
    occupied=[]
    for j in range(nz-1):
        row=[]
        for i in range(nx-1):
            x,z=(xs[i]+xs[i+1])/2,(zs[j]+zs[j+1])/2
            row.append(not any(a<x<c and d<z<e for a,c,d,e in openings))
        occupied.append(row)
    vertices=[origin+u*x+UP*z-n*depth for depth in [0,thickness] for z in zs for x in xs]
    def index(layer,i,j):return layer*nx*nz+j*nx+i
    faces=[]
    for j in range(nz-1):
        for i in range(nx-1):
            if not occupied[j][i]:continue
            o00,o10,o11,o01=[index(0,a,c) for a,c in [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]]
            q00,q10,q11,q01=[index(1,a,c) for a,c in [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]]
            faces.extend([(o00,o10,o11,o01),(q01,q11,q10,q00)])
            if i==0 or not occupied[j][i-1]:faces.append((o00,o01,q01,q00))
            if i==nx-2 or not occupied[j][i+1]:faces.append((o10,q10,q11,o11))
            if j==0 or not occupied[j-1][i]:faces.append((o00,q00,q10,o10))
            if j==nz-2 or not occupied[j+1][i]:faces.append((o01,o11,q11,q01))
    b.geom(vertices,faces,mat)


def oriented_box(b,origin,n,center,size,mat):
    n=Vector(n);u=Vector((-n.y,n.x,0));base=Vector((*origin,0))
    along,depth,z=center
    b.box(base+u*along+n*depth+UP*z,size,mat,[u,n,UP])


def inset_window(b,origin,normal,along,z,w,h,depth=.45,outer_trim=True,divisions=3):
    """Glass front is 0.43 m behind the outer stone, not on top of it."""
    box=lambda c,s,m:oriented_box(b,origin,normal,c,s,m)
    box((along,-depth,z),(w,.04,h),2)
    # Bronze frame is also behind the outside face. The actual reveals come
    # from thick_wall; no wall, dark backing plane or filler crosses the pane.
    for a in [along-w/2,along+w/2]:box((a,-depth+.035,z),(.075,.09,h+.12),4)
    for zz in [z-h/2,z+h/2]:box((along,-depth+.035,zz),(w+.15,.09,.075),4)
    for k in range(1,divisions):box((along-w/2+w*k/divisions,-depth+.065,z),(.045,.09,h),4)
    for k in range(1,4):box((along,-depth+.065,z-h/2+h*k/4),(w,.09,.045),4)
    if outer_trim:
        for a in [along-w/2-.115,along+w/2+.115]:box((a,.025,z),(.13,.18,h+.32),1)
        box((along,.045,z+h/2+.12),(w+.36,.22,.15),1)
    # Sloped two-tier sill: visible forward projection and shaded underside.
    box((along,.095,z-h/2-.11),(w+.38,.40,.16),1)
    box((along,.045,z-h/2-.21),(w+.24,.30,.07),0)


def extruded_profile(b,origin,normal,polygon,depth,thickness,mat):
    n=Vector(normal);u=Vector((-n.y,n.x,0));base=Vector((*origin,0));count=len(polygon)
    verts=[base+u*a+UP*z+n*d for d in [depth,depth-thickness] for a,z in polygon]
    faces=[tuple(range(count)),tuple(reversed(range(count,count*2)))]
    faces.extend((i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count))
    b.geom(verts,faces,mat)


def arch_window(b,origin,normal,along,bottom,spring,radius=.75):
    # Fill only the two corner spandrels above the true curved opening.
    top=spring+radius
    left=[(along-radius,spring),(along-radius,top),(along,top)]
    left += [(along+radius*math.cos(a),spring+radius*math.sin(a)) for a in [math.pi/2+math.pi*k/48 for k in range(1,24)]]
    right=[(along,top),(along+radius,top),(along+radius,spring)]
    right += [(along+radius*math.cos(a),spring+radius*math.sin(a)) for a in [math.pi*k/48 for k in range(1,24)]]
    extruded_profile(b,origin,normal,left,0,.72,0)
    extruded_profile(b,origin,normal,right,0,.72,0)
    poly=[(along-radius,bottom),(along+radius,bottom)]
    poly += [(along+radius*math.cos(math.pi*k/32),spring+radius*math.sin(math.pi*k/32)) for k in range(33)]
    extruded_profile(b,origin,normal,poly,-.45,.04,2)
    # A volumetric arch molding, with a visible inner and outer edge.
    n=Vector(normal);u=Vector((-n.y,n.x,0));base=Vector((*origin,0));verts=[]
    for depth in [.12,-.06]:
        for radius2 in [radius,radius+.18]:
            for k in range(33):
                a=math.pi*k/32
                verts.append(base+u*(along+radius2*math.cos(a))+UP*(spring+radius2*math.sin(a))+n*depth)
    faces=[]
    for k in range(32):
        faces.extend([(k,k+1,33+k+1,33+k),(66+k,99+k,99+k+1,66+k+1),
                      (k,66+k,66+k+1,k+1),(33+k,33+k+1,99+k+1,99+k)])
    faces.extend([(0,33,99,66),(32,98,131,65)])
    b.geom(verts,faces,1)
    for a in [along-radius-.09,along+radius+.09]:
        oriented_box(b,origin,normal,(a,.03,(spring+bottom)/2),(.18,.24,spring-bottom),1)
    for a in [along-radius/3,along+radius/3]:
        height=math.sqrt(radius**2-(a-along)**2)+spring-bottom
        oriented_box(b,origin,normal,(a,-.385,bottom+height/2),(.045,.10,height),4)
    for z in [bottom+.75,bottom+1.5,spring]:
        oriented_box(b,origin,normal,(along,-.385,z),(radius*2,.10,.045),4)
    oriented_box(b,origin,normal,(along,.10,bottom-.10),(radius*2+.45,.45,.18),1)


def refined_main_block(b,footprint):
    F=11.71;W=36.345;D=23.425;columns=[-7.8,-3.9,0,3.9,7.8]
    rows=[(9.65,3.25),(14.25,3.45),(18.65,3.45),(23.0,3.50)]
    b.outline(footprint,0,1.55,5)
    for side in [-1,1]:
        normal=(side,0,0);origin=(side*F,0)
        # Tangent points north on the east face and south on the west face.
        holes=[(y-1.0,y+1.0,7.75,25.45) for y in columns]
        holes += [(y-.975,y+.975,29.15,32.05) for y in [-7.8,-3.9,0,3.9,7.8]]
        for y in columns:
            width=2.8 if side==1 and abs(y)<10 else 1.85
            low=1.55 if side==1 and abs(y)<10 else 2.25
            high=6.58 if side==1 and abs(y)<10 else 6.35
            holes.append((y-width/2,y+width/2,low,high))
        thick_wall(b,origin,normal,W,1.55,33.20,holes)
        for y in columns:
            for z,h in rows:inset_window(b,origin,normal,y,z,1.66,h,outer_trim=False)
            # Dark inter-storey spandrels sit inside each continuous stone slot.
            span=7.75
            for z,h in rows+[(25.45,0)]:
                upper=z-h/2
                if upper>span:
                    oriented_box(b,origin,normal,(y,-.39,(span+upper)/2),(1.86,.12,upper-span),4)
                    if upper-span>.45:
                        for yy in [y-.58,y,y+.58]:
                            oriented_box(b,origin,normal,(yy,-.30,(span+upper)/2),(.045,.055,upper-span-.14),0)
                        oriented_box(b,origin,normal,(y,-.30,span+.13),(1.72,.055,.045),0)
                        oriented_box(b,origin,normal,(y,-.30,upper-.13),(1.72,.055,.045),0)
                span=z+h/2
            if side==1 and abs(y)<10:
                # Actual recessed entrance portals, not glass pasted on a box.
                oriented_box(b,origin,normal,(y,-1.15,3.92),(2.58,.06,4.60),2)
                for yy in [y-1.24,y,y+1.24]:oriented_box(b,origin,normal,(yy,-1.07,3.93),(.085,.14,4.62),4)
                for j in range(13):oriented_box(b,origin,normal,(y-1.2+j*.2,-1.02,3.15),(.035,.06,3.08),4)
                for zz in [1.73,3.5,4.74,5.6,6.2]:oriented_box(b,origin,normal,(y,-1.02,zz),(2.55,.075,.055),4)
                for yy in [y-1.46,y+1.46]:
                    oriented_box(b,origin,normal,(yy,.025,4.03),(.17,.22,5.10),1)
                    oriented_box(b,origin,normal,(yy,.05,1.75),(.34,.35,.36),5)
                    oriented_box(b,origin,normal,(yy,.07,6.36),(.40,.35,.30),1)
                oriented_box(b,origin,normal,(y,.08,6.68),(3.20,.48,.28),1)
            else:inset_window(b,origin,normal,y,4.30,1.65,3.90)
        for y in [-7.8,-3.9,0,3.9,7.8]:inset_window(b,origin,normal,y,30.60,1.72,2.70)
        # Cut course joints stop at the slot boundaries rather than traversing glass.
        intervals=[];edge=-W/2
        for y in columns:intervals.append((edge,y-1.04));edge=y+1.04
        intervals.append((edge,W/2))
        for low,high in intervals:
            if high-low<.12:continue
            for z in [8.0+i*1.55 for i in range(12)]:
                oriented_box(b,origin,normal,((low+high)/2,.006,z),(high-low,.012,.022),3)
        for j in range(34):
            y=-17.5+j*1.06
            oriented_box(b,origin,normal,(y,.24,26.65),(.42,.30,.78),1)
            oriented_box(b,origin,normal,(y,.31,27.18),(.65,.38,.13),0)
        # Attic gallery has physical posts, a top rail and a separate lower rail.
        for y in [-10.8+i*.9 for i in range(25)]:
            oriented_box(b,origin,normal,(y,.38,28.87),(.085,.085,.92),4)
            oriented_box(b,origin,normal,(y,.38,28.45),(.19,.19,.10),1)
        for z in [28.66,29.32]:oriented_box(b,origin,normal,(0,.38,z),(22.1,.11,.09),4)
    # North and south elevations are also fully perforated stone shells.
    for side in [-1,1]:
        normal=(0,side,0);origin=(0,side*W/2);bays=[-3.5,0,3.5]
        levels=[(4.30,3.9),(9.65,3.25),(14.25,3.45),(18.65,3.45),(23.,3.50),(30.60,2.70)]
        holes=[(a-.99,a+.99,z-h/2-.10,z+h/2+.10) for a in bays for z,h in levels]
        thick_wall(b,origin,normal,D,1.55,33.20,holes)
        for a in bays:
            for z,h in levels:inset_window(b,origin,normal,a,z,1.65,h)
        for a in [-10.7,-6,-2,2,6,10.7]:
            for z in [8+i*1.55 for i in range(12)]:
                width=1.3 if abs(a)>10 else 1.70
                oriented_box(b,origin,normal,(a,.006,z),(width,.012,.022),3)
    # Structural floor plates remain between clear window apertures.
    for z in [7.20,11.85,16.40,20.80,25.25,33.05]:
        b.box((0,0,z),(D-1.35,W-1.35,.22),3)
    b.box((0,0,1.60),(D+.24,W+.24,.22),1)
    for z,thick,overhang in [(6.9,.45,.32),(7.35,.25,.35),(25.7,.30,.36),(27.55,.58,.62),(28.15,.25,.42),(33.15,.45,.52)]:
        b.box((0,0,z),(D+overhang,W+overhang,thick),1)
    # Multi-course plinth and entry stair: six risers reaching the existing 1.55m datum.
    for j in range(6):
        rise=(j+1)*1.55/6;front=F+2.0-j*.30
        b.box(((F+front)/2,0,rise/2),(front-F,20.2,rise),5 if j==0 else 1)
    for y in [-10.25,10.25]:
        b.box((F+.85,y,.92),(1.85,.32,1.84),5)
        b.box((F+.85,y,1.91),(2.0,.45,.18),1)
    # Four physically mapped corner pavilions replace the original two guessed boxes.
    mapped_corner_pavilions(b)


def refined_tower_shaft(b,C):
    for nx,ny in [(1,0),(-1,0),(0,1),(0,-1)]:
        n=Vector((nx,ny,0));origin=Vector((*C,0))+n*5.30;xy=(origin.x,origin.y)
        holes=[(off-.61,off+.61,41.55,47.85) for off in [-2.08,0,2.08]]
        thick_wall(b,xy,n,10.6,39.90,49.40,holes,.60)
        for offset in [-2.08,0,2.08]:inset_window(b,xy,n,offset,44.70,1.08,6.10,depth=.45,outer_trim=False,divisions=2)
        for z in [40.9,42.2,43.5,44.8,46.1,47.4]:
            for off in [-4.25,-1.04,1.04,4.25]:oriented_box(b,xy,n,(off,.006,z),(1.0,.012,.022),3)


MAPPED_PAVILIONS = [{'osm_id': 178407323, 'polygon': [[-12.738449090865078, -10.591366084801573], [-13.076587751175591, -18.94518096406945], [-5.537827020868358, -19.265959182530704], [-5.496235464641453, -18.15469132891797], [-5.188962514633346, -10.902218640818269], [-11.709987975598553, -10.653930554175954]], 'center': [-9.134914265362147, -14.929982803125501]}, {'osm_id': 178407328, 'polygon': [[-14.036194265205294, 21.209308666790438], [-13.81300717344854, 12.400269815730022], [-11.706146344858846, 12.459122052793381], [-5.947157668857875, 12.588710294214497], [-6.10136640816588, 18.164411113603844], [-6.170351154647802, 21.397748976994233]], 'center': [-9.994666012964602, 16.90071172845385]}, {'osm_id': 178407330, 'polygon': [[5.916420994474347, -10.562062125495842], [5.818459744036975, -18.162279727322804], [5.785829964341953, -19.029046903363326], [12.965040521083509, -19.141023170860326], [13.095625861083406, -10.674038302169553], [11.710654885139117, -10.626248523399187]], 'center': [9.446793962599443, -14.843573640391694]}, {'osm_id': 178407333, 'polygon': [[4.643122968120242, 21.034900524362737], [4.59998387581023, 18.16044441207137], [4.505944872473881, 13.260626964006025], [11.704062001767817, 13.146471385955987], [12.601291271821575, 13.110172988102113], [12.738463473312047, 20.884446657635365]], 'center': [8.622859062666317, 17.077271842024274]}]

def pavilion_edges(pavilion):
    points=pavilion['polygon'];edges=[]
    for i,p in enumerate(points):
        q=points[(i+1)%len(points)];dx,dy=q[0]-p[0],q[1]-p[1];length=math.hypot(dx,dy)
        if length<.01:continue
        edges.append({'origin':((p[0]+q[0])/2,(p[1]+q[1])/2),'normal':(dy/length,-dx/length,0),'width':length,'index':i})
    return edges


def polygon_roof(b,points,center):
    def scaled(f):return [(center[0]+(x-center[0])*f,center[1]+(y-center[1])*f) for x,y in points]
    lower=scaled(1.055);upper=scaled(.965);count=len(points)
    b.outline(lower,34.92,35.38,1)
    verts=[(x,y,z) for poly,z in [(lower,35.38),(upper,36.0)] for x,y in poly]
    faces=[tuple(reversed(range(count))),tuple(count+i for i in range(count))]
    faces.extend((i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count))
    b.geom(verts,faces,3)
    b.outline(scaled(.98),36.0,36.2,1)


def mapped_corner_pavilions(b):
    """Four OSM source outlines, not bounding-box replacements or guessed buffers.

    Ways 178407323/328/330/333 share nodes with the main block. Their mapped
    ground footprints include the corner returns outside the central rectangle.
    Vertical elevations and depths still come from photographs, not OSM levels.
    """
    rows=[(9.65,3.25),(14.25,3.45),(18.65,3.45),(23.0,3.50)]
    for pavilion in MAPPED_PAVILIONS:
        points=pavilion['polygon'];center=pavilion['center']
        b.outline(points,0,1.55,5)
        for edge in pavilion_edges(pavilion):
            origin,n,width=edge['origin'],edge['normal'],edge['width']
            # Short shared-node returns are solid. Long walls contain full
            # recessed slots and a true upper arch on all four elevations.
            if width<4.5:
                thick_wall(b,origin,n,width,1.55,34.92,[])
                continue
            holes=[(-1,1,7.75,25.45),(-.975,.975,2.25,6.35),(-.75,.75,28.80,32.15)]
            thick_wall(b,origin,n,width,1.55,34.92,holes)
            inset_window(b,origin,n,0,4.30,1.65,3.90)
            for z,h in rows:inset_window(b,origin,n,0,z,1.66,h,outer_trim=False)
            span=7.75
            for z,h in rows+[(25.45,0)]:
                upper=z-h/2
                if upper>span:
                    oriented_box(b,origin,n,(0,-.39,(span+upper)/2),(1.86,.12,upper-span),4)
                    if upper-span>.45:
                        for a in [-.58,0,.58]:oriented_box(b,origin,n,(a,-.30,(span+upper)/2),(.045,.055,upper-span-.14),0)
                span=z+h/2
            arch_window(b,origin,n,0,28.80,31.40,.75)
            oriented_box(b,origin,n,(0,.15,32.60),(2.25,.40,.20),1)
            extruded_profile(b,origin,n,[(-1.22,32.70),(1.22,32.70),(0,33.32)],.25,.25,1)
            # Small horizontal masonry joints only on the flanking piers.
            for zz in [2.0+i*.65 for i in range(8)]+[8+i*1.55 for i in range(12)]+[29.1,30.3,31.5,33.9]:
                for lo,hi in [(-width/2,-1.06),(1.06,width/2)]:
                    if hi-lo>.1:oriented_box(b,origin,n,((lo+hi)/2,.006,zz),(hi-lo,.012,.022),3)
            for j in range(max(1,int(width/.94))):
                a=-width/2+.47+j*.94
                oriented_box(b,origin,n,(a,.22,26.65),(.40,.28,.78),1)
        for z,thick,factor in [(6.9,.45,1.025),(7.35,.25,1.03),(25.7,.30,1.025),(27.55,.58,1.06),(28.15,.25,1.04)]:
            poly=[(center[0]+(x-center[0])*factor,center[1]+(y-center[1])*factor) for x,y in points]
            b.outline(poly,z-thick/2,z+thick/2,1)
        # The opaque roof covers the exact mapped plan, including projecting
        # portions outside the original central 36.345 x 23.425m rectangle.
        b.outline(points,33.12,33.34,3)
        polygon_roof(b,points,center)
