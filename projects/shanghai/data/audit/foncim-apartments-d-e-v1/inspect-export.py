"""Render both buildings and their courtyard from seven source-registered positions."""
import argparse,hashlib,json,runpy
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/xuhui-foncim-apartments-d-e/source'
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    cams=SOURCE/'cameras.json';rows=json.loads(cams.read_bytes())
    engine=runpy.run_path(HERE.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py')
    report=engine['render'](a.mesh,a.output,[(v['name'],v['eye'],v['target'],v['width_m'])for v in rows],rows[0]['width'],rows[0]['height'])
    assert report['embedded_textures'][0]['embedded_sha256']==hashlib.sha256((SOURCE/'chestnut-ochre-courses.png').read_bytes()).hexdigest()
    prominent={'both-blocks':['D dark grey flat roof','E weathered flat roof','Court golden cement fascia'],
               'street-elevation':['Chestnut and warm ochre horizontal render','D buff cement','D desaturated window glass'],
               'splayed-balconies':['D dark terrace rail','D buff cement','D shaded glazing','D ochre louvres'],
               'south-court':['E warm buff cement','E smoked stair lights','Court russet round columns'],
               'garden-elevation':['D buff cement','D desaturated window glass','Court russet round columns'],
               'covered-walk':['Court grey paving','Court ivory soffit','Court russet round columns'],
               'roof-plan':['D grey stone flags','D fine terrazzo','E weathered flat roof','Court golden cement fascia']}
    prominent['roof-plan'][0]='Court grey stone flags'
    report['registered_materials']={}
    for v in report['views']:
        name=v['view'];counts=v['material_pixels'];test={m:counts.get(m,0)for m in prominent[name]}
        assert min(test.values())>24,(name,test)
        report['registered_materials'][name]=test
    report['camera_source_sha256']=hashlib.sha256(cams.read_bytes()).hexdigest()
    (a.output/'views.json').write_text(json.dumps(report,indent=2)+'\n')
