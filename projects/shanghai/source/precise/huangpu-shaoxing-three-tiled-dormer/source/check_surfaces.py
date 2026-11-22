"""Fire rays through the exported GLB towards each casement, tile course, roof margin and gutter."""
import os,runpy
from pathlib import Path
from gable import GLASS,FRAME,WALL,TILE,EDGE,GUTTER,roof_y,roof_z
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']

def check(reader):
    rows=[]
    def check_point(label,xyz,direction,material,limit):
        hit=reader.ray(xyz,direction,limit)
        passed=(hit is None) if material is None else bool(hit and hit['material']==material)
        rows.append(dict(part=label,origin=xyz,direction=direction,expected_material=material,hit=hit,passed=passed))
    for x in (-.367,-.137,.137,.367):
        for z in (1.04,1.46,1.82):
            check_point('Recessed individual pane',[x,-1.02,z],[0,1,0],GLASS,1.0)
        for z in (1.266,1.655):
            check_point('Horizontal glazing bar',[x,-1.02,z],[0,1,0],FRAME,1.0)
    for x in (-.504,-.252,0,.252,.504):
        for z in (1.04,1.47,1.84):
            check_point('Casement jamb or glazing bar',[x,-1.02,z],[0,1,0],FRAME,1.0)
    for x in (-1.223,-.855,.855,1.223):
        for row in range(14):
            t=(row+.45)/14
            check_point('Overlapping roof tile',[x,roof_y(t),roof_z(t)+.30],[0,0,-1],TILE,.52)
    for x in (-1.365,1.365):
        for t in (.115,.33,.62,.89):
            check_point('Pale curved verge',[x,roof_y(t),roof_z(t)+.30],[0,0,-1],EDGE,.52)
    for x in (-1,-.5,0,.5,1):
        check_point('Gutter lip',[x,-.94,.198],[0,1,0],GUTTER,.28)
        check_point('Space above gutter',[x,-.94,.32],[0,1,0],None,.17)
    return dict(passed=all(row['passed'] for row in rows),samples=rows)
