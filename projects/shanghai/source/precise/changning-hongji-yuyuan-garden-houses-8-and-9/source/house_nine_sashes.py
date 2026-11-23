"""Six sash windows and the stepped chimney breast of house 9, east lawn gable."""
import json
from pathlib import Path

from shapely.geometry import Polygon, box

from hongji_roof_geometry import PEBBLE, PALETTE as ROOF_MATERIALS, height
from roof_9 import dimensions as roof_dimensions, planes as roof_planes

SURVEY = Path(__file__).resolve().parents[1] / "measurements/nine-gable-window-survey.json"
WOOD = "9 sash | charcoal frame"
BEAD = "9 sash | painted glazing bar"
GLASS = ("9 glass | green grey", "9 glass | shaded warm grey", "9 glass | reflected sky")
PALE = "9 glass | pale lower light"
PLASTER = "9 surround | aged cream render"
EDGE = "9 surround | sunlit sill edge"
MOUNT = "9 surround | iron fixing"


def finish(rgb, roughness, metallic=0.):
    def linear(n):
        n /= 255
        return n / 12.92 if n <= .04045 else ((n + .055) / 1.055) ** 2.4
    return {"color": [linear(v) for v in rgb], "roughness": roughness, "metallic": metallic}


PALETTE = {
    WOOD: finish((43, 51, 48), .68),
    BEAD: finish((72, 80, 72), .60),
    GLASS[0]: finish((81, 104, 97), .27, .15),
    GLASS[1]: finish((86, 87, 76), .32, .13),
    GLASS[2]: finish((94, 116, 120), .27, .17),
    PALE: finish((157, 169, 161), .50, .04),
    PLASTER: finish((199, 197, 183), .91),
    EDGE: finish((218, 216, 202), .88),
    MOUNT: finish((45, 48, 43), .78, .15),
    PEBBLE: ROOF_MATERIALS[PEBBLE],
}


def records():
    return json.loads(SURVEY.read_bytes())["registration"]["fitted_windows"]


def front_openings(layout):
    return {row["id"]: box(row["x_min"], row["bottom_z"], row["x_max"], row["top_z"])
            for row in records()}


def solid(b, outline, front_y, back_y, material, label):
    b.prism(outline, -back_y, -front_y, lambda x, z, d: (x, -d, z), material, label)


def sash(b, row, lod):
    label = "9 " + row["id"]
    x, r = row["x_min"], row["x_max"]
    low, top = row["bottom_z"], row["top_z"]
    mid = (x + r) / 2
    upper = row["id"].startswith("upper")
    axis = int(row["id"][-1]) - 1
    rect = lambda l, z, h, zz, a, c, m, part: solid(
        b, box(l, z, h, zz), a, c, m, label + " | " + part)

    outer = box(x, low, r, top)
    jamb = .053 if upper else .049
    clear = box(x + jamb, low + jamb, r - jamb, top - jamb)
    solid(b, outer.difference(clear), .064, .153, WOOD, label + " | perimeter")
    if not lod:
        edge = clear.difference(clear.buffer(-.012, join_style=2))
        solid(b, edge, .084, .142, BEAD, label + " | inner bead")
    inner_l, inner_r = x + jamb, r - jamb
    inner_lo, inner_hi = low + jamb, top - jamb
    if upper:
        lights = [(inner_lo, inner_hi, 3, GLASS[axis])]
    else:
        cross = row["transom_center_z"]
        rect(inner_l, cross-.047, inner_r, cross+.047, .055, .148, WOOD, "transom")
        lights = [(inner_lo, cross-.047, 2, GLASS[axis] if axis==1 else PALE),
                  (cross+.047, inner_hi, 2, GLASS[axis])]
    for level,(z0,z1,divisions,glass_material) in enumerate(lights):
        rect(mid-.031, z0, mid+.031, z1, .079, .15, WOOD, f"meeting stile {level+1}")
        row_step = (z1-z0)/divisions
        for side,(l,rr) in enumerate(((inner_l,mid-.031),(mid+.031,inner_r))):
            for j in range(divisions):
                a=z0+j*row_step
                zz=z0+(j+1)*row_step
                if j:
                    rect(l, a-.009, rr, a+.009, .105, .151, BEAD,
                         f"glazing bar {level+1}.{side+1}.{j}")
                rect(l, a+(.009 if j else 0), rr, zz-(.009 if j<divisions-1 else 0),
                     .153, .168, glass_material, f"pane {level+1}.{side+1}.{j+1}")
    rect(x-.025, top+.005, r+.025, top+.128, -.061, .019, PLASTER, "head fascia")
    cap = row["cap_z"] + .010
    rect(x-.078, top+.127, r+.078, cap, -.121, .019, EDGE, "projecting cap")
    positions=[mid] if upper else [x+.024,r-.024]
    for j,center in enumerate(positions,1):
        rect(center-.040,cap,center+.040,max(cap+.051,row["observed_fixing_z"]),-.073,-.015,MOUNT,f"head fixing {j}")
    if upper:
        rect(x-.026,low-.164,r+.026,low-.055,-.074,.018,PLASTER,"sill apron")
        rect(x-.055,low-.057,r+.055,low-.004,-.126,.018,EDGE,"sill lip")


def breast(b, layout):
    measured = json.loads(SURVEY.read_bytes())["registration"]["shaft_shoulders"]
    r_low = measured["right_lower_nose"]["xyz"]
    r_high = measured["right_upper_nose"]["xyz"]
    l_low = measured["left_lower_nose"]["xyz"]
    l_high = measured["left_upper_nose"]["xyz"]
    z0, z1 = r_low[2], r_high[2]
    bottom = float(layout.get("ground_z",0))
    solid(b,box(l_low[0],bottom,r_low[0],z0),r_low[1],.006,PEBBLE,"9 breast | lower front")
    shoulder = Polygon([(l_low[0],z0),(r_low[0],z0),(r_high[0],z1),(l_high[0],z1)])
    def graded(x,z,d):
        t=(z-z0)/(z1-z0)
        y=r_low[1]+(r_high[1]-r_low[1])*t
        return (x,.006*(1-d)+y*d,z)
    b.prism(shoulder,0,1,graded,PEBBLE,"9 breast | splayed shoulders")
    dims=roof_dimensions(layout)
    axis=float(layout.get("chimney_x",dims["wall_width"]*2.5126/7.27))
    chimney_y=float(layout.get("chimney_y",.006))
    stack_bottom=height(roof_planes(layout),axis,chimney_y)-.72
    solid(b,box(l_high[0],z1,r_high[0],stack_bottom),r_high[1],.006,PEBBLE,
          "9 breast | upper front below roof stack")


def add_sashes(b, lod, layout):
    for material, values in PALETTE.items():
        b.palette.setdefault(material,values)
    for row in records():
        sash(b,row,lod)
    breast(b,layout)
