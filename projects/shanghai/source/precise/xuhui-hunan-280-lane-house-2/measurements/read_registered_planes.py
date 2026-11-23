"""Recover the straight walls, their limits and the pipe's offset from the street datum."""
import argparse
import json
from pathlib import Path

import numpy as np

from register_house import Camera

HERE = Path(__file__).resolve().parent


def read():
    result = json.loads((HERE / "house-cameras.json").read_bytes())
    obs = json.loads((HERE / "flat-window-observations.json").read_bytes())["stations"]
    outline = json.loads((HERE / "face-outlines.json").read_bytes())
    inner = Camera("84")
    directions = []
    for name, quad in obs["43052484"]["windows"].items():
        if not name.startswith("E"):
            continue
        for u, v in [(0, 1), (3, 2)]:
            trace = np.cross(inner.ray(quad[u]), inner.ray(quad[v]))
            tangent = np.array([-trace[1], trace[0]])
            tangent /= np.linalg.norm(tangent)
            if tangent @ inner.R[0, :2] < 0:
                tangent = -tangent
            directions.append(tangent)
    tangent = np.median(directions, axis=0)
    tangent /= np.linalg.norm(tangent)
    normal = [tangent[1], -tangent[0], 0.]
    outer_jamb = result["points"]["j2_0_0"]
    oblique = outline["inner_oblique_wall"]
    pipe = [inner.plane(uv, outer_jamb, normal).tolist() for uv in oblique["pipe_axis"]]
    pic = Camera("86")
    return {
        "datum": "Pavement under the left jamb of A2–A5, Y=0 south wall. Pipe axis intersects a different facade.",
        "coordinate_system": result["axes"],
        "south_wall": {"plane_origin": [0., 0., 0.], "normal":[0., 1., 0.],
                       "upper_west_roof_corner_at_y0": pic.wall(outline["south_front"]["upper_west_corner"]).tolist(),
                       "west_foot_read_at_y0":pic.wall(outline["south_front"]["street_base_west"]).tolist()},
        "lane_wall": {"station": "84", "photo_right_unit_xy": tangent.tolist(),
                      "photo_right_azimuth_deg": float((result["x_azimuth_deg"]-np.degrees(np.arctan2(tangent[1],tangent[0])))%360),
                      "plane_anchor": outer_jamb, "plane_normal": normal,
                      "pipe_projection_method": "Wall anchor at outer curved jamb. Iron stands proud of wall by its radius; wall projections alone provide a horizontal offset estimate.",
                      "pipe_wall_xyz": pipe,
                      "estimated_pipe_foot_xy":np.median(np.array(pipe)[:,:2],axis=0).tolist(),
                      "far_corner": inner.plane(oblique["outer_visible_left"],outer_jamb,normal).tolist()},
        "east_return": {"first_estimate": "eastern-end-validation.json", "current_result": "eastern-roof-four-stations.json",
                        "interpretation": "The independent four-station roof check follows the measured 16-degree E-bank turn. Adopt the four-station corner X 13.36, Y 1.17, Z 18.20 m. Two-station east-only assessment assumed parallel windows and is superseded. Three narrow east openings are separately visible. Trees, court wall and neighbouring red roof obscure the lower and rear parts."},
    }


if __name__=="__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("output",type=Path)
    args = cli.parse_args()
    args.output.write_text(json.dumps(read(),indent=2)+"\n")
