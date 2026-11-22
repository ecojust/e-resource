"""Use the original 2022 image pixels to test the visible components against the finished GLB."""
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from entrance_recess import ARRIS,BOX,FLANGE,GLASS,LABEL,RENDER,SMALL_LABEL,WOOD

CLASSES=[
    (RENDER,[(152,440),(166,490),(203,530),(180,410)]),
    ((WOOD,ARRIS),[(131,515),(135,502),(136,479),(137,410),(129,482)]),
    (BOX,[(171,378),(182,368),(203,378)]),
    (LABEL,[(187,370)]),(SMALL_LABEL,[(169,356)]),
    ((BOX,FLANGE),[(186,389)]),(GLASS,[(90,249)]),
    (WOOD,[(85,247),(102,258),(90,280)]),
]


def check(mesh,matrix):
    eye=-np.linalg.solve(matrix[:,:3],matrix[:,3])
    scene=SerialScene(mesh)
    hits=[]
    for material,points in CLASSES:
        names=(material,) if isinstance(material,str) else material
        for pixel in points:
            ray=np.linalg.solve(matrix[:,:3],[*pixel,1])
            actual=scene.ray(eye,ray,40.)
            hits.append({'image_xy':list(pixel),'expected':list(names),'first_hit':actual,
                         'passed':bool(actual and actual['material'] in names)})
    # A separate weak edge is partly screened by the brick arch. Preserve the original
    # central ray as well as its two-pixel neighbourhood in each actual level.
    occluded=[]
    for u in range(101,106):
        ray=np.linalg.solve(matrix[:,:3],[u,250,1.])
        occluded.append({'original_pixel':[u,250],'first_hit':scene.ray(eye,ray,40.)})
    visible=[abs(row['original_pixel'][0]-103) for row in occluded
             if row['first_hit'] and row['first_hit']['material']==WOOD]
    return {'mesh':scene.asset,'samples':len(hits),'passed':sum(hit['passed'] for hit in hits),'first_hits':hits,
            'faint_upper_frame_edge':{'approximate_source_pixel':[103,250],'neighbourhood':occluded,
                                     'distance_to_nearest_visible_timber_px':min(visible) if visible else None}}


if __name__=='__main__':
    output=Path(sys.argv[1])
    camera=json.loads((HERE/'press-entrance-camera.json').read_bytes())
    matrix=np.asarray(camera['press'])
    results=[check(Path(name),matrix) for name in sys.argv[2:]]
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'source':camera['image'],'models':results},ensure_ascii=False,
                                separators=(',',':'))+'\n')
    for result in results:
        print(result['mesh']['file'],result['passed'],result['samples'])
        for hit in result['first_hits']:
            if not hit['passed']:print(hit)
    sys.exit(any(r['passed']!=r['samples'] for r in results))
