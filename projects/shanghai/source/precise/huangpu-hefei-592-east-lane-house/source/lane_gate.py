"""The paired masonry piers, open iron leaves and enamel address plate of Hefei Lane 592."""
from functools import lru_cache
import json
from pathlib import Path
import sys

import numpy as np
from shapely import affinity
from shapely.geometry import box

from west_gable_shutters import finish
from lane_paving import PALETTE as PAVEMENT, add_paving

SOURCE = Path(__file__).resolve().parent
COMMON = SOURCE.parents[1] / "hongkou-general-post-office/source/common"
sys.path.insert(0, str(COMMON))
from sign_lettering import lettering_shapes

PLASTER = "Hefei lane | warm pier plaster"
CAP = "Hefei lane | pale cast pier caps"
BAND = "Hefei lane | shaded cap and wall coping"
PLINTH = "Hefei lane | blue-grey outer plinth"
MORTAR = "Hefei lane | lime joints"
BRICKS = ("Hefei lane | terracotta end", "Hefei lane | warm red end", "Hefei lane | dark red end")
IRON = "Hefei lane | black painted ironwork"
ENAMEL = "Hefei lane | green enamel number sign"
LETTER = "Hefei lane | off-white enamel lettering"
EDGE = "Hefei lane | folded metal sign edge"
PALETTE = {
    **PAVEMENT,
    PLASTER: finish((184,177,156),.94), CAP: finish((197,194,181),.91),
    BAND: finish((141,144,138),.90), PLINTH: finish((100,114,120),.93),
    MORTAR: finish((160,146,128),.96), IRON: finish((43,46,45),.63,.35),
    ENAMEL: finish((23,105,84),.38,.08), LETTER: finish((220,223,196),.48),
    EDGE: finish((67,81,72),.55,.28),
}
PALETTE.update({m: finish(c,.91) for m,c in zip(BRICKS,[(148,87,64),(164,96,70),(133,79,63)])})
UP = np.array([0.,0.,1.])


@lru_cache(maxsize=1)
def survey():
    return json.loads((SOURCE.parent/"measurements/hefei-lane-gate-survey.json").read_text())


def xy_axis(direction):
    axis = np.array([*direction,0.])
    return axis / np.linalg.norm(axis)


def pier_frames():
    """Origins are the left end of the street-facing shaft skin at local z=0."""
    points = {k:np.array(v["xyz_m"]) for k,v in survey()["features"].items()}
    west_axis = xy_axis((points["west plate TR"]-points["west plate TL"])[:2])
    west_corner = points["west red street corner foot"] * [1.,1.,0.]
    east_corner = points["east red corner foot"] * [1.,1.,0.]
    return [
        ("West address pier",west_corner-west_axis*.735,west_axis,.735,.64,.569,3.121,"right"),
        ("East entrance pier",east_corner,xy_axis([.78,-.085]),.765,.63,.527,3.116,"left"),
        ("West flanking pier",np.array([-6.41,-2.34,0.]),xy_axis([1.,-.08]),.48,.46,.57,3.05,"both"),
        ("East flanking pier",np.array([2.04,-3.68,0.]),xy_axis([1.,-.065]),.49,.47,.46,2.98,"both"),
    ]


def local_frame(origin,axis):
    inland = np.cross(UP,axis)
    def mapped(x,y,z):
        return origin + axis*x + inland*y + UP*z
    return inland,mapped


def moulded_cap(b,mapped,w,d,head,prefix):
    # The broad cast coping has a fillet, a projecting drip, a ledge and a
    # shallow hipped top. Its square lower rings remain separate editable skins.
    profile = [(head-.028,.018),(head+.018,.029),(head+.044,.060),
               (head+.092,.072),(head+.108,.059),(head+.125,.102),(head+.164,.104)]
    for i,((z0,o0),(z1,o1)) in enumerate(zip(profile,profile[1:])):
        v = [mapped(x,y,z) for z,o in [(z0,o0),(z1,o1)]
             for x,y in [(-o,-o),(w+o,-o),(w+o,d+o),(-o,d+o)]]
        b.add(v,[(0,3,2,1),(4,5,6,7),*( (j,(j+1)%4,4+(j+1)%4,4+j) for j in range(4))],
              BAND if i in (0,3) else CAP,prefix+f" cap moulding {i+1}")
    z,h=profile[-1]
    v=[mapped(x,y,z)for x,y in [(-h,-h),(w+h,-h),(w+h,d+h),(-h,d+h)]]
    v.append(mapped(w*.51,d*.51,head+.335))
    b.add(v,[(0,3,2,1),*((j,(j+1)%4,4) for j in range(4))],CAP,prefix+" shallow four-sided cap")


def pier(b,row,lod):
    label,org,axis,w,d,base,head,edge=row
    inland,at=local_frame(org,axis)
    def block(x,y,z,dx,dy,dz,material,title):
        b.box(at(x,y,z),[dx,dy,dz],material,[axis,inland,UP],label+" "+title)
    block(w/2,d/2,(base+head)/2,w,d,head-base,PLASTER,"plastered shaft")
    moulded_cap(b,at,w,d,head,label)
    # The west address pier's exposed red corner terminates above the foot.
    # Both red arrises of each outer fence post are visible in the street views.
    red_base=base+.69 if label.startswith("West address") else base+.018
    height=.0611
    courses=int(round((head-red_base)/height))
    step=(head-red_base)/courses
    for side in (["left","right"] if edge=="both" else [edge]):
        side_sign = -1 if side=="left" else 1
        x=w if side_sign==1 else 0.
        center_z=(head+red_base)*.5
        block(x-side_sign*.039,-.002,center_z,.078,.014,head-red_base,MORTAR,side+" arris joints")
        block(x+side_sign*.002,.038,center_z,.014,.076,head-red_base,MORTAR,side+" return joints")
        for i in range(courses):
            z=head-(i+.5)*step
            a,breadth=(.095,.057) if i%2==0 else (.054,.100)
            material=BRICKS[(i//3+i)%3]
            block(x-side_sign*a/2,-.009,z,a,.025,step-.006,material,f"{side} face brick {i+1:02d}")
            block(x+side_sign*.009,breadth/2,z,.024,breadth,step-.006,
                  material,f"{side} return brick {i+1:02d}")


def number_sign(b):
    f=survey()["features"]
    left,right=(np.array(f[k]["xyz_m"]) for k in ("west plate TL","west plate TR"))
    w=np.linalg.norm((right-left)[:2]);h=left[2]-f["west plate BL"]["xyz_m"][2]
    axis=xy_axis((right-left)[:2]);normal=np.cross(axis,UP)
    center=(left+right)/2-UP*h/2
    def at(x,z,d):
        return center+axis*x+UP*z+normal*d
    shape=box(-w/2+.006,-h/2+.006,w/2-.006,h/2-.006).buffer(.006,quad_segs=4)
    b.prism(shape,-.010,.002,at,EDGE,"Folded rim of green lane number plate")
    b.prism(shape.buffer(-.003),.001,.005,at,ENAMEL,"Green enamel street address plate")
    # At 2015 pixel scale 592弄 occupies roughly the left half of the upper row.
    # Smaller marks visible to its right and below cannot be securely read.
    for char,glyph in lettering_shapes("592弄",w*.465,h*.41,font=SOURCE/"fonts/HefeiLaneAddress.otf"):
        form=affinity.translate(glyph,xoff=-w*.214,yoff=h*.144)
        b.prism(form,.0048,.0061,at,LETTER,"Enamel lane number "+char)


def sweep_wall(b,path,bottom,top,width,material,title):
    xy=np.asarray(path);t=np.gradient(xy,axis=0);t/=np.linalg.norm(t,axis=1)[:,None]
    normals=np.column_stack([-t[:,1],t[:,0]])
    v=[]
    for p,n in zip(xy,normals):
        for s,z in [(1,bottom),(-1,bottom),(-1,top),(1,top)]:
            v.append([*(p+s*n*width/2),z])
    # Path is directed left-to-right. The outward winding follows each section.
    f=[(0,1,2,3)]
    for i in range(len(path)-1):
        for j in range(4):
            k=(j+1)%4;f.append((4*i+j,4*i+4+j,4*i+4+k,4*i+k))
    end=4*(len(path)-1);f.append((end+3,end+2,end+1,end))
    b.add(v,f,material,title)


def rail_screens(b,rows,lod):
    left,right,outer_west,outer_east=rows
    for label,pts,zbase in [
        ("West curved screen",[[-5.94,-2.32],[-4.66,-2.35],[-4.38,-1.56],[-4.15,-1.22]],.57),
        ("East curved screen",[[.40,-1.79],[.56,-2.82],[1.09,-3.52],[2.12,-3.60]],.50)]:
        # Cubic through the observed bow, with a horizontal nose on its street end.
        t=np.linspace(0.,1.,17 if lod else 41)[:,None];a,c,d,e=np.asarray(pts)
        xy=(1-t)**3*a+3*t*(1-t)**2*c+3*t*t*(1-t)*d+t**3*e
        for suffix,lo,hi,width,mat in [("blue-grey base",0,.46,.22,PLINTH),("warm plaster wall",.46,.83,.216,PLASTER),
                                      ("projecting stone edge",.83,.877,.254,BAND),("stone coping",.877,.903,.243,CAP)]:
            sweep_wall(b,xy,zbase+lo,zbase+hi,width,mat,label+" "+suffix)
        for z,r in [(1.00,.014),(1.22,.012),(2.17,.014)]:
            b.tube([[*p,zbase+z] for p in xy],r,IRON,6 if lod else 9,label+" horizontal iron rail")
        length=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(xy,axis=0),axis=1))]
        for i,s in enumerate(np.linspace(.01,length[-1]-.01,round(length[-1]/.123)+1)):
            x,y=np.interp(s,length,xy[:,0]),np.interp(s,length,xy[:,1])
            b.tube([[x,y,zbase+.881],[x,y,zbase+2.32]],.010,IRON,6 if lod else 9,label+f" upright {i+1}")
            # Separate slender points above the top rail are visible in the street photograph.
            bottom=zbase+2.31
            verts=[(x+.017,y,bottom),(x,y+.017,bottom),(x-.017,y,bottom),(x,y-.017,bottom),
                   (x,y,bottom+.093)]
            b.add(verts,[(0,3,2,1),*((k,(k+1)%4,4) for k in range(4))],
                  IRON,label+f" pointed finial {i+1}")


def open_leaves(b,lod):
    # The broad west leaf and narrow east leaf have different widths. Their
    # measured upper spans total about three metres against a 3.07 m gate throat.
    for o in survey()["open_leaves"]:
        label=o["name"];hinge=np.asarray(o["hinge_xy_m"]);tip=np.asarray(o["free_top_xy_m"])
        foot=np.asarray(o["free_lower_xy_m"]);top=o["top_z"];head=o["under_head_z"]
        base=o["base_z"];band=o["pierced_band_bottom_z"];high=o["pierced_band_top_z"]
        sides=6 if lod else 10
        def rod(a,z0,c,z1,r,title):
            b.tube([[*a,z0],[*c,z1]],r,IRON,sides,label+" "+title)
        for z in [top,head]:
            rod(hinge,z,tip,z,.016,"projecting upper frame")
        for i,y in enumerate(o["upper_bar_plane_y_m"]):
            xy=np.array([hinge[0],y])
            rod(xy,head,xy,top,.015 if i in (0,o["upper_bar_intervals"]) else .009,
                f"upper upright {i+1}")
        for z in [base+.02,band,high]:
            rod(hinge,z,foot,z,.018,"lower frame rail")
        ys=o.get("lower_bar_plane_y_m",np.linspace(hinge[1],foot[1],o["lower_bar_intervals"]+1))
        for i,y in enumerate(ys):
            xy=np.array([hinge[0],y])
            r=.017 if i in (0,o["lower_bar_intervals"]) else .010
            rod(xy,base+.02,xy,band,r,f"lower upright {i+1}")
            rod(xy,high,xy,head,r,f"upper length of lower upright {i+1}")
        # The broad band around hand height has two opposed diagonal runs in
        # the close west photograph. Its edge frame stays open through the centre.
        rod(hinge,band,hinge,high,.017,"band hinge edge")
        rod(foot,band,foot,high,.017,"band free edge")
        for i in range(o["band_lights"]):
            a=hinge+(foot-hinge)*i/o["band_lights"];c=hinge+(foot-hinge)*(i+1)/o["band_lights"]
            mid=(a+c)/2;z=(band+high)/2
            for j,(a0,za,a1,zb) in enumerate([(a,z,mid,high),(mid,high,c,z),(c,z,mid,band),(mid,band,a,z)]):
                rod(a0,za,a1,zb,.0075,f"open band lozenge {i+1} edge {j+1}")
        for i,h in enumerate((base+.41,head-.11)):
            rod(hinge,h-.045,hinge,h+.045,.032,f"hinge knuckle {i+1}")


def add_lane_gate(builder,lod=False):
    add_paving(builder,lod)
    rows=pier_frames()
    for row in rows:
        pier(builder,row,lod)
    rail_screens(builder,rows,lod)
    open_leaves(builder,lod)
    number_sign(builder)
