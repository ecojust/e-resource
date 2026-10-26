#!/usr/bin/env python3
"""Conservative slab projection controls; no Museum raw is loaded."""
import argparse,json
from pathlib import Path
from shapely.geometry import box as rectangle
from audit_repair_envelope import slab_projection_hull,projected_footprint
from test_preservation import box
from modern_mesh import filemeta


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists()
    t=box('closed-prism',0.,1.).triangles_enu
    hull=slab_projection_hull(t,.25,.75)
    rows=[
        {'case':'no_original_vertices_in_slab_but_cap_interior_enclosed','passed':hull is not None and hull.area==1.},
        {'case':'interior_xy_point_cannot_be_false_clear','passed':not hull.disjoint(rectangle(.2,.2,.8,.8))},
        {'case':'positive_xy_gap_clears','passed':hull.disjoint(rectangle(2.,0.,3.,1.))},
        {'case':'exact_boundary_contact_is_not_clear','passed':not hull.disjoint(rectangle(1.,0.,2.,1.))},
        {'case':'true_z_disjoint_interval_is_empty','passed':slab_projection_hull(t,2.,3.)is None},
        {'case':'actual_closed_solid_xy_footprint_fills_interior','passed':projected_footprint(t).area==1.},
    ]
    passed=all(r['passed']for r in rows)
    result={'schema':'museum-geometry-v2-repair-envelope-synthetic-tests-v1','synthetic_tests_passed':passed,
        'test_count':len(rows),'tests':rows,'actual_museum_geometry_loaded':False,
        'checker_files':[filemeta(__file__),filemeta(Path(__file__).parent/'audit_repair_envelope.py'),filemeta(Path(__file__).parent/'test_preservation.py')]}
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'report':filemeta(a.output),'passed':passed}))
    raise SystemExit(0 if passed else 1)


if __name__=='__main__':main()
