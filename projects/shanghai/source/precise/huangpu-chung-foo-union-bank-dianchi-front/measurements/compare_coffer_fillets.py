"""Compare the stereo joist intersections with the separate single-photo fillet traces."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d, map_coordinates
from scipy.optimize import least_squares
from stereo_north_soffit import source_pixel

HERE = Path(__file__).resolve().parent


def address(uv):
    return least_squares(lambda x: source_pixel("close", *x) - uv, uv).x


def bright_and_dark_edges(photo, rows):
    # Compare both sides in a rectified transverse interval, without naming the darkest flute an axis.
    u_rect = np.arange(700., 1660.)
    result = {}
    for t in rows:
        col = np.array([source_pixel("close", s, t) for s in u_rect])
        profile = map_coordinates(photo, [col[:, 1], col[:, 0]], order=1)
        grad = np.gradient(gaussian_filter1d(profile, 1.5))
        bounds = []
        for left, right in [(990, 1050), (1315, 1385)]:
            keep = (left <= u_rect) & (u_rect <= right)
            s = u_rect[keep]
            bounds.append({"negative_edge_s": s[grad[keep].argmin()], "negative_gradient": grad[keep].min(),
                           "positive_edge_s": s[grad[keep].argmax()], "positive_gradient": grad[keep].max()})
        result[str(t)] = bounds
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("near_original",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    args = ap.parse_args()
    original = args.near_original.read_bytes()
    source = json.loads((HERE/"coffered-soffit.json").read_bytes())
    assert hashlib.sha256(original).hexdigest() == source["source_sha256"]
    raw = json.loads((HERE/"north-soffit-stereo.json").read_bytes())
    im = np.array(Image.open(args.near_original).convert("L"), float)
    single = [np.asarray(r["highlights_px"]) for r in source["transverse_rows"]]
    med = [np.median([address(uv)[1] for uv in row]) for row in single]
    data = {"source_2015_sha256":source["source_sha256"],"source_2017_sha256":raw["verified_original_profiles"]["wide"]["source_sha256"],
            "stereo_measurement_file":"north-soffit-stereo.json",
            "coordinate_units":"Original pixels (u,v). Rectified horizontal s and transverse t use the camera vanishing points. Metres use the wall frame.",
            "transverse_edge_identification":[
                {"member":"outer transverse beam","stereo_dark_step_t":1118.8,"near_bright_fillet_median_t":med[0],
                 "difference_px":med[0]-1118.8,"classification":"distinct adjacent edges of the same moulded band"},
                {"member":"inner transverse beam","stereo_dark_step_t":1176.8,"near_bright_fillet_median_t":med[1],
                 "difference_px":med[1]-1176.8,"classification":"distinct adjacent edges of the same moulded band"}],
            "longitudinal_position_method":"A local visual centre of the joist shadow strip was used in each crossing, measured outside the transverse fillet and interpolated across it. These points are neither the left edge nor the right edge of the joist. The deepest edge is laterally less certain as the joist tapers.",
            "pick_tolerance_original_pixels":{"near_joist_horizontal_centre":[4,9],"near_transverse_edge_v":[1,2],"wide_joist_horizontal_centre":[1.5,3],"wide_transverse_edge_v":[1,2],
              "meaning":"Estimated visual selection widths in the originals, separate from camera/calibration error. At the inner ending the near horizontal half-width grows to 10 px."},
            "crossings":raw["intersection_picks"],
            "inner_tip_close_px":source["inner_beam_ends_px"],
            "inner_tip_rectified_st":[address(p).tolist() for p in source["inner_beam_ends_px"]],
            "rear_dark_pick_original_px":[row["sample_px"] for row in source["longitudinal_ribs"][2:4]],
            "rear_dark_pick_rectified_st":[address(row["sample_px"]).tolist() for row in source["longitudinal_ribs"][2:4]],
            "near_lateral_edge_profile_by_rectified_t":bright_and_dark_edges(im, [1112,1166,1172,1204,1207,1210,1216,1224,1227]),
            "rear_tip_comparison":"At t≈1204–1207 the imaged joists extend over roughly 35–45 px. The previously selected near dark samples sit on the west side of the east joist and the east side of the west joist. Their approximately 10–15 px displacement from the centre trace fits inside the joist width. At t≈1223–1226 the tips disappear; they are downstream from the inner transverse edge at t=1196.8 by 27–29 image pixels. This longitudinal difference is a distinct projecting beam end, not the transverse moulding width. The west rear intersection is occluded by the capitals in the wide image.",
            "adopted_dimensions_m":{"front_beam_z": [6.85,6.86],"back_transverse_z":6.93,"inner_visible_moulding_z":6.98,
                "front_to_back_transverse_y":raw["transverse_spacing_in_depth_m"],
                "shaft_row_to_inner_moulding":raw["innermost_traced_edge_inside_shaft_axis_m"]},
            "scope":"Image evidence measures these exposed edges; the concealed depth of individual coffer recesses remains an estimate."}
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")


if __name__=="__main__":
    main()
