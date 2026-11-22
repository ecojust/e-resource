"""Render the 1914 kitchen block, two streets, courtyard, roof and stone cartouche from eight fixed positions."""
import argparse,hashlib,json,runpy
from pathlib import Path

HERE=Path(__file__).absolute().parent
SOURCE=HERE.parents[2]/'source/precise/hongkou-general-hospital-1914-kitchen-block/source'
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    cams=SOURCE/'cameras.json';rows=json.loads(cams.read_bytes())
    renderer=runpy.run_path(HERE.parent/'yimin-food-factory-former-canteen-v1/render-with-stone-mips.py')
    report=renderer['render'](a.mesh,a.output,[(v['name'],v['eye'],v['target'],v['width_m']) for v in rows],rows[0]['width'],rows[0]['height'])
    runpy.run_path(HERE.parent/'yimin-food-factory-former-canteen-v1/sunlight.py')['cast_shadows'](a.mesh,a.output,report)
    assert {v['embedded_sha256']for v in report['embedded_textures']}=={hashlib.sha256((SOURCE/f).read_bytes()).hexdigest()for f in __import__('json').loads((SOURCE/'material-sources.json').read_bytes())}
    report['camera_source_sha256']=hashlib.sha256(cams.read_bytes()).hexdigest()
    (a.output/'views.json').write_text(json.dumps(report,indent=2)+'\n')
