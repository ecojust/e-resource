"""Prepare the actual editable components and verify their geometry and UVs in a second Blender."""
import argparse,importlib.util,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
SPEC=importlib.util.spec_from_file_location('architectural_blender',PROJECT/'source/precise/putuo-nanlin-normal-school-brick-villa/source/build_blender_source.py')
engine=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(engine)
ID='yangpu-yangshupu-fire-brigade-historic-tower-crown'
engine.SOURCE=HERE;engine.ID=ID;engine.UV_NAME='Tower mineral and sheet surfaces';engine.PHOTO_URL='https://m.thepaper.cn/newsDetail_forward_19513921'
engine.LEGAL='Original model of the historic open pavilion. Yangpu District archival photo from Yang Tu, exposure date unrecorded; Fayhoo, 6 April 2015, period comparison. No source photo is embedded.'
engine.__file__=__file__
def collection(name):
    if name.startswith('front '):return '正面圆眼与线框'
    if name.startswith('return '):return '折侧圆眼与线框'
    if 'lantern' in name or 'pavilion' in name or 'cap' in name:return '敞亭、栏柱与亭帽'
    return '方塔挑檐与截面'
def prepare(raw,out):
    sys.path.insert(0,str(HERE))
    from build_model import build,META
    b=build(False);rebuilt=out/'regenerated.glb';b.save(rebuilt,META)
    assert engine.sha(raw)==engine.sha(rebuilt)
    doc,_=engine.read_gltf(raw);parts=[]
    for part in b.parts:
        v=np.asarray(part['vertices'],dtype='<f4');t=np.asarray(part['triangles'],dtype=int)
        xyz,ix=np.unique(v,axis=0,return_inverse=True);label=part['label']
        entry={'name':label,'label':label,'collection':collection(label),'material':part['material'],'v':xyz.tolist(),'t':ix[t].tolist()}
        if 'texcoords' in part:
            uv=np.asarray(part['texcoords'],dtype='<f4')[t];uv[:,:,1]=(1.-uv[:,:,1].astype(np.float64)).astype(np.float32)
            entry['corner_uv']=uv.reshape(-1,2).tolist()
        parts.append(entry)
    assert len(set(x['name']for x in parts))==len(parts)
    palette={m['name']:m['pbrMetallicRoughness']for m in doc['materials']}
    data={'id':ID,'source':META,'copyright':META['copyright'],'raw_sha256':engine.sha(raw),'parts':parts,'materials':palette,
          'textures':engine.raw_textures(raw),'cameras':json.loads((HERE/'cameras.json').read_bytes()),'layout_sha256':engine.sha(HERE.parent/'measurements/historical-crown-camera.json')}
    engine.write(out/'editable-parts.json',data)
    engine.write(out/'editable-inputs.json',{'raw_sha256':engine.sha(raw),'signed_parts':engine.sha(out/'editable-parts.json'),'components':len(parts)})
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=('prepare','run','make','verify'));p.add_argument('raw',type=Path);p.add_argument('out',type=Path);p.add_argument('--project',type=Path,default=PROJECT)
    argv=sys.argv[sys.argv.index('--')+1:]if '--' in sys.argv else sys.argv[1:];a=p.parse_args(argv)
    raw=a.raw.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    if a.stage=='prepare':prepare(raw,out)
    elif a.stage=='run':engine.run(raw,out,PROJECT)
    elif a.stage=='make':engine.blender_make(out)
    else:engine.blender_verify(raw,out,PROJECT)
