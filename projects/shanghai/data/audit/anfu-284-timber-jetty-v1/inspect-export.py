"""Render the exposed timber, bracket, gable verge and paired window lights from the actual decoded geometry."""
from pathlib import Path
import argparse,hashlib,json,runpy
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/xuhui-anfu-284-timber-jetty/source'
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();cameras=SOURCE/'cameras.json';rows=json.loads(cameras.read_bytes())
    method=HERE.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py'
    report=runpy.run_path(method)['render'](args.mesh,args.output,[(r['name'],r['eye'],r['target'],r['width_m'])for r in rows],750,830)
    assert len(report['views'])==7 and report['embedded_textures'][0]['embedded_sha256']==hashlib.sha256((SOURCE/'washed-pebbles.png').read_bytes()).hexdigest()
    for r in report['views']:
        mat=r['material_pixels']
        if r['view'] in ('timber-frame','upper-panel','east-elevation'):
            assert mat.get('Oxide red rails',0)>250 and mat.get('Dark washed pebble aggregate',0)>500,r['view']
        if r['view'] == 'under-jetty':
            assert mat.get('Oxide red rails',0)>250 and mat.get('Dark timber end grain',0)>180,r['view']
        if r['view'] == 'red-verge':
            assert mat.get('Rough red tile',0)>150,r['view']
        if r['view'] == 'paired-sashes':
            assert mat.get('Red brown sash frames',0)>150 and mat.get('Grey green glass',0)>150,r['view']
    report['camera_source_sha256']=hashlib.sha256(cameras.read_bytes()).hexdigest()
    (args.output/'views.json').write_text(json.dumps(report,indent=2)+'\n')
