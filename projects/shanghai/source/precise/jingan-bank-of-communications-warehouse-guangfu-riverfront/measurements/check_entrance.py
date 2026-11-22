"""Test actual first intersections on the Guang Er Warehouse south entrance or assembled warehouse."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import polylabel

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
import south_entrance as portal


def check(path, frame=None, whole=False):
    xz,width,y0=portal.image_frame(frame)
    scene=SerialScene(path); observed=[]
    def ray(label,uv,kind,allowed,maximum=.25):
        x,z=xz(uv)
        start=[float(x),y0-.18*width,float(z)]
        hit=scene.ray(start,[0.,1.,0.],width*(.18+maximum))
        actual=hit['material'] if hit else None
        if allowed=='opening':
            passed=(actual is None or (whole and actual not in portal.PALETTE))
        else:passed=actual in allowed
        observed.append(dict(label=label,purpose=kind,reference_uv=np.round(np.array(uv,dtype=float),3).tolist(),first_material=actual,
                             first_world_position=hit['point_enu_m'] if hit else None,passed=bool(passed)))
    for row in portal.LETTERS:
        for n,field in enumerate(row['polygons'],1):
            poly=Polygon(field['outer'],field['holes']);spot=polylabel(poly,.045)
            # Contours smaller than a native pixel cannot establish a reliable *separate* photographed stroke.
            if poly.area<.50:continue
            name=f"{row['text']} / stroke {n}"
            metallic=portal.BRONZE if row['source_view']=='oblique' else portal.GOLD
            ray(name,spot.coords[0],'raised letter face',[metallic])
            for i,hole in enumerate(poly.interiors,1):
                gap=Polygon(hole);pt=polylabel(gap,.045)
                if gap.area>.6 and not any(Polygon(q['outer'],q['holes']).covers(pt) for q in row['polygons']):
                    ray(f'{name}, counter {i}',pt.coords[0],'clear cut through applied lettering',[portal.STONE])
    for u in (397.5,417.,443.,455.8,462.,473.,613.7,622.,628.,655.,681.,687.):
        for v in (265.,382.,488.,558.,601.,688.,715.):
            if v<577 and 471<u<614:continue
            if v>=615 and 455<=u<=630:continue
            ray('Tower shaft',[u,v],'stone strips',[portal.STONE])
    for u,v in [(406,164),(426,165),(450,164),(466,173),(480,182),(516,173),(540,166),(569,173),
                (588,183),(619,173),(637,164),(669,168),(684,171)]:
        ray('Stepped top cap',[u,v],'stone on irregular silhouette',[portal.STONE])
    for u in (465.,486.,531.,550.,583.,603.,618.):
        ray('Three-window sill',[u,583.2],'projecting pale stone sill',[portal.EDGE])
    for u in (464.,621.):
        for v in (634.,651.,671.,696.,725.):ray('Splayed side',[u,v],'mitered entrance frame',[portal.EDGE])
    for u in (487.,512.,538.,566.,599.):
        for z,material in [(623.,portal.EDGE),(637.,portal.BLACK),(648.5,portal.EDGE)]:
            ray('Entrance head',[u,z],'three independently visible horizontal bands',[material])
    for u in (478.,508.,539.,570.,607.):
        for v in (661.,686.,713.,730.):ray('Street passage',[u,v],'clear opening','opening',maximum=.14)
    for left,right in portal.OBS['window_clear_cells']:
        for top,sill in portal.OBS['window_rows_top_sill']:
            for frac in (.24,.7):
                ray('Central steel window opening',[left+(right-left)*frac,top+.52*(sill-top)],'opening in masonry','opening',maximum=.13)
    return dict(passed=all(a['passed']for a in observed),asset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                checks=len(observed),first_intersections='All materials and meshes, before the indicated maximum depth.',
                by_purpose=dict(Counter(a['purpose']for a in observed)),failures=[a for a in observed if not a['passed']],results=observed)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--width',type=float,help='Explicit width for pre-calibration component checks.')
    parser.add_argument('--whole',action='store_true');args=parser.parse_args()
    report=check(args.asset,{'clear_width_m':args.width}if args.width is not None else None,args.whole)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n')
    print(report['checks'],len(report['failures']),report['failures'][:3])
    raise SystemExit(0 if report['passed'] else 1)
