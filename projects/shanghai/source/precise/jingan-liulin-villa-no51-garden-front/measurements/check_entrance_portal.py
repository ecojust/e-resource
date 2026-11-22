"""从两台实测相机在原图像素发射光线，取完整GLB上最近的三角面。"""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene

SURFACE={
    'Entrance | warm pale render':'plaster','Entrance | projecting moulded cream edges':'pale',
    'Entrance | recessed walnut joinery':'wood','Entrance | polished wood beads':'wood',
    'Entrance | dark reflective glazing':'glass','Entrance | aged paired door pulls':'iron',
    'Entrance | shaded space beyond opening':'shadow','Entrance | worn grey-brown treads':'tread',
    'Entrance | darker stone risers':'riser',
}

def inspect(asset):
    evidence=HERE/'entrance-portal-observations.json'
    registration=json.loads(evidence.read_bytes())
    camera=HERE/'no51-house-cameras.json'
    assert registration['camera_sha256']==sha256(camera.read_bytes()).hexdigest()
    cameras=json.loads(camera.read_bytes())['source_poses']
    scene=SerialScene(asset)
    rows=[]
    for item in registration['observations']:
        p=np.asarray(cameras[item['camera']]['P'])
        inverse=np.linalg.inv(p[:,:3])
        hit=scene.ray(-inverse@p[:,3],inverse@[*item['pixel'],1.],60)
        mat=hit['material'] if hit else None
        observed=SURFACE.get(mat,mat)
        rows.append(dict(**item,first_material=mat,observed=observed,direct=observed==item['surface']))
    by_camera=Counter(row['camera'] for row in rows if row['direct'])
    return dict(mesh=asset.name,sha256=sha256(asset.read_bytes()).hexdigest(),registration_sha256=sha256(evidence.read_bytes()).hexdigest(),
                direct=sum(by_camera.values()),total=len(rows),by_camera=by_camera,measurements=rows)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assets',type=Path,nargs='+')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=[inspect(mesh) for mesh in args.assets]
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for item in result:print(item['mesh'],item['direct'],item['total'])
