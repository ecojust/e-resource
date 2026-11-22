"""Compare unchanged image pixels with the nearest surface of the actual mesh."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / 'xuhui-pathe-records-office/measurements/city-contact'),
                str(HERE.parent / 'source')]
from glb_triangles import SerialScene
from pointed_piers import STONE, EDGE, BOWL, LEAF, RECESS, SEAM

SAMPLES = [
    ('a',4,'inner lancet',(RECESS, SEAM),[(2418,1994),(2420,2038)]),
    ('a',4,'projecting sill',(EDGE,),[(2421,2098),(2422,2118)]),
    ('a',4,'finial silhouette',(STONE,),[(2406,468),(2398,497)]),
    ('a',2,'arch above shop fascia',(EDGE, RECESS, SEAM),[(1401,1950),(1402,1957)]),
    ('c',7,'folded shaft',(STONE,),[(1007,151),(999,243),(984,598),(982,950),(979,1230)]),
    ('c',7,'stone flank',(STONE, SEAM),[(1036,1767),(929,1720),(1048,1575)]),
    ('c',7,'dark terminal',(BOWL,LEAF),[(984,1369),(947,1366),(992,1388)]),
    ('c',7,'blind lancet',(RECESS, SEAM),[(960,2520),(960,2623),(960,2701),(963,2820)]),
    ('c',7,'stepped sill',(EDGE,),[(962,2914),(960,2950),(957,2992)]),
    ('c',8,'blind lancet',(RECESS, SEAM),[(1960,2570),(1960,2675),(1975,2748)]),
    ('c',9,'blind lancet at oblique angle',(RECESS, SEAM),[(2521,2646),(2534,2720),(2538,2812)]),
    ('c',10,'blind lancet at oblique angle',(RECESS, SEAM),[(2899,2710),(2905,2774),(2912,2882)]),
    ('c',11,'blind lancet at oblique angle',(RECESS, SEAM),[(3168,2770),(3172,2820),(3182,2894)]),
    ('204',10,'blind lancet',(RECESS, SEAM),[(502,1917),(490,2080)]),
    ('204',10,'outer jamb',(EDGE,),[(461,1940)]),
    ('204',10,'stepped sill',(EDGE,),[(486,2151),(479,2180),(479,2241)]),
    ('204',11,'blind lancet',(RECESS, SEAM),[(1443,1970),(1448,2073)]),
    ('204',11,'outer jamb',(EDGE,),[(1405,1947)]),
    ('204',11,'stepped sill',(EDGE,),[(1456,2140),(1467,2194)]),
    ('204',11,'crown silhouette',(STONE,),[(1232,331)]),
    ('204',11,'dark terminal',(BOWL,LEAF),[(1320,1051)]),
]


def evaluate(mesh_path):
    observations = json.loads((HERE / 'pointed-piers-photo-evidence.json').read_bytes())
    layout = json.loads((HERE / 'street-frontage-layout.json').read_bytes())
    closeup = json.loads((HERE / '204-front-metric-camera.json').read_bytes())
    cameras = {}
    for key, source in [('a','gao00'),('c','gao08')]:
        s = observations['sources'][source]['size'][0] / 512.
        cameras[key] = np.diag([s,s,1.]) @ observations['camera_512'][key]
    left, right = np.asarray(layout['pier_tip_axes_m'][-2:])
    t = right-left
    span = np.linalg.norm(t)
    t /= span
    n = np.array([-t[1],t[0]])
    k = span/closeup['width_m']
    to_world = np.eye(4)
    to_world[:2,0], to_world[:2,1] = k*t, k*n
    to_world[2,2] = k
    to_world[:2,3] = left + .26*n
    cameras['204'] = np.asarray(closeup['local_P']) @ np.linalg.inv(to_world)
    scene = SerialScene(mesh_path)
    rows = []
    for source, station, feature, expected, pixels in SAMPLES:
        P = cameras[source]
        eye = -np.linalg.solve(P[:,:3], P[:,3])
        for u,v in pixels:
            ray = np.linalg.solve(P[:,:3], [u,v,1])
            hit = scene.ray(eye, ray, 160)
            actual = hit['material'] if hit else None
            rows.append(dict(source=source,station=station,feature=feature,native_px=[u,v],
                             expected=list(expected),first_material=actual,matches=actual in expected))
    point = np.r_[right, layout['height_m']['tip'],1.]
    image = cameras['204'] @ point
    projected = image[:2]/image[2]
    measured = np.array([1225,278])
    return dict(mesh_sha256=hashlib.sha256(mesh_path.read_bytes()).hexdigest(),total=len(rows),
                direct_first_surface_matches=sum(r['matches'] for r in rows),rows=rows,
                closeup_204_to_world=to_world.tolist(),closeup_204_common_span_m=span,
                right_finial_tip_204=dict(measured=measured.tolist(),reprojected=projected.round(2).tolist(),
                                          error_px=float(np.linalg.norm(projected-measured))),
                interpretation='Unadjusted rays at the original image pixels. The street-angle image has shallow intersections at the three southern piers, particularly across the narrow lancets. The separate entrance camera gives an additional view of the terminal and low niches. The two calibrations differ at the top silhouette. All disagreements are retained.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    result=evaluate(args.mesh)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    print(result['direct_first_surface_matches'],result['total'],result['right_finial_tip_204'])
