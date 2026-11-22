"""Stone balustrades and the four slender square posts of the south veranda."""
from math import hypot

BOTTLE = "Veranda | pale turned stone"
CAP = "Veranda | weathered stone coping"
POST = "Veranda | warm dressed stone"
BASE = "Veranda | blue-grey plinth"
PALETTE = {
    BOTTLE: dict(color=[.70, .69, .64], roughness=.92),
    CAP: dict(color=[.61, .60, .55], roughness=.90),
    POST: dict(color=[.67, .62, .53], roughness=.93),
    BASE: dict(color=[.26, .27, .27], roughness=.96),
}

# Height above the bottom and radius are both fractions of the complete
# baluster height. The outer square neck and foot have their own sections.
TURNED = (
    (.070,.083), (.091,.080), (.108,.067), (.130,.060), (.155,.048),
    (.180,.044), (.207,.045), (.260,.052), (.330,.065), (.395,.081),
    (.438,.090), (.459,.091), (.476,.081), (.487,.074), (.500,.078),
    (.515,.089), (.531,.091), (.545,.083), (.555,.073), (.570,.078),
    (.580,.086), (.600,.088), (.643,.078), (.700,.067), (.767,.054),
    (.816,.045), (.862,.043), (.885,.045), (.907,.052), (.926,.069),
    (.950,.079), (.965,.081),
)
LOD_TURNED = tuple(TURNED[i] for i in (0,2,5,8,10,12,13,15,17,18,20,21,25,26,28,29,31))


def square_section(b, x, y, rings, mat, label):
    """Solid square moulding, shared end corners and outward winding."""
    vertices = [(x+sx*half, y+sy*half, z) for z,half in rings
                for sx,sy in ((-1,-1),(1,-1),(1,1),(-1,1))]
    faces = [(3,2,1,0), tuple(range(len(vertices)-4,len(vertices)))]
    for i in range(0,len(vertices)-4,4):
        for j in range(4):
            k=(j+1)%4
            faces.append((i+j,i+k,i+k+4,i+j+4))
    b.add(vertices,faces,mat,label)


def baluster(b, x, y, z, h, lod, label):
    profile = LOD_TURNED if lod else TURNED
    square_section(b,x,y,[(z,.098*h),(z+.059*h,.098*h),(z+.070*h,.091*h)],
                   BOTTLE,label+" foot")
    b.lathe((x,y),[(z+a*h,r*h) for a,r in profile],BOTTLE,
            segments=10 if lod else 18,label=label+" spindle")
    square_section(b,x,y,[(z+.965*h,.083*h),(z+.976*h,.096*h),
                          (z+h,.096*h)],BOTTLE,label+" neck")


def moulded_rail(b, p, q, z, half_widths, mat, label):
    dx,dy=q[0]-p[0],q[1]-p[1]
    length=hypot(dx,dy)
    nx,ny=-dy/length,dx/length
    vertices=[]
    for level,half in half_widths:
        for (x,y),sign in ((p,1),(p,-1),(q,-1),(q,1)):
            vertices.append((x+sign*nx*half,y+sign*ny*half,z+level))
    faces=[(3,2,1,0), tuple(range(len(vertices)-4,len(vertices)))]
    for i in range(0,len(vertices)-4,4):
        for j in range(4):
            k=(j+1)%4
            faces.append((i+j,i+k,i+k+4,i+j+4))
    b.add(vertices,faces,mat,label)


def spindle_fractions(run):
    if "first_fraction" in run:
        return [run["first_fraction"]+i*run["pitch_fraction"] for i in range(run["count"])]
    return [(i+.5)/run["count"] for i in range(run["count"])]


def rail(b, run, lod):
    p,q=run["p"],run["q"]
    sill,top=run["base"],run["top"]
    label=run["id"]
    moulded_rail(b,p,q,sill,[(0,.123),(.029,.123),(.041,.116)],
                 CAP,label+" sill")
    height=top-sill-.041-.094
    for i,f in enumerate(spindle_fractions(run)):
        x=p[0]+f*(q[0]-p[0]); y=p[1]+f*(q[1]-p[1])
        baluster(b,x,y,sill+.041,height,lod,label+" %02d"%(i+1))
    moulded_rail(b,p,q,top-.094,[(0,.105),(.019,.113),(.027,.129),
                  (.074,.129),(.094,.119)],CAP,label+" handrail")


def column(b, x, y, z, top, half, lod, label):
    square_section(b,x,y,[(z,half+.038),(z+.217,half+.038),
                          (z+.252,half+.014),(z+.269,half+.008)],
                   BASE,label+" plinth")
    # The visible joints are shallow square rustication. Horizontal joints
    # terminate at the edge of each post, including the shaded return.
    base=z+.269
    crown=top-.155
    count=8
    rings=[(base,half)]
    for i in range(1,count):
        joint=base+(crown-base)*i/count
        rings.extend([(joint-.005,half),(joint-.002,half-.009),
                      (joint+.002,half-.009),(joint+.005,half)])
    rings.append((crown,half))
    square_section(b,x,y,rings,POST,label+" coursed shaft")
    square_section(b,x,y,[(crown,half+.010),(crown+.023,half+.016),
                   (crown+.055,half+.047),(crown+.075,half+.047),
                   (crown+.090,half+.068),(top,half+.068)],CAP,label+" capital")


def member_positions(layout):
    edges=layout["bay_edges"]; fronts=layout["front_y"]
    lower=layout["landing_z"]; upper=layout["balcony_z"]
    post_specs=[]; runs=[]
    # End fractions of each free railing in the three separately recessed
    # facade planes. The wider masonry piers are supplied by the wall model.
    upper_runs=(
        ((.180,.535,7),(.608,.945,7)),
        ((.162,.268,3),(.336,.671,8),(.743,.846,3)),
        ((.040,.398,7),(.472,.812,7)),
    )
    floor_runs=((.3075,.8373,11),None,(.1265,.6178,10))
    for n,(left,right) in enumerate(zip(edges,edges[1:])):
        width=right-left
        front=fronts[n]
        cross=lambda f:left+width*f
        rows=list(upper_runs[n])
        if layout.get("garden_arches"):
            opened=layout["garden_arches"][n]["upper_clear_x"]
            a,z,k=rows[0];rows[0]=((opened[0]-.009-left)/width,z,k)
            a,z,k=rows[-1];rows[-1]=(a,(opened[1]+.009-left)/width,k)
        for j,(start,end,count) in enumerate(rows):
            row=dict(id="U%d.%d"%(n+1,j+1),p=(cross(start),front+.16),
                     q=(cross(end),front+.16),base=upper,top=upper+.90,count=count)
            if n==2 and j==0:
                # Opposite photographs 08/13 independently fix this run of seven.
                # Its end coping continues to the masonry independently of the shafts.
                row.update(p=(cross(start),front+.086965),q=(cross(end),front+.086965),
                           first_fraction=(.09929223-start)/(end-start),
                           pitch_fraction=.04609954/(end-start))
            runs.append(row)
        for j in range(len(rows)-1):
            start,end=rows[j][1],rows[j+1][0]
            half=(end-start)*width/2
            post_specs.append((cross((start+end)/2),front+half,upper,
                               layout["upper_soffit_z"],half,"P%d.%d"%(n+1,j+1)))
        if floor_runs[n]:
            start,end,count=floor_runs[n]
            runs.append(dict(id="L%d"%(n+1),p=(cross(start),front+.16),
                        q=(cross(end),front+.16),base=lower,top=lower+.75,count=count))
    x=edges[-1]-.17
    depth=layout["veranda_depth"]
    for label,z,h,start,end in (("LE",lower,.75,.526,.852),("UE",upper,.90,.41,.96)):
        end_y=fronts[2]+depth*end
        if label=="UE":
            # In photographs 09 and 13 the coping enters the rear wall.
            end_y=min(end_y,layout["rear_gallery_wall_y"]+.006)
        runs.append(dict(id=label,p=(x,fronts[2]+depth*start),
                    q=(x,end_y),base=z,top=z+h,count=4))
    return runs,post_specs


def add_railings(b,lod,layout):
    runs,posts=member_positions(layout)
    for run in runs:
        rail(b,run,lod)
    for x,y,z,top,half,label in posts:
        column(b,x,y,z,top,half,lod,label)
