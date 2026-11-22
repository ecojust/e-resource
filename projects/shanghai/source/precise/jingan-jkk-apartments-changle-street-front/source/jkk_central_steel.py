"""Build the glazed steel casements in the recessed central bay of the south elevation."""
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BLACK = "JKK central | dark painted steel"
EDGE = "JKK central | rubbed edge of glazing bars"
GLASS = "JKK central | cool reflected glass"
DULL = "JKK central | shaded glass"
PALE = "JKK central | sky reflection"
SHADOW_GLASS = "JKK central | deep grey glass"
LIGHT_GLASS = "JKK central | light grey glass"
OPEN = "JKK central | glass in projecting leaf"
BACK = "JKK central | inner shadow"
SILL = "JKK central | sill and reveal"
UP = np.array([0., 0., 1.])


def finish(rgb, roughness, metal=0., alpha=None):
    rgb = np.asarray(rgb)/255
    material = {"color": np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4).tolist(),
                "metallic": metal, "roughness": roughness}
    if alpha is not None:
        material["alpha"] = alpha
    return material


PALETTE = {
    BLACK: finish([43, 42, 39], .62, .43), EDGE: finish([68, 65, 58], .69, .30),
    GLASS: finish([76, 80, 82], .31, .13), DULL: finish([52, 53, 54], .33, .13),
    SHADOW_GLASS: finish([35, 36, 36], .36, .12), LIGHT_GLASS: finish([99, 103, 108], .30, .15),
    PALE: finish([139, 143, 146], .30, .17), OPEN: finish([96, 102, 102], .29, .10, .44),
    BACK: finish([28, 27, 24], .96), SILL: finish([127, 110, 91], .90)
}


def placement():
    return json.loads((HERE.parent/"measurements/central-steel-reconstruction.json").read_text())


def central_openings():
    """Four actual plaster cutouts. Dimensions are in the host's local x/z plane."""
    return placement()["openings"]


def leaf(b, xhinge, plane, bottom, top, width, direction, angle, tilt, columns, rows,
         name, lod, glazing):
    """Coordinate u runs from the hinged jamb to the free stile. A top light can tilt separately."""
    yaw, slant = np.radians([angle, tilt])
    along = np.array([direction*math.cos(yaw), -math.sin(yaw), 0.])
    normal = np.array([direction*math.sin(yaw), math.cos(yaw), 0.])
    rise = UP*math.cos(slant) + normal*math.sin(slant)
    inward = normal*math.cos(slant) - UP*math.sin(slant)
    origin = np.array([xhinge, plane, top])
    def solid(u, d, z, w, thickness, height, mat, description):
        pos = origin + u*along + d*inward + (z-top)*rise
        b.box(pos, (w, thickness, height), mat, (along, inward, rise), f"JKK central | {name} | {description}")
    rim = .022 if columns > 2 else .017
    blade = .014 if columns > 2 else .012
    height = top-bottom
    for u, side in [(rim/2,"hinged edge"), (width-rim/2,"free edge")]:
        solid(u, 0., (top+bottom)/2, rim, .042, height, BLACK, side)
    for z, side in [(bottom+rim/2,"bottom bar"), (top-rim/2,"top bar")]:
        solid(width/2, 0., z, width-2*rim, .042, rim, BLACK, side)
    clear_w, clear_h = width-2*rim, height-2*rim
    dx, dz = clear_w/columns, clear_h/rows
    for c in range(1,columns):
        solid(rim+c*dx, -.002, (bottom+top)/2, blade, .032, clear_h, BLACK, f"muntin {c}")
    for r in range(1,rows):
        solid(width/2, -.002, bottom+rim+r*dz, clear_w, .032, blade, BLACK, f"crossbar {r}")
    for c in range(columns):
        for r in range(rows):
            u, z = rim+(c+.5)*dx, bottom+rim+(r+.5)*dz
            w, h = dx-blade*.86, dz-blade*.86
            mat = OPEN if angle else glazing
            solid(u, .007, z, w, .006, h, mat, f"pane {c+1}/{r+1}")
            if not lod:
                # Two small return beads hold each individual pane in the steel angle.
                solid(u, -.006, z-h/2+.0035, w, .014, .007, EDGE, f"pane {c+1}/{r+1} bedding")
                solid(u-w/2+.0035, -.006, z, .007, .014, h, EDGE, f"pane {c+1}/{r+1} left bead")
    if angle and not lod:
        for n, z in enumerate([bottom+.12*height, top-.12*height], 1):
            b.lathe((xhinge, plane), [(z-.034,.013),(z-.027,.015),(z+.026,.015),(z+.035,.012)],
                    BLACK, 10, f"JKK central | {name} | hinge barrel {n}")
    if tilt and not lod:
        for n, u in enumerate([rim, width-rim], 1):
            opened = origin + u*along + ((bottom+.042)-top)*rise
            fixed = [xhinge+direction*u, plane+.015, bottom+.065]
            b.tube([fixed, opened], .007, BLACK, 8, f"JKK central | {name} | transom stay {n}")


def build_opening(b, record, lod):
    label = record["id"]
    left, bottom, right, top = record["rect_xz_m"]
    y = record["sash_y_m"]
    face = record["face_y_m"]
    w, h = right-left, top-bottom
    # The source shows a narrow, square reveal with no projecting ornamental architrave.
    b.box(((left+right)/2, y+.45, (bottom+top)/2), (w,.032,h), BACK,
          label=f"JKK central | {label} | unlit depth")
    for x, side in [(left+.009,"west"),(right-.009,"east")]:
        b.box((x,y+.226,(bottom+top)/2),(.018,.46,h),BACK,
              label=f"JKK central | {label} | shaded interior {side} return")
    for z, side in [(bottom+.009,"bottom"),(top-.009,"head")]:
        b.box(((left+right)/2,y+.226,z),(w-.032,.46,.018),BACK,
              label=f"JKK central | {label} | shaded interior {side} return")
    d = y+.017-face
    for x, side in [(left+.010,"west"),(right-.010,"east")]:
        b.box((x, face+d/2, (top+bottom)/2), (.020,d,h), SILL, label=f"JKK central | {label} | {side} reveal")
    for z, side in [(bottom+.012,"sill"),(top-.012,"head")]:
        b.box(((left+right)/2,face+d/2,z),(w-.036,d,.024),SILL,label=f"JKK central | {label} | {side}")
    jamb=.027
    for x, side in [(left+.019+jamb/2,"west"),(right-.019-jamb/2,"east")]:
        b.box((x,y,(bottom+top)/2),(jamb,.067,h-.026),BLACK,label=f"JKK central | {label} | {side} frame")
    for z, side in [(bottom+.022+jamb/2,"bottom"),(top-.022-jamb/2,"head")]:
        b.box(((left+right)/2,y,z),(w-.08,.067,jamb),BLACK,label=f"JKK central | {label} | {side} frame")
    x0, x1 = left+.043, right-.043
    z0, z1 = bottom+.048, top-.048
    if label == "upper-transom":
        leaf(b,x0,y,z0,z1,x1-x0,1,0.,0.,6,2,label,lod,GLASS)
        return
    div = record.get("transom_fraction_from_top")
    zleaf = z1 if div is None else z1-div*(z1-z0)
    if div is not None:
        b.box(((left+right)/2,y,zleaf),(x1-x0,.074,.036), BLACK,
              label=f"JKK central | {label} | transom rail")
    width=(x1-x0)/3
    for j,(side,angle) in enumerate(zip(("west","centre","east"),record["lower_leaf_angles_deg"],strict=True)):
        l,r=x0+j*width,x0+(j+1)*width
        sign=-1 if j==2 else 1
        pivot=r-.009 if sign<0 else l+.009
        kind=[DULL,GLASS,DULL][j]
        pivot_y=y-.015
        actual_width=width-.018
        if angle:
            pivot=right-record["hinge_inset_m"] if sign<0 else left+record["hinge_inset_m"]
            pivot_y=record["hinge_y_m"]
            actual_width+=record["open_leaf_width_increment_m"]
            for k,z in enumerate([z0+.12*(zleaf-.016-z0),zleaf-.016-.12*(zleaf-.016-z0)]):
                b.box((pivot,(pivot_y+y)/2,z),(.024,y-pivot_y+.020,.041),BLACK,
                      label=f"JKK central | {label} {side} | hinge return {k+1}")
        leaf(b,pivot,pivot_y,z0,zleaf-.016,actual_width,sign,angle,0.,2,4,
             f"{label} {side} casement",lod,kind)
        if div is not None:
            tilt=record.get("center_top_tilt_deg",0.) if j==1 else 0.
            leaf(b,l+.009,y-.005,zleaf+.016,z1,width-.018,1,0.,tilt,2,2,
                 f"{label} {side} transom",lod,PALE if j==1 else GLASS)
        if j:
            b.box((l,y+.009,(z0+z1)/2),(.025,.061,z1-z0),BLACK,
                  label=f"JKK central | {label} | fixed division {j}")


def add_central_sashes(builder, lod=False):
    builder.palette.update(PALETTE)
    first=len(builder.parts)
    for record in central_openings():
        build_opening(builder,record,lod)
    reference=json.loads((HERE.parent/"measurements/central-steel-glass-tones.json").read_text())["panes"]
    colours={"shadow":SHADOW_GLASS,"dark":DULL,"cool":GLASS,"light":LIGHT_GLASS,"pale":PALE}
    for part in builder.parts[first:]:
        if part["material"] in (GLASS,DULL,PALE):
            pane=part["label"].removeprefix("JKK central | ")
            part["material"]=colours[reference[pane]["tone"]]
