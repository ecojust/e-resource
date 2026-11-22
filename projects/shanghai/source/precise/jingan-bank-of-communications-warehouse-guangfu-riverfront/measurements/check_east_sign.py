"""Read all triangles of the exterior return wall and test the two dated sign rows against the traced strokes."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import polylabel
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
import east_wall_sign as component

def test(asset,whole=False):
    scene=SerialScene(asset);layout=json.loads((component.HERE/'riverfront-layout.json').read_bytes())
    mapper,n=component.map_to_wall(layout);direction=[-n[0],-n[1],0.]
    rows=[]
    def ray(label,sz,solid):
        origin=np.array(mapper(*sz,.19));hit=scene.ray(origin,direction,.25)
        material=hit['material'] if hit else None
        expected_material = component.GOLD if solid else ('Guangfu | gable render' if whole else None)
        okay = material == expected_material
        rows.append(dict(part=label,wall_s_z=np.round(sz,4).tolist(),expected='yellow face'if solid else 'unlettered wall',first_material=material,passed=bool(okay),first_hit_m=hit['point_enu_m']if hit else None))
    for i,(r,word,multi) in enumerate(component.shaped_rows(),1):
        for piece in ([multi] if multi.geom_type=='Polygon'else multi.geoms):
            if piece.area<.00022:continue
            pt=polylabel(piece,tolerance=.0009)
            ray(f'{r} {i} {word}',pt.coords[0],True)
            for hole in piece.interiors:
                ring=Polygon(hole)
                if ring.area>.0009:
                    pt=polylabel(ring,.001)
                    if not multi.covers(pt):ray(f'{r} {i} counter',pt.coords[0],False)
    for s in np.linspace(1.4,5.4,5):
        for z in (15.64,17.88):ray('adjacent stone',np.array([s,z]),False)
    return dict(passed=all(z['passed']for z in rows),checks=len(rows),asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),
                camera_checks='19 ground, 34 aerial, with 18 before restoration.',results=rows,failures=[z for z in rows if not z['passed']])
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('asset',type=Path);parser.add_argument('out',type=Path);parser.add_argument('--whole',action='store_true');a=parser.parse_args()
    report=test(a.asset,a.whole);a.out.write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n');print(report['checks'],len(report['failures']),report['failures'][:2]);raise SystemExit(not report['passed'])
