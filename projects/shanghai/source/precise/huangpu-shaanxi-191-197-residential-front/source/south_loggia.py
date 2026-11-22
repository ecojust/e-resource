"""Photographed southern porch of the residence at 195 South Shaanxi Road."""
from functools import lru_cache
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon

from west_photo_plane import on_wall


MEASUREMENTS = Path(__file__).resolve().parents[1] / "measurements"


def mapped(uv,depth=0.):
    xyz=on_wall(*uv,y=depth,camera="2018_commons")
    return (xyz[0],xyz[2])


@lru_cache(maxsize=1)
def porch_openings():
    """The two actual holes in the photographed street wall, in X,Z metres."""
    arch=json.loads((MEASUREMENTS/"south-porch-arch-trace.json").read_bytes())
    # Angle decreases from pi to zero. The two feet disappear behind the
    # boundary wall. Continue their photographed jamb alignment down to grade.
    arc=[mapped(row["inner_px"]) for row in arch["samples"]]
    lower=Polygon([*arc,(arc[-1][0],.15),(arc[0][0],.15)])
    upper=json.loads((MEASUREMENTS/"south-porch-upper-opening.json").read_bytes())
    return lower,Polygon([mapped(pt)for pt in upper["corners_clockwise_px"]])

from shapely.geometry import box
from shapely.ops import unary_union
from west_photo_plane import matrix
from west_upper_windows import paint

RIM = "Shaanxi porch smooth warm plaster edge"
INSIDE = "Shaanxi porch shaded lime lining"
CEILING = "Shaanxi porch warm grey soffit"
SHELTER = "Sheltered lime face inside the Shaanxi arcade"
IRON = "Shaanxi porch dark painted rail"
METAL = "Shaanxi porch pendant oxidized caps"
GLASS = "Shaanxi porch milk glass lamp bowls"
SILL = "Shaanxi porch grey cast sill"
MORTAR = "Shaanxi porch pale lime pointing"
BRICK = ("Shaanxi porch russet quoins","Shaanxi porch muted red quoins","Shaanxi porch burnt brick ends")
PALETTE = {RIM:paint((191,178,151),.93),INSIDE:paint((163,151,129),.95),CEILING:paint((163,154,139),.94),
           SHELTER:paint((100,89,73),.95),IRON:paint((48,47,40),.70,.18),METAL:paint((53,52,47),.62,.25),
           GLASS:paint((188,189,175),.43,.02),SILL:paint((114,114,107),.89),MORTAR:paint((169,151,130),.96)}
for name,rgb in zip(BRICK,[(143,99,82),(132,90,78),(152,108,88)]):
    PALETTE[name]=paint(rgb,.91)


def plate(b, shape, front, rear, mat, label):
    if not shape.is_empty and shape.area>1.e-6:
        b.prism(shape,-rear,-front,lambda x,z,d:(x,-d,z),mat,label)


def solid_box(b,left,right,front,rear,bottom,top,mat,label):
    b.box([(left+right)/2,(front+rear)/2,(bottom+top)/2],
          [right-left,rear-front,top-bottom],mat,label=label)


def edge_strip(b,inner,outer,front,rear,mat,label):
    """Form a continuous strip with a front bevel following the photographed curve."""
    verts=[]
    for a,c in zip(inner,outer):
        verts.extend([(a[0],front,a[1]),(c[0],rear,c[1]),
                      (c[0],rear+.055,c[1]),(a[0],front+.055,a[1])])
    faces=[]
    for j in range(len(inner)-1):
        a=4*j
        for k in range(4):
            h=(k+1)%4
            faces.append((a+k,a+4+k,a+4+h,a+h))
    faces.extend([(0,1,2,3),tuple(range(len(verts)-1,len(verts)-5,-1))])
    # A strip can turn either way around the lower jambs. Choose outward
    # winding from its signed volume in the same Cartesian frame as the mesh.
    vv=np.array(verts)
    volume=sum(vv[f[0]]@np.cross(vv[f[k]],vv[f[k+1]]) for f in faces for k in range(1,len(f)-1))
    if volume<0:faces=[tuple(reversed(f)) for f in faces]
    b.add(verts,faces,mat,label)


def plain_returns(b):
    record=json.loads((MEASUREMENTS/"south-porch-arch-trace.json").read_bytes())
    inner=[mapped(v["inner_px"]) for v in record["samples"]]
    outer=[mapped(v["outer_px"]) for v in record["samples"]]
    for curve in (inner,outer):
        curve.insert(0,(curve[0][0],.15))
        curve.append((curve[-1][0],.15))
    edge_strip(b,inner,outer,-.024,-.006,RIM,"Street porch narrow smooth-plaster arch rim and jambs")
    lower,upper=porch_openings()
    # These linings show the real wall thickness from the front. Their inner
    # surface is visible through the holes cut by the wall builder.
    for name,opening,depth in [("Ground arched entry",lower,.295),("Upper square loggia",upper,.22)]:
        shell=opening.buffer(.023,join_style=2).difference(opening.buffer(-.001))
        # The ground entry intrados is shaded behind the thin light rim.
        # Its front-reveal rays stop before reaching the side arcade.
        finish=SHELTER if name=="Ground arched entry" else INSIDE
        plate(b,shell,.002,depth,finish,name+" inward plastered reveals")
    plate(b,upper.buffer(.047,join_style=2).difference(upper),-.019,.04,RIM,"Upper opening narrow rectangular plaster edge")
    x0,z0,x1,_=upper.bounds
    solid_box(b,x0-.105,x1+.088,-.126,.228,z0-.096,z0-.032,SILL,"Upper loggia grey sill apron")
    solid_box(b,x0-.124,x1+.107,-.156,.20,z0-.032,z0+.007,SILL,"Upper loggia moulded sill nose")


def tooth_jambs(b):
    data=json.loads((MEASUREMENTS/"south-porch-toothed-jambs.json").read_bytes())
    for g in data["jambs"]:
        for i,c in enumerate(g["courses"]):
            left,right=c["left_native_u"],c["right_native_u"]
            z0,z1=c["top_native_v"],c["bottom_native_v"]
            face=lambda l,r,t,bot:Polygon([mapped([l,t]),mapped([r,t]),mapped([r,bot]),mapped([l,bot])])
            label=f"{g['level']} stepped red jamb course {i+1:02d}"
            plate(b,face(left,right,z0,z1),-.009,.018,MORTAR,label+" mortar")
            cuts=[left,*c["vertical_joint_u"],right]
            for j,(a,h) in enumerate(zip(cuts,cuts[1:])):
                plate(b,face(a+(.4 if j else 0),h-(.4 if j<len(cuts)-2 else 0),
                             z0+.65,z1-.65),-.019-.0006*((i+j)%3),-.005,
                      BRICK[(i*3+j*7+i//4)%3],label+f" red face {j+1}")


def side_wall(b, rectangular, side_x, bays, bottom, top, depth_limit, lod):
    """Build the visible southern return, including the thickness of each side opening."""
    outline=box(.10,bottom,depth_limit,top)
    if rectangular:
        holes=[box(a,bottom+.04,z,top-.16) for a,z in bays]
    else:
        observed=json.loads((MEASUREMENTS/"south-porch-side-arches.json").read_bytes())
        holes=[]
        for feature in observed["arches"]:
            center=feature["centre_y_m"]
            ry,rz=feature["radius_y_m"],feature["radius_z_m"]
            spring=feature["spring_z_m"]
            th=np.linspace(np.pi,0,33 if lod else 65)
            curve=[(center+ry*np.cos(t),spring+rz*np.sin(t)) for t in th]
            holes.append(Polygon([*curve,(center+ry,bottom-.04),(center-ry,bottom-.04)]))
        # Beyond the independently triangulated middle pier, retain only the
        # far arched shoulder actually visible from the front in 2018. The
        # unconstrained rear of the house is outside the surveyed fragment.
        eye=-np.linalg.solve(matrix()[:,:3],matrix()[:,3])
        def side_cut(x,z):
            return (eye[1]+(side_x-eye[0])*(0.-eye[1])/(x-eye[0]),
                    eye[2]+(side_x-eye[0])*(z-eye[2])/(x-eye[0]))
        frontage=porch_openings()[0]
        visible=Polygon([side_cut(x,z)for x,z in frontage.exterior.coords]).buffer(.08)
        outline=outline.intersection(box(0.,bottom,2.83,top).union(visible))
    shape=outline.difference(unary_union(holes))
    tag="Upper gallery" if rectangular else "Lower side arcade"
    # Side-wall thickness of approximately 0.32 m is consistent with the
    # offset of the small daylight gaps from both arched intradoses.
    b.prism(shape,side_x,side_x+.32,lambda y,z,x:(x,y,z),INSIDE,tag+" pale intrados and outer return")
    # The shaded inside face is consistently much darker than the curved
    # reveal in the original. Give this recessed surface its own finish.
    if not rectangular:
        b.prism(shape,side_x-.003,side_x+.001,lambda y,z,x:(x,y,z),SHELTER,tag+" sheltered face")


def bowed_grille(b,lod,return_end):
    fit=json.loads((MEASUREMENTS/"south-porch-fittings.json").read_bytes())["front_rail"]
    depth=.084
    def point(u,v):return np.array(on_wall(u,v,depth))
    us=fit["uprights_at_native_v_1300"];x0=mapped([2707,1300])[0];x1=mapped([2924,1300])[0]
    zvals={k:float(point(2815,fit[k])[2]) for k in ("top_native_v","inner_cross_rail_native_v","lower_cross_rail_native_v","foot_rail_native_v")}
    ztop=zvals["top_native_v"];zbot=zvals["foot_rail_native_v"];n=6 if lod else 10
    for k,z in zvals.items():
        r=.016 if k=="top_native_v" else .009
        b.tube([[x0,depth,z],[x1,depth,z]],r,IRON,n,"Upper loggia front rail "+k)
    xs=[float(point(u,1300)[0]) for u in us]
    for i,x in enumerate(xs):
        b.tube([[x,depth,zbot],[x,depth,ztop]],.009,IRON,n,f"Upper front iron upright {i+1}")
    for i,x in enumerate(xs[:-1]):
        gap=xs[i+1]-x
        # Small curved ties between the foot rail and the lower cross rail
        # can be read in the unobstructed central portion of the 2018 original.
        if i not in (1,3,5,7):continue
        t=np.linspace(0,1,7 if lod else 13)
        v=[[x+gap*(.16+.70*s),depth+.003,zbot+.012+(zvals["lower_cross_rail_native_v"]-zbot-.012)*(1-s)**2]for s in t]
        b.tube(v,.0065,IRON,n,f"Upper front curved foot tie {i+1}")
    # The sloping apparent top in the street photo belongs to the horizontal
    # side return running inward towards the second square pier.
    for a,h in return_end:
        x=5.966
        for z,r in [(ztop,.017),(zvals["lower_cross_rail_native_v"],.009),(zbot,.013)]:
            b.tube([[x,a,z],[x,h,z]],r,IRON,n,"South side iron gallery rail")
        for i,y in enumerate(np.linspace(a,h,max(3,round((h-a)/.136)+1))):
            b.tube([[x,y,zbot],[x,y,ztop]],.009,IRON,n,"South side gallery upright "+str(i+1))


def add_lamps(b,lod):
    data=json.loads((MEASUREMENTS/"south-porch-fittings.json").read_bytes())
    p=matrix("2018_commons");eye=-np.linalg.solve(p[:,:3],p[:,3]);cx=5.40
    for light in data["lights"]:
        u=light["centre_u"];profile=light["profiles_v_radius_px"]
        ray=np.linalg.solve(p[:,:3],[u,np.median([v for v,_ in profile]),1.])
        middle=eye+(cx-eye[0])/ray[0]*ray;depth=float(middle[1]);rings=[]
        for v,radius in profile:
            c=on_wall(u,v,depth);left=on_wall(u-radius,v,depth);right=on_wall(u+radius,v,depth)
            rings.append((c[2],(right[0]-left[0])/2))
        groups=[(0,light['metal_to_index'],METAL,"metal ceiling fitting and lip"),
                (light['metal_to_index'],light['finial_from_index'],GLASS,"frosted pendant bowl"),
                (light['finial_from_index'],len(rings)-1,METAL,"small dark finial")]
        n=16 if lod else 36
        if light["level"]=="ground":
            # The street arch hides the upper part of the lower suspension.
            # Continue its measured axis to the underside of the gallery slab.
            b.tube([[cx,depth,rings[0][0]-.002],[cx,depth,4.451]],.008,METAL,8 if lod else 14,
                   "Ground porch pendant suspension to ceiling")
        for a,z,mat,title in groups:
            rv=rings[a:z+1];v=[(cx+r*np.cos(ang),depth+r*np.sin(ang),h)for h,r in rv for ang in np.arange(n)*2*np.pi/n]
            # The recorded profile runs top to bottom.
            f=[tuple(range(n)),tuple(range(len(v)-1,len(v)-n-1,-1))]
            for i in range(len(rv)-1):
                for j in range(n):
                    q=(j+1)%n;f.append((i*n+j,(i+1)*n+j,(i+1)*n+q,i*n+q))
            b.add(v,f,mat,light["level"]+" porch lamp "+title)


def add_south_loggia(b,lod=False):
    plain_returns(b)
    tooth_jambs(b)
    upper=[(.24,2.03),(2.50,4.03)]
    study=json.loads((MEASUREMENTS/"south-porch-side-arches.json").read_bytes())
    depth=study["upper_limit_m"]
    side_wall(b,False,study["assumed_south_inner_x_m"],[],.14,4.46,study["visible_side_limit_m"],lod)
    side_wall(b,True,5.964,upper,4.72,7.135,depth,lod)
    # Only the portions of the passage ceiling and floor visible through the
    # street and side openings are included.
    solid_box(b,4.70,6.22,.08,depth,4.45,4.73,CEILING,"Upper loggia floor over ground arcade")
    solid_box(b,4.70,6.22,.09,depth,7.135,7.215,CEILING,"Cream ceiling of the upper loggia")
    solid_box(b,4.70,6.22,.09,depth,.12,.15,INSIDE,"Visible ground porch floor")
    bowed_grille(b,lod,[(a,min(z,depth)) for a,z in upper if a<depth])
    add_lamps(b,lod)
