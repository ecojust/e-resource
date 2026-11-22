"""Six shutter leaves, front timber frame and cheeks of the garden-facing shed dormer."""
import json
from pathlib import Path

REGISTRATION = Path(__file__).resolve().parents[1] / "measurements" / "dormer-registration.json"

TIMBER = "Garden dormer | red-brown timber framing"
LOUVRE = "Garden dormer | dark stained louvre blades"
EDGE = "Garden dormer | shutter-frame moulding"
SHADOW = "Garden dormer | recess behind the shutter blades"
PLASTER = "Garden dormer | buff plaster between timbers"
TRIM = "Garden dormer | painted eaves and soffit"
RIM = "Garden dormer | folded dark roof rim"
ROOF = "Garden dormer | shaded shed roof skin"


def finish(rgb, roughness, metallic=0):
    c = [v / 255 for v in rgb]
    return {"color": [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in c],
            "roughness": roughness, "metallic": metallic}


PALETTE = {
    TIMBER: finish((102, 76, 65), .83), LOUVRE: finish((86, 73, 68), .79),
    EDGE: finish((98, 79, 68), .79), SHADOW: finish((36, 32, 30), .93),
    PLASTER: finish((195, 171, 153), .92), TRIM: finish((91, 69, 59), .84),
    RIM: finish((67, 67, 66), .70, .22), ROOF: finish((85, 78, 73), .84)
}


def _across(builder, left, right, section, material, label):
    """Extrude one closed convex Y/Z profile between two end faces."""
    area = sum(y1*z2-y2*z1 for (y1,z1),(y2,z2) in
               zip(section, section[1:]+section[:1]))
    if area < 0:
        section = list(reversed(section))
    n = len(section)
    vertices = [(x, y, z) for x in (left, right) for y, z in section]
    faces = [tuple(reversed(range(n))),tuple(range(n, n*2))]
    faces.extend((i, (i+1)%n, n+(i+1)%n, n+i) for i in range(n))
    builder.add(vertices, faces, material, label)


def _box(builder, x0, x1, y0, y1, z0, z1, mat, name):
    builder.box(((x0+x1)/2, (y0+y1)/2, (z0+z1)/2),
                (x1-x0, y1-y0, z1-z0), mat, label=name)


def add_dormer(builder, lod=False):
    """Add the photographed dormer in the metric coordinate system of the garden arcade."""
    d = json.loads(REGISTRATION.read_text())
    far = lod is True or lod in ("low", "lod", "far", "distant")
    face = d["front_shutter_plane_y_m"]
    left, right = d["face_extent_x_m"]
    base, head = d["platform_and_head_z_m"]
    rz = d["roof"]
    roof_left, roof_right = rz["outer_x_m"]
    nose, back = rz["front_y_m"], rz["rear_intersection_y_m"]
    tip, rear = rz["front_upper_z_m"], rz["rear_upper_z_m"]
    slope = (rear-tip)/(back-nose)

    def top(y):
        return tip+slope*(y-nose)

    def roof_band(x0,x1,y0,y1,drop0,drop1,material,label):
        _across(builder,x0,x1,[(y0,top(y0)-drop1),(y1,top(y1)-drop1),
                (y1,top(y1)-drop0),(y0,top(y0)-drop0)],material,label)

    roof_band(roof_left,roof_right,nose,back,0,.085,ROOF,"Single-pitch shed | continuous roof")
    roof_band(roof_left,roof_right,nose-.015,nose+.070,-.012,.122,RIM,"Single-pitch shed | dark leading rim")
    roof_band(roof_left+.045,roof_right-.045,nose+.065,back,.084,.324,TIMBER,"Single-pitch shed | warm fascia")
    roof_band(roof_left+.074,roof_right-.074,nose+.088,back,.324,.420,TRIM,"Single-pitch shed | lower timber fascia strip")
    roof_band(roof_left+.108,roof_right-.108,nose+.105,back,.420,.489,TRIM,"Single-pitch shed | exposed underside")
    for side,x0,x1 in [("left",roof_left,roof_left+.063),("right",roof_right-.063,roof_right)]:
        roof_band(x0,x1,nose,back,-.005,.122,RIM,"Single-pitch shed | "+side+" rim fold")

    # The normalized front photograph resolves six leaves and two solid pale panels.
    bank_bottom, bank_top = d["bank_frame_z_m"]
    blade_bottom, blade_top = d["blade_borders_z_m"]
    cream_bottom, cream_top = d["central_plaster_z_m"]
    _box(builder,left,right,face-.037,face+.095,base,bank_bottom,TIMBER,"Garden dormer | sill below the two shutter banks")
    _box(builder,left,right,face-.036,face+.085,bank_top,top(face)-.489,TIMBER,"Garden dormer | upper transverse timber")
    banks = d["bank_frame_x_m"]
    cream = d["central_plaster_intervals_x_m"]
    for label,x0,x1 in [("left outer jamb",left,banks[0][0]),("left centre post",banks[0][1],cream[0][0]),
                         ("middle post",cream[0][1],cream[1][0]),("right centre post",cream[1][1],banks[1][0]),
                         ("right outer jamb",banks[1][1],right)]:
        _box(builder,x0,x1,face-.044,face+.12,bank_bottom,bank_top,TIMBER,"Garden dormer | "+label)
    for i,(x0,x1) in enumerate(cream,1):
        _box(builder,x0,x1,face+.018,face+.130,cream_bottom,cream_top,PLASTER,f"Garden dormer | pale infill {i}")
        for a,b in [(bank_bottom,cream_bottom),(cream_top,bank_top)]:
            if b>a:
                _box(builder,x0,x1,face-.027,face+.095,a,b,TIMBER,f"Garden dormer | infill {i} horizontal edge")

    for bank_index, (x0,x1) in enumerate(banks):
        group = d["shutters"][3*bank_index:3*bank_index+3]
        blades = d["blade_rows"][bank_index]["leading_edge_z_m"]
        for a,b,n in [(bank_bottom,blade_bottom,"sill"),(blade_top,bank_top,"head")]:
            _box(builder,x0,x1,face-.020,face+.086,a,b,EDGE,f"Shutter bank {bank_index+1} | {n}")
        limits = [x0]
        for shutter in group:
            limits.extend(shutter["blade_span_x_m"])
        limits.append(x1)
        for j,(a,b) in enumerate(zip(limits[::2],limits[1::2]),1):
            _box(builder,a,b,face-.021,face+.093,blade_bottom,blade_top,EDGE,
                 f"Shutter bank {bank_index+1} | vertical stile {j}")
        for sh in group:
            a,b = sh["blade_span_x_m"]
            number = sh["id"]
            _box(builder,a-.047,b+.047,face+.121,face+.160,blade_bottom-.052,blade_top+.052,SHADOW,f"Shutter {number} | unlit recess")
            for k,z in enumerate(blades,1):
                # The outer leading lip is lower than the inner edge. The unseen depth is estimated.
                yy = face+.008
                if far:
                    sec = [(yy,z-.016),(yy+.070,z+.029),(yy+.070,z+.045),(yy,z)]
                else:
                    sec = [(yy,z-.013),(yy+.004,z-.015),(yy+.068,z+.026),
                           (yy+.073,z+.032),(yy+.071,z+.045),(yy+.004,z+.002)]
                _across(builder,a,b,sec,LOUVRE,f"Shutter {number} | louvre {k:02}")

    # Oblique photographs expose the left cheek up to the intersection with the main tiles.
    roof_pitch = (rz["roof_main_seam_back_yz_m"][1]-base)/(back-face)
    soffit = lambda y:top(y)-.489
    joint_y = face+(soffit(face)-base)/(roof_pitch-slope)
    joint_z = soffit(joint_y)
    cheek = [(face,base),(joint_y,joint_z),(face,soffit(face))]
    for label,x0,x1 in [("left",left,left+.095),("right",right-.095,right)]:
        _across(builder,x0,x1,cheek,PLASTER,f"Garden dormer | {label} triangular cheek")
        exposed_x0,exposed_x1 = (x0-.038,x0) if label=="left" else (x1,x1+.038)
        _across(builder,exposed_x0,exposed_x1,[(face,base),(joint_y,joint_z),
                (joint_y-.085,joint_z-slope*.085),(face,base+.187)],TIMBER,
                f"Garden dormer | {label} diagonal timber against main tiles")
        _box(builder,exposed_x0,exposed_x1,face,face+.165,base+.162,soffit(face)-.018,TIMBER,
             f"Garden dormer | {label} cheek upright")


    # The photographs resolve the two offset metal strips and the dark projecting
    # block at each corner. Their junction with the lower main eave is obscured.
    for item in d["corner_fittings"]:
        side = item["name"]
        x1,x2 = item["fascia_and_lower_x_m"]
        y1,y2 = item["fascia_and_lower_y_m"]
        upper, lower = item["top_and_bottom_z_m"]
        elbow = item["elbow_z_m"]
        _box(builder,x1-.073,x1+.073,y1-.044,y1+.060,elbow+.26,upper,RIM,
             f"Dormer {side} | vertical eave strap")
        path = [(x1,y1+.018,elbow+.295),(x1,y1+.080,elbow+.227),
                (x2,y2-.082,elbow+.080),(x2,y2,elbow+.012)]
        builder.tube(path,.060,RIM,6 if far else 10,f"Dormer {side} | offset below the shed eave")
        _box(builder,x2-.147,x2+.147,y2-.113,y2+.054,elbow-.107,elbow+.050,RIM,
             f"Dormer {side} | projecting square head")
        _box(builder,x2-.057,x2+.057,y2-.036,y2+.054,lower,elbow-.090,RIM,
             f"Dormer {side} | dark vertical at shutter jamb")
