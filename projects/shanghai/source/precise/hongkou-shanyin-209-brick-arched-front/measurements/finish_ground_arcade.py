"""Verify the three packaged levels and reproduce the registered study plate."""
from pathlib import Path
import argparse,json
from check_ground_arcade import inspect,DEFAULT_LAYOUT
from render_ground_arcade import plate
if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('package',type=Path)
    a.add_argument('photo',type=Path)
    a.add_argument('audit',type=Path)
    a.add_argument('--camera',type=Path,help='Calibrated facade camera with camera_P or ground_camera_P.')
    o=a.parse_args();cal=DEFAULT_LAYOUT
    if o.camera:
        d=json.loads(o.camera.read_bytes())
        cal={'ground_camera_P':d.get('ground_camera_P',d.get('camera_P'))}
    o.audit.mkdir(parents=True,exist_ok=True)
    for key,name in [('raw','raw.glb'),('full','decoded-full.glb'),('lod','decoded-lod.glb')]:
        result=inspect(o.package/name,cal)
        (o.audit/f'whole-{key}.json').write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
        if not result['passed']:
            for row in result['rays']:
                if not row['passed']:print(row)
            raise SystemExit(1)
        print(key,result['tests'],'passed',flush=True)
    plate(o.package/'decoded-full.glb',o.package/'decoded-lod.glb',o.photo,o.audit/'ground-arcade.jpg',cal)
