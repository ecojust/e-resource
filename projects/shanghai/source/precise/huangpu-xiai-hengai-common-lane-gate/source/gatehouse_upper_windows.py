"""Street-facing casements above the shared passage of Xiai Village and Hengai Lane."""
import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np

from yongjia_photo_plane import CALIBRATION

MEASUREMENTS=Path(__file__).resolve().parents[1]/"measurements"
CASING="Yongjia gatehouse | pale mineral window surround"
LEDGE="Yongjia gatehouse | weathered sill and cap"
TIMBER="Yongjia gatehouse | dark brown outer sash"
BAR="Yongjia gatehouse | narrow dark cross rail"
BEAD="Yongjia gatehouse | glazing bead"
GLASS="Yongjia gatehouse | cool reflected upper glass"
LOWER="Yongjia gatehouse | muted lower glazing"
SHADOW="Yongjia gatehouse | shade observed through the opening"
CANOPY="Yongjia gatehouse | dark weathered sheet sunshade"


def paint(values,roughness,metallic=0.0):
    val=np.array(values,dtype=float)/255
    return {"color":np.where(val<.04045,val/12.92,((val+.055)/1.055)**2.4).tolist(),
            "roughness":roughness,"metallic":metallic}


PALETTE={CASING:paint((164,157,141),.84),LEDGE:paint((134,125,112),.82),
         TIMBER:paint((56,42,39),.60),BAR:paint((55,44,40),.53,.1),
         BEAD:paint((87,77,65),.60),GLASS:paint((79,91,103),.28,.25),
         LOWER:paint((62,72,78),.29,.23),SHADOW:paint((45,43,41),.91),
         CANOPY:paint((70,71,65),.73,.12)}


@lru_cache(maxsize=1)
def openings():
    coords=CALIBRATION["observed_windows"]
    picks=json.loads((MEASUREMENTS/"upper-casement-reads.json").read_text())["leaf_edges"]
    return tuple({"key":k,"label":k+" upper casement","left":coords[k+"TL"][0],
                  "right":coords[k+"TR"][0],"bottom":coords[k+"BL"][2],"top":coords[k+"TL"][2],
                  "depths":[.103,.103] if k=="left" else [picks[t]["hinge_depth_m"] for t in picks],
                  "angles":[0.,0.] if k=="left" else [picks[t]["angle_degrees"] for t in picks]}
                 for k in ("left","right"))


def box(builder,x0,x1,y0,y1,z0,z1,material,label):
    builder.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=label)


def molding(builder,l,r,profile,material,label):
    """Sweep a single clockwise y/z profile across the width with closed end caps."""
    verts=[(x,y,z) for x in (l,r) for y,z in profile]
    n=len(profile)
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((a,(a+1)%n,(a+1)%n+n,a+n) for a in range(n))
    p=np.asarray(profile)
    if np.sum(p[:,0]*np.roll(p[:,1],-1)-np.roll(p[:,0],-1)*p[:,1])<0:
        faces=[tuple(reversed(face)) for face in faces]
    builder.add(verts,faces,material,label)


def leaf_axes(row,index):
    a=math.radians(row["angles"][index])
    sign=1 if index==0 else -1
    along=np.array([sign*math.cos(a),-math.sin(a),0.])
    inward=np.array([sign*math.sin(a),math.cos(a),0.])
    hinge=np.array([row["left"]+.023 if index==0 else row["right"]-.023,row["depths"][index],0.])
    return hinge,along,inward


def leaf_parts(builder,row,index,lod):
    hinge,along,inward=leaf_axes(row,index);up=np.array([0.,0.,1.])
    l,r,z0,z1=[row[k] for k in ("left","right","bottom","top")]
    width=(r-l)/2-.026;bottom=z0+.028;top=z1-.030;stile=.032
    pre=row["key"]+(" | left leaf " if index==0 else " | right leaf ")
    def block(a,b,front,back,low,high,mat,tag):
        center=hinge+along*((a+b)/2)+inward*((front+back)/2)+up*((low+high)/2)
        builder.box(center,(b-a,back-front,high-low),mat,basis=[along,inward,up],label=pre+tag)
    block(0,stile,-.018,.022,bottom,top,TIMBER,"hinge stile")
    block(width-stile,width,-.018,.022,bottom,top,TIMBER,"meeting stile")
    bands=[(bottom,bottom+.045,TIMBER),(top-.040,top,TIMBER)]
    for pos in (.248,.500,.755):
        z=bottom+(top-bottom)*pos
        bands.append((z-.012,z+.012,BAR))
    bands.sort()
    for i,(a,b,mat) in enumerate(bands):
        block(stile,width-stile,-.015,.019,a,b,mat,f"rail {i+1}")
    for i in range(len(bands)-1):
        a,b=bands[i][1],bands[i+1][0];gap=.005 if lod=="full" else 0.
        if gap:
            for x in (stile,width-stile-gap):
                block(x,x+gap,-.005,.003,a,b,BEAD,f"pane {i+1} upright rebate")
            for z in (a,b-gap):
                block(stile+gap,width-stile-gap,-.005,.003,z,z+gap,BEAD,f"pane {i+1} end rebate")
        block(stile+gap,width-stile-gap,.003,.010,a+gap,b-gap,GLASS if i>=2 else LOWER,f"light {i+1}")


def add_windows(builder,lod):
    # Whole-building callers pass a boolean, while the standalone export names the two levels.
    lod = "lod" if lod is True else "full" if lod is False else lod
    if lod not in ("full","lod"):
        raise ValueError("Expected a named or boolean level of detail")
    for row in openings():
        l,r,z0,z1=[row[k] for k in ("left","right","bottom","top")]
        prefix=row["key"]+" upper window | "
        # The light surround is flush to the surrounding plaster at its rear edge.
        for a,b in ((l-.129,l),(r,r+.123)):
            box(builder,a,b,-.042,.055,z0,z1,CASING,prefix+"outer stone jamb")
        molding(builder,l-.129,r+.123,[(-.071,z1),(.055,z1),(.055,z1+.113),
                (-.060,z1+.113),(-.071,z1+.100)],CASING,prefix+"cap with weathered arris")
        molding(builder,l-.160,r+.146,[(-.115,z0-.010),(-.111,z0-.069),
                (-.078,z0-.086),(.103,z0-.086),(.103,z0+.004)],LEDGE,prefix+"sloping sill")
        for a,b in ((l,l+.024),(r-.024,r)):
            box(builder,a,b,.044,.146,z0,z1,TIMBER,prefix+"inset rebate jamb")
        box(builder,l+.024,r-.024,.044,.146,z1-.025,z1,TIMBER,prefix+"inset rebate head")
        if row["key"]=="right":
            # Shaded return surfaces terminate at the observed recess; no room is depicted.
            for a,b in ((l+.013,l+.024),(r-.024,r-.013)):
                box(builder,a,b,.137,.422,z0+.008,z1-.007,SHADOW,prefix+"shaded opening return")
            box(builder,l+.024,r-.024,.139,.422,z1-.023,z1-.007,SHADOW,prefix+"shaded head return")
            box(builder,l+.024,r-.024,.139,.422,z0+.005,z0+.018,SHADOW,prefix+"shaded sill return")
            box(builder,l+.019,r-.019,.405,.425,z0+.008,z1-.019,SHADOW,prefix+"shaded visible recess")
        for index in (0,1):leaf_parts(builder,row,index,lod)
        if row["key"]=="left":
            roof=z1+.175
            profile=[(-.345,roof-.061),(-.345,roof-.089),(-.317,roof-.089),(.025,roof-.023),(.025,roof)]
            molding(builder,l-.185,r+.162,profile,CANOPY,prefix+"projecting thin canopy")
            for n,f in enumerate((.09,.315,.555,.805,.92)):
                x=l+(r-l)*f
                molding(builder,x-.006,x+.006,[(-.326,roof-.071),(.008,roof-.010),(.008,roof+.002),(-.326,roof-.060)],CANOPY,prefix+f"canopy standing seam {n+1}")
