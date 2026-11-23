"""Check the freestanding louvred enclosure from three winter photographic baselines."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import numpy as np

HERE = Path(__file__).resolve().parent
SCENE = HERE.parents[1] / 'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact/glb_triangles.py'
SerialScene = runpy.run_path(str(SCENE))['SerialScene']

def ray(camera, pixel):
    r = np.array(camera['R']).T @ np.linalg.solve(camera['K'], [*pixel,1])
    return r/np.linalg.norm(r)

def result(file):
    scene = SerialScene(file)
    measure = json.loads((HERE/'grille-third-station.json').read_bytes())
    cams = json.loads((HERE/'street-cameras.json').read_bytes())['cameras']
    cams['east'] = measure['2015_oblique_camera']
    features = next(value for value in measure.values() if isinstance(value,dict) and 'top left' in value)
    corners=[np.asarray(features[k]['three_station_xyz']) for k in ('top left','top right','bottom left','bottom right')]
    bounds=np.asarray(corners)
    front_y=float(np.mean(bounds[:,1]))
    left,right=float(np.mean(bounds[[0,2],0])),float(np.mean(bounds[[1,3],0]))
    bottom,top=float(np.mean(bounds[[2,3],2])),float(np.mean(bounds[[0,1],2]))
    result = {}
    for key in ('2015-12-front','2021-01-front','east'):
        camera = cams[key]
        points = np.asarray([features[k]['native_pixels'][key] for k in ('top left','top right','bottom left','bottom right')])
        tl,tr,bl,br = points
        hits = []
        for v in (.14,.32,.51,.69,.86):
            for u in (.18,.40,.62,.82):
                pixel = (1-v)*((1-u)*tl+u*tr)+v*((1-u)*bl+u*br)
                direction=ray(camera,pixel)
                eye=np.asarray(camera['eye'])
                projected=eye+direction*(front_y-eye[1])/direction[1]
                crosses_front=left<=projected[0]<=right and bottom<=projected[2]<=top
                hit = scene.ray(eye,direction,60.)
                correct = False
                if hit:
                    x,y,z = hit['point_enu_m']
                    correct = 7.66<x<8.92 and 2.75<y<3.13 and 2.43<z<3.40 and any(
                        t in hit['material'] for t in ('louvre','stairwell','iron drain','weathered pale sill'))
                through=bool(hit and crosses_front and not correct and hit['point_enu_m'][1]>front_y+.13 and 'ochre roughcast' in hit['material'])
                hits.append({'native_pixel':pixel.round(3).tolist(),'crosses_measured_front':bool(crosses_front),
                             'hit_enclosure':correct,'through_open_slats_to_wall':through,'first_surface':hit})
        result[key]={'sample_count':len(hits),'on_enclosure':sum(h['hit_enclosure'] for h in hits),'open_to_masonry':sum(h['through_open_slats_to_wall'] for h in hits),'samples':hits}
    return {'asset':scene.asset,'three_station_controls_sha256':hashlib.sha256((HERE/'grille-third-station.json').read_bytes()).hexdigest(),
            'method':'Twenty points within the independently measured inset quadrilateral per view. First triangle, material and bounded physical location identify a direct hit. A separate counter records sightlines through the measured enclosure front that first hit the masonry behind. The backing is only partly occupied by the condenser case. No nearest-pixel search.','views':result}

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('mesh',type=Path);cli.add_argument('out',type=Path)
    a=cli.parse_args();report=result(a.mesh);a.out.write_text(json.dumps(report,indent=2)+'\n')
    print([s['on_enclosure'] for s in report['views'].values()])
