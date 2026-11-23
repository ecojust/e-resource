"""Measure the lettering's bearing on the actual front brick triangles from both editions."""
import argparse
import json
from pathlib import Path
import statistics

from shapely.geometry import Polygon
from shapely.ops import unary_union
from check_inscription_glb import decode_groups, digest, inspect

def profile(mesh,order):
    groups=decode_groups(mesh,order)
    held={}
    wall=[]
    for label,material,triangles in groups:
        if label.startswith('street face/'):
            assert material=='Furu | dark red facing brick'
            wall.extend(t for t in triangles if max(abs(v[1]) for v in t)<1e-6)
        elif label.startswith('archival hospital name/'):
            assert material=='Furu | chalk grey cement'
            held.setdefault(label.rsplit('/',1)[1],[]).extend(triangles)
    def area(triangles):
        return unary_union([Polygon([(x,z) for x,y,z in t]) for t in triangles])
    wall_face=area(wall)
    projection=inspect(mesh,order)
    observed=projection['glyphs']['district-archive']
    rows=[]
    for obs in observed:
        ch=obs['character'];triangles=held[ch]
        coords=[v for t in triangles for v in t]
        low=min(v[1] for v in coords);high=max(v[1] for v in coords)
        front=area([t for t in triangles if max(abs(v[1]-low) for v in t)<1e-6])
        assert not front.is_empty and front.area>0
        outside=front.difference(wall_face).area
        rows.append(dict(character=ch,face_area_m2=front.area,
                         outside_brick_area_m2=outside,
                         supported_area_ratio=(front.area-outside)/front.area,
                         beyond_right_edge_m=max(0.,front.bounds[2]-wall_face.bounds[2]),
                         gap_behind_m=max(0.,-high),embedded_m=max(0.,high),
                         archive_box_centre_error_px=obs['centre_error_px'],archive_box_iou=obs['boxes_iou']))
    residuals=[r['archive_box_centre_error_px'] for r in rows]
    return dict(mesh_sha256=digest(mesh),box_centre_median_px=statistics.median(residuals),
                box_centre_max_px=max(residuals),groups=len(groups),letters=rows)

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for word in ('old','new','out'):cli.add_argument(word,type=Path)
    args=cli.parse_args()
    result={}
    for role in ('full','lod'):
        result[role]={}
        for tag,folder in [('previous',args.old),('corrected',args.new)]:
            proof=profile(folder/(role+'-source.glb'),folder/(role+'-source.geometry.json'))
            result[role][tag]=proof
            if tag=='corrected':
                assert all(r['outside_brick_area_m2']<1e-8 and r['gap_behind_m']==0 and r['embedded_m']>0 for r in proof['letters'])
        assert result[role]['corrected']['box_centre_median_px']<result[role]['previous']['box_centre_median_px']
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
