"""Render the Young Allen Court octagonal tower, roof dormers and street windows."""
import argparse,hashlib,json,runpy
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/hongkou-young-allen-court-gilded-corner/source'
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    cams=SOURCE/'cameras.json';rows=json.loads(cams.read_bytes())
    renderer=runpy.run_path(HERE.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py')
    report=renderer['render'](a.mesh,a.output,[(v['name'],v['eye'],v['target'],v['width_m']) for v in rows],rows[0]['width'],rows[0]['height'])
    assert report['embedded_textures'][0]['embedded_sha256']==hashlib.sha256((SOURCE/'young-allen-grey-brick.png').read_bytes()).hexdigest()
    report['camera_source_sha256']=hashlib.sha256(cams.read_bytes()).hexdigest()
    (a.output/'views.json').write_text(json.dumps(report,indent=2)+'\n')
