"""Verify both originals, repeating samplers, and every oriented textured triangle after decompression."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
from contextlib import ExitStack

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'source'
PRECISE=HERE.parent.parent
Model=runpy.run_path(str(PRECISE/'changning-hengchang-li-yuyuan-road-gatehouse/measurements/check_render_uv.py'))['Model']

def compare(role, geometry, packaged):
    source=geometry/(role+'-source.glb')
    decoded=packaged/('decoded-'+role+'.glb')
    web_name='web' if role=='full' else 'lod'
    web=next(packaged.glob('*-'+web_name+'.glb'))
    paths=[source,decoded,web]
    with ExitStack() as stack:
        models=[Model(p) for p in paths]
        for model in models:
            stack.callback(model.data.close)
        textures=[model.textures(SOURCE) for model in models]
        assert len(textures[0])==2 and textures[0]==textures[1]==textures[2]
        surfaces=[model.surfaces(SOURCE) for model in models[:2]]
        assert surfaces[0]==surfaces[1]
    return dict(files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                images=textures[0],material_surfaces=surfaces[0])

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['geometry','packaged','report']:
        parser.add_argument(name,type=Path)
    o=parser.parse_args()
    result={role:compare(role,o.geometry,o.packaged) for role in ['full','lod']}
    o.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
