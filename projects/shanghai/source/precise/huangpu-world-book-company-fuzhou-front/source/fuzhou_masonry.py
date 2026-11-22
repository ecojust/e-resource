"""Facing units, folded lower belt and projecting parapet on the Fuzhou Road frontage."""
from collections import defaultdict
import json
from pathlib import Path

import numpy as np

from material_names import MATERIAL
from shopfront import DATA, block, rect
from upper_bookshop_windows import finish, openings


MEASURES = Path(__file__).resolve().parents[1] / "measurements"
PROFILE = json.loads((MEASURES / "bookshop-piers-and-belts.json").read_bytes())
JOINTS = json.loads((MEASURES / "bookshop-pale-joints.json").read_bytes())
DIRECT = {r["opening"]: r for r in JOINTS["measured_panels"]}
PALE = ["Fuzhou pale biscuit face", "Fuzhou warm grey face", "Fuzhou buff face",
        "Fuzhou worn pale face", "Fuzhou darker pale face"]
BED = "Fuzhou pale facing joint bed"
SHADOW = "Shaded return of the Fuzhou continuous drip"
RED = ["Fuzhou red sill ends", "Fuzhou muted red sill ends", "Fuzhou plum sill ends"]
COPING = "Grey cap of the Fuzhou Road parapet"
LOWER_CAP = "Patinated lower edge of the Fuzhou Road parapet"
PALETTE = {BED: finish((146, 133, 116), .95, 0), COPING: finish((160, 158, 154), .90, 0),
           LOWER_CAP: finish((130, 128, 124), .94, 0), SHADOW: finish((103, 93, 80), .96, 0)}
for name, rgb in zip(PALE, [(181, 164, 140), (172, 158, 141), (182, 163, 137),
                             (188, 174, 154), (164, 149, 132)]):
    PALETTE[name] = finish(rgb, .92, 0)
for name, rgb in zip(RED, [(123, 72, 69), (135, 79, 72), (112, 64, 65)]):
    PALETTE[name] = finish(rgb, .91, 0)


def add_cell(group, left, right, bottom, top, front, rear):
    """Append a closed solid to a group of individually jointed facing units."""
    if right <= left or top <= bottom or rear <= front:
        return
    vertices, faces = group
    i = len(vertices)
    for z in (bottom, top):
        vertices.extend([(left, front, z), (right, front, z), (right, rear, z), (left, rear, z)])
    for face in [(0,3,2,1), (4,5,6,7), (0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7)]:
        faces.append(tuple(i + v for v in face))


def repeated_heads(width, index):
    # The close view shows long and short faces within a course. Successive
    # courses move the perpend about 45 mm. No hidden wall bond is inferred.
    long, short = PROFILE["unit_stretcher_and_header_width_m"]
    period = long + short
    offset = -.033 + (.044 if index % 2 else 0.)
    return sorted(x for k in range(-1, int(width/period)+2)
                  for x in (offset+k*period, offset+k*period+long) if .020 < x < width-.020)


def panel(b, left, right, bottom, top, front, label, seed, record=None):
    width, height = right-left, top-bottom
    if width <= .035 or height <= .025:
        return
    bed = front + .018
    block(b, left, bottom, right, top, bed, bed+.025, BED, label+" recessed pointing")
    if record:
        rw, rh = record["rectification_px"]
        levels = np.r_[0., record["bed_centres_px"], rh] * (height/rh)
        heads = [[u*width/rw for u in row["visible_heads_px"]] for row in record["courses"]]
    else:
        count = max(1, round(height/JOINTS["bed_module_m"]))
        levels = np.linspace(0., height, count+1)
        heads = [repeated_heads(width, i+seed) for i in range(count)]
    groups = defaultdict(lambda: ([], []))
    for index, (a, z) in enumerate(zip(levels, levels[1:])):
        upper = top-a-(.0035 if index else .001)
        lower = top-z+(.0035 if index+1 < len(levels)-1 else .001)
        cuts = [0., *heads[index], width]
        for col, (lo, hi) in enumerate(zip(cuts, cuts[1:])):
            shade = (seed*7+col*13+index*3+(index*col*17)%7) % len(PALE)
            face = front + .0009*((shade+col)%3)
            add_cell(groups[shade], left+lo+(.0045 if lo else .001),
                     left+hi-(.0045 if hi<width else .001), lower, upper, face, bed+.003)
    for shade, (vertices, faces) in groups.items():
        b.add(vertices, faces, PALE[shade], label+" facing units "+str(shade+1))


def soldier_ends(b, r, lod):
    # The bottom of each dark window meets narrow red end faces. The opening
    # has a dark red soffit with transverse joints visible in the close views.
    left, right, z, top = (r[k] for k in ("left","right","bottom","top"))
    groups = defaultdict(lambda: ([], []))
    count = max(3, round((right-left)/.091))
    for i in range(count):
        l = left+(right-left)*i/count+.003
        h = left+(right-left)*(i+1)/count-.003
        shade = (i+r["within_bay"]+r["row_from_roof"])%len(RED)
        add_cell(groups[shade], l, h, z-.112, z-.002, -.023, .012)
        if not lod:
            add_cell(groups[shade], l, h, top-.004, top+.032, -.011, .19)
    for shade, (vertices, faces) in groups.items():
        b.add(vertices, faces, RED[shade], r["label"]+" red sill and soffit ends "+str(shade+1))


def profiled_band(b, left, right, section, mat, label):
    """Extrude a street-side Y,Z profile along the horizontal X axis."""
    n=len(section)
    v=[(x,y,z) for x in (left,right) for y,z in section]
    f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    f.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    # Profile winding can vary with the direction of a bevel.
    area=sum(y*section[(i+1)%n][1]-section[(i+1)%n][0]*z for i,(y,z) in enumerate(section))
    if area<0:
        f=[tuple(reversed(face)) for face in f]
    b.add(v,f,mat,label)


def parapet(b):
    caps=PROFILE["caps_left_right_m"]
    roof=PROFILE["roof_fit_m"]
    base, top = roof["base"],roof["top"]
    for i,(left,right) in enumerate(caps):
        # The outer nose overhangs the brick on all visible sides. The return
        # steps in again between piers, without opening a gap in the cap.
        l,r=left+.064,right-.064
        face=roof["pier_face"]
        block(b,l,8.12,r,base+.015,face,.055,MATERIAL,f"Parapet pier {i+1} red face and returns")
        for k,(a,c) in enumerate([(l-.078,l+.015),(r-.015,r+.078)]):
            block(b,a,8.12,c,base+.009,face+.093,.030,MATERIAL,f"Parapet pier {i+1} shallow shoulder {k+1}")
    spans=[]
    for i,(left,right) in enumerate(caps):
        spans.append((left,right,roof["pier_coping_nose"],f"Projecting pier cap {i+1}"))
        if i<len(caps)-1:
            spans.append((right,caps[i+1][0],roof["bay_coping_nose"],f"Connecting bay coping {i+1}"))
    for left,right,front,label in spans:
        # The blackened underside, vertical fascia and sloping water-shedding
        # top can be distinguished even where the coping crosses a pilaster.
        profiled_band(b,left,right,[(.26,base-.025),(.26,base+.225),(front+.026,base+.225),
                      (front+.045,base+.148),(front+.080,base+.071),(front+.112,base-.025)],LOWER_CAP,label+" recessed bed")
        profiled_band(b,left,right,[(.26,base+.208),(.26,top-.047),(front+.016,top),
                      (front,top-.064),(front,base+.258),(front+.023,base+.208)],COPING,label+" chamfered nose")


def add_upper_masonry(b, lod=False):
    rows=list(openings())
    positions={(r["bay"],r["within_bay"],r["row_from_roof"]):r for r in rows}
    fascia={v["bay"]:rect(v["black_fascia"],-.32).bounds[3] for v in DATA["bays"]}
    caps=PROFILE["caps_left_right_m"]
    parapet(b)
    for r in rows:
        bay,index,tier=(r[k] for k in ("bay","within_bay","row_from_roof"))
        left,right=r["left"]-.006,r["right"]+.006
        below=positions.get((bay,index,tier+1))
        ztop=r["bottom"]-({4:.259,5:.304}.get(tier,PROFILE["upper_sill_to_pale_top_m"]))
        if tier==5:
            floor=fascia[bay]-.11
        elif tier==4:
            floor=below["top"]+.879
        else:
            floor=below["top"]+PROFILE["upper_head_to_pale_bottom_m"]
        panel(b,left,right,floor,ztop,-.029,r["label"]+" pale apron",bay*17+index+tier,DIRECT.get(r["label"]))
        soldier_ends(b,r,lod)
        if tier==5:
            panel(b,left,right,r["top"]+.129,r["top"]+.307,-.027,
                  r["label"]+" pale inset below drip",index)
    for bay in range(1,6):
        z=float(np.median([r["top"] for r in rows if r["bay"]==bay and r["row_from_roof"]==5]))
        left,right=caps[bay-1][1]-.077,caps[bay][0]+.077
        profiled_band(b,left,right,[(.057,z+.294),(.057,z+.891),(-.116,z+.919),
                      (-.162,z+.865),(-.149,z+.351),(-.107,z+.306),(-.060,z+.294)],SHADOW,f"Bay {bay} deep continuous drip and shadow")
        panel(b,left,right,z+.356,z+.882,-.169,f"Bay {bay} pale continuous belt",bay*7)
