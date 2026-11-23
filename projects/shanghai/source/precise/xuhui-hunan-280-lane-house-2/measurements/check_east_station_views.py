"""Cast independent interior/window and wall observations in the two additional eastern views."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np

HERE = Path(__file__).resolve().parent
HELPER = HERE.parents[3] / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'

# Native 800x600, not the fitted jamb corners. The wall shadow is included in the
# photographs but wires and intervening trees are deliberately omitted.
PICKS = {
    'east-1512': {
        'upper bay E5': [('opening', [460,62]), ('opening',[476,48])],
        'upper bay E4': [('opening',[459,155]), ('opening',[487,128])],
        'upper bay E3': [('opening',[458,249]), ('opening',[479,231])],
        'upper bay E2': [('opening',[470,360]), ('opening',[487,344])],
        'ground bay E1': [('opening',[460,470]), ('opening',[462,491])],
        'C1 load-bearing jamb and tiled sill': [('wall',[434,478]), ('tile',[396,512])],
        'E2/E3 spandrel': [('wall',[465,300])],
        'E3/E4 spandrel': [('wall',[474,189])],
        'east return': [('wall',[607,113]), ('wall',[620,180])],
    },
    'east-2002': {
        'E5': [('opening',[380,181]), ('opening',[398,169])],
        'E4': [('opening',[382,251]), ('opening',[396,240])],
        'E1': [('opening',[378,507]), ('opening',[389,509])],
        'E4/E5 spandrel': [('wall',[381,209])],
        'E5 eastern pier below roof': [('wall',[414,141])],
        'east return': [('wall',[463,145]), ('wall',[505,152])],
    }
}
MATERIALS={'opening':('reflection','steel joinery','replacement frame','grille'), 'wall':('roughcast','lower render'), 'tile':('sill tiles','sill bedding')}


def inspect(path):
    scene=runpy.run_path(str(HELPER))['SerialScene'](path)
    archive=json.loads((HERE/'eastern-window-planes.json').read_bytes())['eastern_roof_and_windows']['east_cameras']
    rows=[]
    for station,groups in PICKS.items():
        camera=archive[station.split('-')[1]]
        C,R,K=(np.asarray(camera[k]) for k in ('C','R','K'))
        for label,marks in groups.items():
            for cls,uv in marks:
                v=R.T@np.linalg.solve(K,[*uv,1]);v/=np.linalg.norm(v)
                h=scene.ray(C,v,100.);mat=h['material'] if h else None
                rows.append({'station':station,'label':label,'observed_pixel':uv,'group':cls,'hit_material':mat,
                             'triangle':h['triangle_index'] if h else None,'matches_observation':bool(mat and any(k in mat for k in MATERIALS[cls]))})
    return {'mesh':path.name,'mesh_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'registration_sha256':hashlib.sha256((HERE/'eastern-window-planes.json').read_bytes()).hexdigest(),
            'frame':'Native 800x600; two added eastern views. Window and adjacent wall interiors excluded from the input of the ten-station fit.',
            'matched':sum(r['matches_observation'] for r in rows),'total':len(rows),'rays':rows}


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path)
    args=cli.parse_args();args.output.write_text(json.dumps(inspect(args.mesh),indent=2)+'\n')
