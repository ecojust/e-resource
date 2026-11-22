"""Three window openings in the gable on the east side of the entrance to Hefei Lane 592."""
from functools import lru_cache
import json
import math
from pathlib import Path

import numpy as np

TIMBER = "Hefei gable | weathered red-brown shutter framing"
BLADES = "Hefei gable | red-brown timber blades"
BACK = "Hefei gable | pale back of swung shutters"
DARK = "Hefei gable | dark inset timber sash"
GLASS = "Hefei gable | shaded window glass"
SHADE = "Hefei gable | dark exterior gap behind shut timber"
STONE = "Hefei gable | painted stone sill"
EDGE = "Hefei gable | darker underside of sill"


def finish(rgb, roughness, metallic=0.0):
    c = [v / 255 for v in rgb]
    return {"color": [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in c],
            "roughness": roughness, "metallic": metallic}


PALETTE = {TIMBER: finish((99,63,57),.76), BLADES: finish((110,71,64),.73),
           BACK: finish((145,128,108),.85), DARK: finish((54,55,49),.75),
           GLASS: finish((48,61,59),.30,.12), STONE: finish((188,183,167),.84),
           EDGE: finish((159,153,140),.86), SHADE:finish((45,39,36),.95)}


@lru_cache(maxsize=1)
def side_openings():
    path = Path(__file__).resolve().parents[1]/"measurements"/"west-gable-apertures.json"
    return tuple(json.loads(path.read_text())["rows"])


def axes(row, inland):
    """Normal and hinge-to-tip unit vectors for each photographed leaf."""
    angle = math.radians(row["inward_leaf_angle_deg"] if inland else 0.0)
    direction = np.array([-math.sin(angle), -math.cos(angle) if inland else 1.0, 0.0])
    inward = np.array([-direction[1] if inland else direction[1],
                        direction[0] if inland else -direction[0], 0.0])
    return inward, direction, np.array([0.,0.,1.])


def leaf(builder, row, inland, lod):
    n, d, v = axes(row,inland)
    hinge_y = row["back_y"]-.020 if inland else row["front_y"]+.020
    hinge = np.array([-.023,hinge_y,0.])
    z0,z1 = row["bottom"]+.030,row["top"]-.030
    width = (row["back_y"]-row["front_y"])/2-.024
    stile = .035 if width < .44 else .040
    low,high = z0+.065, z0+.701*(z1-z0)
    raised = row["inward_leaf_angle_deg"] > 0 and inland
    wood = BACK if raised else TIMBER
    blade = BACK if raised else BLADES
    prefix = row["key"] + (" | inland leaf " if inland else " | street leaf ")
    def panel(t0,t1,s0,s1,zlo,zhi,material,part):
        p=hinge+n*((t0+t1)/2)+d*((s0+s1)/2)+v*((zlo+zhi)/2)
        builder.box(p,(t1-t0,s1-s0,zhi-zlo),material,basis=[n,d,v],label=prefix+part)
    panel(-.018,.017,0,stile,z0,z1,wood,"hinge stile")
    panel(-.018,.017,width-stile,width,z0,z1,wood,"meeting stile")
    for lo,up,name in [(z0,low,"bottom rail"),(high,high+.037,"panel dividing rail"),(z1-.049,z1,"top rail")]:
        panel(-.018,.017,stile,width-stile,lo,up,wood,name)
    panel(-.006,.012,stile,width-stile,high+.037,z1-.049,wood,"recessed solid head panel")
    if raised:
        # The pale reverse has a narrow upright over the slats in both visible upper leaves.
        panel(.017,.029,width*.50-.010,width*.50+.010,low+.002,high-.002,wood,"slat tilting rod on pale reverse")
    if lod=="full":
        for position in (stile+.008,width-stile-.008):
            panel(-.012,-.006,position-.007,position+.007,high+.039,z1-.051,wood,"head-panel bead")
    count=row["blade_count"]
    pitch=(high-low)/count
    tilt=math.radians(32)
    thick=n*math.cos(tilt)-v*math.sin(tilt)
    slope=n*math.sin(tilt)+v*math.cos(tilt)
    for number in range(count):
        center=hinge+d*(width/2)+v*(low+(number+.5)*pitch)
        builder.box(center,(.008,width-2*stile,pitch*.91),blade,basis=[thick,d,slope],
                    label=prefix+"inclined blade "+str(number+1))


def sill(builder,row):
    start=row["front_y"]-.055; end=row["back_y"]+.055
    z=row["bottom"];p=row["sill_projection"];h=row["sill_height"]
    section=[(-p,z-.015),(-p+.003,z-h*.66),(-p+.030,z-h),(.105,z-h),(.105,z+.006)]
    verts=[(x,y,high) for y in (start,end) for x,high in section];k=len(section)
    faces=[tuple(range(k)),tuple(reversed(range(k,2*k)))]
    faces.extend((j,k+j,k+(j+1)%k,(j+1)%k) for j in range(k))
    builder.add(verts,faces,STONE,row["key"]+" | canted sill and lower bevel")
    if row["key"]=="ground-street":
        builder.box((-.035,(start+end)/2,z-h-.018),(.182,(end-start)-.055,.036),EDGE,
                    label=row["key"]+" | narrow underside of projecting sill")


def add_shutters(builder,lod):
    for row in side_openings():
        a,b,z0,z1=row["front_y"],row["back_y"],row["bottom"],row["top"]
        for y in (a+.014,b-.014):
            builder.box((.05,y,(z0+z1)/2),(.123,.028,z1-z0),DARK,label=row["key"]+" | painted reveal stile")
        builder.box((.038,(a+b)/2,z1-.014),(.104,b-a-.056,.028),DARK,label=row["key"]+" | head of reveal")
        if row["inward_leaf_angle_deg"]:
            sash_y=(a+b)/2; sash_z=z0+.70*(z1-z0)
            builder.box((.171,sash_y,(z0+z1)/2),(.040,.028,z1-z0),DARK,label=row["key"]+" | inset central glazing bar")
            builder.box((.170,sash_y,sash_z),(.035,b-a-.050,.035),DARK,label=row["key"]+" | upper sash rail")
            for ylo,yhi in ((a+.025,sash_y-.014),(sash_y+.014,b-.025)):
                for zl,zh in ((z0+.017,sash_z-.0175),(sash_z+.0175,z1-.025)):
                    builder.box((.199,(ylo+yhi)/2,(zl+zh)/2),(.012,yhi-ylo,zh-zl),GLASS,
                                label=row["key"]+" | recessed shaded pane")
        else:
            # The photograph records dark gaps in the shut pair. No interior arrangement is resolved.
            builder.box((.211,(a+b)/2,(z0+z1)/2),(.020,b-a-.055,z1-z0-.050),SHADE,
                        label=row["key"]+" | unlit backing behind the shut slats")
        leaf(builder,row,False,lod);leaf(builder,row,True,lod);sill(builder,row)
