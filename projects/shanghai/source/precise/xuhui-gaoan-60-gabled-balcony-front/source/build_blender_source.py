"""Prepare the actual editable components and verify their geometry and UVs in a second Blender."""
import argparse,importlib.util,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
SPEC=importlib.util.spec_from_file_location('architectural_blender',PROJECT/'source/precise/putuo-nanlin-normal-school-brick-villa/source/build_blender_source.py')
engine=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(engine)
ID='xuhui-gaoan-60-gabled-balcony-front'
engine.SOURCE=HERE;engine.ID=ID;engine.UV_NAME='Rendered masonry and red brick grain';engine.PHOTO_URL='https://4travel.jp/travelogue/11116030'
engine.LEGAL='Original reconstruction with generated aggregate and facing-brick textures. Photo references by Gao Can 88 (2015) and 中国の風景 (2016).'
engine.__file__=__file__
def collection(label):
    return {'Gable':'中央山花、钢窗与饰额','Gallery':'阴影廊、第五层与陶瓦檐带','Balcony':'六组圆角敞廊与镂空栏板'}[label.split(' | ')[0]]
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
          'textures':engine.raw_textures(raw),'cameras':json.loads((HERE/'cameras.json').read_bytes()),'layout_sha256':engine.sha(HERE.parent/'measurements/facade-registration.json')}
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
