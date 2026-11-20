"""Low gridded cover observed on contemporary overhead photographs of Jiangwan museum."""
from shapely import box


def add_east_hall_cover(builder, params, roof_polygon, probes):
    center_x, center_y = params["center_enu_m"]
    width, depth = params["size_m"]
    west, south = center_x - width / 2, center_y - depth / 2
    east, north = west + width, south + depth
    rim = params["rim_m"]
    columns, rows = params["column_count"], params["row_count"]
    panel_z = params["estimated_panel_top_m"]
    roof_z = params["existing_roof_top_m"]
    top_z = params["estimated_frame_top_m"]
    # A continuous curb crosses the original roof surface by 2cm, leaving all
    # surrounding slab, parapets, courtyard walls and adjoining roofs untouched.
    footprint = box(west, south, east, north)
    if not roof_polygon.covers(footprint.buffer(0.5)):
        raise ValueError("Roof cover extends beyond the selected roof")
    builder.plan_prism(footprint, roof_z - 0.02, panel_z, "cover panel", "east hall / shallow rectangular roof cover")
    clear_width = width - rim * 2
    clear_depth = depth - rim * 2
    inner_frame = params["divider_m"]
    lattice = footprint
    for column in range(columns):
        x0 = west + rim + clear_width * column / columns
        x1 = west + rim + clear_width * (column + 1) / columns
        for row in range(rows):
            y0 = south + rim + clear_depth * row / rows
            y1 = south + rim + clear_depth * (row + 1) / rows
            pane = box(
                x0 + (inner_frame / 2 if column else 0),
                y0 + (inner_frame / 2 if row else 0),
                x1 - (inner_frame / 2 if column < columns - 1 else 0),
                y1 - (inner_frame / 2 if row < rows - 1 else 0),
            )
            lattice = lattice.difference(pane)
            probes.append({"kind": "ray", "label": f"east overhead cover / panel {column + 1}-{row + 1}", "origin": [pane.centroid.x, pane.centroid.y, top_z + .5], "direction": [0, 0, -1], "max_distance": 1.0, "material": "cover panel"})
    builder.plan_prism(lattice, panel_z - .02, top_z, "cover frame", "east hall / continuous raised perimeter and subdividing frame")
    for x, y, label in [(west + rim / 2, center_y, "west edge"), (east - rim / 2, center_y, "east edge"), (center_x, south + rim / 2, "south edge"), (center_x, north - rim / 2, "north edge"), (west + rim + clear_width / columns, south + clear_depth * .27, "north–south division"), (center_x, center_y, "west–east division")]:
        probes.append({"kind": "ray", "label": "east overhead cover / " + label, "origin": [x, y, top_z + .5], "direction": [0, 0, -1], "max_distance": 1.0, "material": "cover frame"})
    for x, y in [(west - .4, center_y), (east + .4, center_y), (center_x, south - .4), (center_x, north + .4)]:
        probes.append({"kind": "ray", "label": "existing flat roof beside the gridded cover", "origin": [x, y, top_z + .5], "direction": [0, 0, -1], "max_distance": 1.0, "material": "roof concrete"})
    return {"kind": "contemporary_east_hall_overhead_cover", **params}
