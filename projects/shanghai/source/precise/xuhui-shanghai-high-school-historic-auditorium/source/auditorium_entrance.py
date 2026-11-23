"""Auditorium doorway, frontispiece and stair, drawn from the October 2020 photograph."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

MEASUREMENTS = Path(__file__).absolute().parents[1] / "measurements"
OCHRE = "Shanghai High School hall | ochre render"
TRIM = "Shanghai High School hall | cool grey cast trim"
STEP = "Shanghai High School hall | dressed stair stone"
WOOD = "Shanghai High School hall | reddish door timber"
GLASS = "Shanghai High School hall | smoked reflecting entrance glass"
METAL = "Shanghai High School hall | worn brass pulls"
REVEAL = "Shanghai High School hall | entrance shadow line"
PALETTE = {
    WOOD: dict(color=[.252, .079, .033], roughness=.56),
    GLASS: dict(color=[.049, .061, .058], roughness=.23, metallic=.12),
    METAL: dict(color=[.40, .24, .093], roughness=.52, metallic=.54),
    REVEAL: dict(color=[.084, .071, .057], roughness=.86),
}


def prism(b, shape, surface, thickness, material, label):
    if not shape.is_empty:
        b.prism(shape, -surface - thickness, -surface, lambda x, z, d: (x, -d, z),
                material, "Entrance | " + label)


def polygon(camera, uv, y):
    return Polygon([camera.wall(pixel, y)[[0, 2]] for pixel in uv]).buffer(0)


def points(camera, uv, y):
    return np.asarray([camera.wall(pixel, y)[[0, 2]] for pixel in uv])


def quad_fraction(q, s, t):
    top = (1-s)*q[0] + s*q[1]
    bottom = (1-s)*q[3] + s*q[2]
    return top*(1-t) + bottom*t


def section(q, a, b, low, high):
    return Polygon([quad_fraction(q, s, t) for s, t in
                    [(a, low), (b, low), (b, high), (a, high)]])


def stripe(b, xy, width, y, depth, mat, label):
    prism(b, LineString(xy).buffer(width / 2, cap_style=2, join_style=2),
          y, depth, mat, label)


def entrance_doors(b, camera, data, y, lod):
    opening = polygon(camera, data["door_outer"], y)
    leaves = []
    for i, frame in enumerate(data["door_pairs"]):
        q = points(camera, frame, y)
        for hand, (start, end) in enumerate([(0., .5), (.5, 1.)]):
            n = i * 2 + hand
            leaf = section(q, start, end, .195, 1).buffer(-.004, join_style=2)
            light = polygon(camera, data["door_glass_panels"][n], y)
            light = light.intersection(leaf.buffer(-.020))
            prism(b, leaf.difference(light), y, .066, WOOD, f"pair {i+1} leaf {hand+1}")
            prism(b, light.buffer(.002), y+.026, .012, GLASS, f"lower light {n+1}")
            if not lod:
                rim = light.buffer(.013, join_style=2).difference(light)
                prism(b, rim, y-.007, .012, WOOD, f"lower glazing bead {n+1}")
            trans = polygon(camera, data["door_transoms"][n], y)
            head = section(q, start, end, 0, .195)
            prism(b, head.difference(trans), y+.007, .057, WOOD, f"transom frame {n+1}")
            prism(b, trans, y+.033, .011, GLASS, f"transom light {n+1}")
            leaves += [leaf, head]
            # The small, vertically oriented public-facing handles are distinct from the timber stiles.
            x, z = camera.wall(data["door_pulls"][n], y-.045)[[0, 2]]
            h = (leaf.bounds[3]-leaf.bounds[1])*.083
            curve = [(x,y-.006,z+h/2), (x,y-.032,z+h*.46),
                     (x,y-.047,z+h*.33), (x,y-.047,z-h*.34),
                     (x,y-.032,z-h*.47), (x,y-.006,z-h/2)]
            b.tube(curve,.009,METAL,sides=6 if lod else 10,label=f"Entrance | pull {n+1}")
    casing = opening.difference(unary_union(leaves))
    prism(b, casing, y-.004, .082, WOOD, "door posts and perimeter")
    seal = opening.buffer(.018,join_style=2).difference(opening)
    prism(b, seal, y+.005, .09, REVEAL, "door perimeter shadow")
    jamb = polygon(camera, data["stone_jamb_outer"], y)
    prism(b, jamb.difference(opening.buffer(.016,join_style=2)), y-.028, .17, TRIM,
          "ashlar jamb and rectangular lintel")


def projecting_apron(b, camera, data, y):
    silhouette = polygon(camera,data["lower_apron"],y)
    prism(b, silhouette,y,.36,TRIM,"stepped apron body")
    for i,row in enumerate(data["lower_inner_panels"]):
        plate=polygon(camera,row,y-.028)
        prism(b,plate.buffer(.036,join_style=2),y-.031,.03,OCHRE,f"inset surround {i+1}")
        prism(b,plate,y-.042,.013,TRIM,f"rectangular tablet {i+1}")
    pendant=polygon(camera,data["pendant_face"],y-.10)
    middle=polygon(camera,data["pendant_middle"],y-.125)
    prism(b,pendant,y-.10,.14,TRIM,"central dropped pendant")
    prism(b,middle,y-.125,.03,TRIM,"pendant chamfered face")
    for name,width in [("pendant_upper_ridge",.047),("pendant_inset_arch",.031),
                       ("pendant_lower_chevron",.035)]:
        stripe(b,points(camera,data[name],y-.15),width,y-.15,.025,TRIM,name.replace("_"," "))
    # The dark soffit is visible between the forward tablet and the recessed door head.
    prism(b,polygon(camera,data["door_lintel"],y+.03),y+.03,.26,TRIM,"recessed lower nosing")


def mainwall_ornament(b,camera,data):
    y=-.034
    limits=box(-5.2,-20.,5.2,45.)
    slab=polygon(camera,data["upper_panel_outer"],y).intersection(limits)
    # The shell supplies the masonry backing at Y=0.
    prism(b,slab,y,.039,OCHRE,"central ochre frieze ground")
    for name in ("upper_panel_inner_marks","upper_lower_marks"):
        for i,row in enumerate(data[name]):
            pts=points(camera,row,y-.033)
            triangle=Polygon(pts).intersection(limits)
            prism(b,triangle,y-.033,.033,TRIM,f"{name} {i+1} raised relief")
            mid=pts.mean(axis=0)
            for n,scale in enumerate((.82,.58)):
                edges=mid+(pts-mid)*scale
                rib=LineString([*edges,edges[0]]).buffer(.016,cap_style=2,join_style=2)
                prism(b,rib.intersection(limits),y-.054,.021,TRIM,f"{name} {i+1} bead {n+1}")
    band=points(camera,data["upper_band_outer"],-.05)
    prism(b,Polygon(band).intersection(limits),-.05,.06,TRIM,"upper frieze band")
    for i in range(11):
        left=i/11; right=(i+1)/11;middle=(left+right)/2
        for lo,hi,width in [(.18,.82,.038),(.30,.70,.022)]:
            ring=[quad_fraction(band,u,v) for u,v in
                  [(left,.50),(middle,lo),(right,.50),(middle,hi),(left,.50)]]
            relief=LineString(ring).buffer(width/2,join_style=2)
            prism(b,relief.intersection(limits),-.085,.036,TRIM,f"crest lozenge {i+1} {lo}")
    for i,t in enumerate((.09,.94)):
        bar=LineString([quad_fraction(band,0,t),quad_fraction(band,1,t)]).buffer(.032,cap_style=2)
        prism(b,bar.intersection(limits),-.084,.037,TRIM,f"continuous frieze lip {i+1}")


def garden_stair(b,camera,data,door_y):
    rows=data["photo_steps"]["inner_cheeks_top_to_front"]
    ds=.38
    back=door_y+.10
    landing_y=door_y-.49
    heights=[]; sides=[]
    for i,row in enumerate(rows):
        y=landing_y-i*ds
        xyz=[camera.wall(p,y) for p in row]
        heights.append(float(np.mean([p[2] for p in xyz])))
        sides.append((float(xyz[0][0]),float(xyz[1][0]),y))
    top=np.mean([camera.wall(p,door_y)[2] for p in data["door_outer"][-2:]])
    bottom=heights[-1]
    # The returned points are silhouettes of eight masonry noses; their grade can
    # differ from the campus photogrammetric datum through plane-depth uncertainty.
    zlevels=np.linspace(top,bottom,len(rows))
    previous=(sides[0][0],sides[0][1],back)
    for i,((l,r,y),z) in enumerate(zip(sides,zlevels)):
        pl,pr,py=previous
        outline=Polygon([(l,y),(r,y),(pr,py),(pl,py)])
        b.plan_prism(outline,min(-.12,zlevels[-1]-.16),float(z),STEP,
                     label=f"Entrance | stone landing and tread {i+1}")
        previous=(l,r,y)
    for hand in (0,1):
        sign=-1 if hand==0 else 1
        vt=[];faces=[]
        for i,(edge,z) in enumerate(zip(sides,zlevels)):
            x,y=edge[hand],edge[2];t=i/(len(sides)-1)
            cheeks=.20+.36*(1-t)**1.8
            for xo,cap in [(0,False),(sign*.29,False),(sign*.29,True),(0,True)]:
                vt.append((x+xo,y,z+cheeks if cap else min(-.11,zlevels[-1]-.14)))
            if i:
                a=(i-1)*4;c=i*4
                faces.extend([(a+j,a+(j+1)%4,c+(j+1)%4,c+j)for j in range(4)])
        a=(len(sides)-1)*4
        faces.extend([(3,2,1,0),(a,a+1,a+2,a+3)])
        if sign<0:faces=[tuple(reversed(f))for f in faces]
        b.add(vt,faces,STEP,label=f"Entrance | sloping stone cheek {hand+1}")
    return {'landing':float(top),'toe':float(bottom),'lines':len(rows)-1}


def entrance_layout(camera,apron_y,door_y,data):
    shape=polygon(camera,data["lower_apron"],apron_y)
    return dict(front_y=apron_y,back_y=apron_y+.36,door_y=door_y,
                apron_bounds_xz=list(shape.bounds),
                door_bounds_xz=list(polygon(camera,data["door_outer"],door_y).bounds))


def add_from_camera(b,camera,apron_y,door_y,lod=False):
    data=json.loads((MEASUREMENTS/"entrance-photo-controls.json").read_bytes())
    entrance_doors(b,camera,data,door_y,lod)
    projecting_apron(b,camera,data,apron_y)
    mainwall_ornament(b,camera,data)
    garden_stair(b,camera,data,door_y)
    return entrance_layout(camera,apron_y,door_y,data)


def add_entrance(b,lod=False):
    import sys
    sys.path.insert(0,str(MEASUREMENTS))
    from register_court import Camera
    from entrance_planes import APRON_Y, DOOR_Y
    return add_from_camera(b,Camera(2020),APRON_Y,DOOR_Y,lod)
