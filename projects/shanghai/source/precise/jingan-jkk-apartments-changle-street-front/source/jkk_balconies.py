"""Street-front gallery slabs and open railings, traced from the winter street views."""
import json
import math
from pathlib import Path

from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

DATA = Path(__file__).resolve().parents[1] / "measurements" / "jkk-balcony-sections.json"
SOFFIT = "JKK balconies | warm grey slab soffit"
FLAG = "JKK balconies | weathered upper walking surface"
BAND = "JKK balconies | pale grey continuous parapet bands"
UPRIGHT = "JKK balconies | cast vertical mullions"
RAIL = "JKK balconies | dark painted metal handrail"
SHOE = "JKK balconies | handrail socket"


def finish(srgb, roughness, metallic=0):
    rgb = [v / 255 for v in srgb]
    return {"color": [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb],
            "roughness": roughness, "metallic": metallic}


PALETTE = {
    SOFFIT: finish((164, 156, 148), .92),
    FLAG: finish((142, 136, 128), .94),
    BAND: finish((183, 180, 174), .87),
    UPRIGHT: finish((182, 178, 172), .90),
    RAIL: finish((75, 74, 68), .65, .27),
    SHOE: finish((94, 90, 82), .78, .30)
}


def balcony_sections():
    """Return four slab footprints and the three independently registered storeys in each."""
    return json.loads(DATA.read_text())["stack_geometry"]


def outline(record, inset, arc_count):
    """Trace the street-facing U. The square ends abut the shared centre pier."""
    left, right = record["x_west_east_m"]
    left, right = left + inset, right - inset
    street = record["street_edge_y_m"] + inset
    back = record["back_attachment_y_m"]
    west_radius, east_radius = [max(0., r - inset) for r in record["front_radius_west_east_m"]]
    points = [(left, back)]
    for x, radius, angles in [(left + west_radius, west_radius, (180, 270)),
                              (right - east_radius, east_radius, (270, 360))]:
        if radius == 0:
            points.append((x, street))
            continue
        for j in range(arc_count + 1):
            angle = math.radians(angles[0] + j * (angles[1] - angles[0]) / arc_count)
            points.append((x + radius * math.cos(angle), street + radius + radius * math.sin(angle)))
    return points + [(right, back)]


def edge_strip(record, width, segments):
    outer = Polygon(outline(record, 0., segments))
    inner = Polygon(outline(record, width, segments))
    # Both polygons share the rear line so only the visible U survives subtraction.
    return orient(outer.difference(inner), sign=1.0)


def add_balconies(builder, lod=False):
    """Use True for the distant mesh. Slabs, four open slots and every rounded return persist."""
    data = json.loads(DATA.read_text())
    section = data["nominal_rail_section_m"]
    coarse = lod is True or lod in ("lod", "low", "far", "distant")
    segments = 5 if coarse else 13
    for stack in data["stack_geometry"]:
        left, right = stack["x_west_east_m"]
        street, back = stack["street_edge_y_m"], stack["back_attachment_y_m"]
        midpoint = stack["front_upright_x_m"]
        slab = orient(Polygon(outline(stack, section["inner_return_rail_web_thickness"], segments)), sign=1.0)
        edge = edge_strip(stack, section["inner_return_rail_web_thickness"], segments)
        top_path = outline(stack, .040, segments)
        for level, z in enumerate(stack["storey_slab_soffits_z_m"], 1):
            name = f"JKK balcony {stack['column']}{level}"
            def add(poly, bottom, top, material, label):
                builder.plan_prism(poly, z + bottom, z + top, material, f"{name} | {label}")
            add(slab, 0, section["deck_thickness"], SOFFIT, "cantilevered slab")
            add(edge, 0., section["deck_thickness"] + .007, BAND, "pale slab fascia")
            if not coarse:
                add(orient(Polygon(outline(stack,.095,segments)), sign=1), .125, .134, FLAG, "deck surface")
            for n, (height, size) in enumerate(zip(section["four_horizontal_solid_band_lower_edges_above_soffit"],
                                                   section["four_horizontal_solid_band_heights"]), 1):
                add(edge, height, height + size, BAND, f"continuous solid band {n}")
            for x, y, width, depth, label in [
                    (midpoint, street + .050, section["middle_plaster_post_width"], .103, "front upright"),
                    (left + .052, back - .095, .103, .146, "west return wall post"),
                    (right - .052, back - .095, .103, .146, "east return wall post")]:
                builder.box((x,y,z+.478), (width,depth,.710), UPRIGHT,label=f"{name} | {label}")
            cap_height = section["upper_rail_centre_height"]
            builder.tube([(x,y,z+cap_height) for x,y in top_path], .023, RAIL,
                         6 if coarse else 12, f"{name} | handrail around the open edge")
            for n,(x,y) in enumerate([(left+.040,back-.09), (left+.30*(right-left),street+.040),
                                      (midpoint,street+.040), (right-.23*(right-left),street+.040),
                                      (right-.040,back-.09)],1):
                builder.box((x,y,z+.897), (.024,.028,.150), RAIL, label=f"{name} | handrail standard {n}")
                if not coarse:
                    builder.box((x,y,z+.839), (.045,.051,.015), SHOE, label=f"{name} | socket {n}")
