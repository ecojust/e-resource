#!/usr/bin/env python3
"""Rebuild the single v6 street prop from the SHA-frozen published first3 mesh plus bounded 07/09 additions.

The immutable baseline is an explicit source dependency, not an inferred Blender
file. --output builds without installation; otherwise validate all outputs before
atomically replacing each installed asset/metadata file. No network or Blender.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
MAPPING = {
    'bund-streets.glb': ['assets/models/bund/bund-streets.glb', 'source/bund/street/bund-streets.glb'],
    'bund-streets-web.glb': ['assets/models/bund/web/bund-streets.glb', 'source/bund/street/bund-streets-web.glb'],
    'street-interaction-v5.json': ['data/bund/street-interaction-v5.json'],
    'bund-streets-metadata.candidate.json': ['data/bund/models/bund-streets.json', 'source/bund/street/bund-streets.json'],
    'bund-streets-web-metadata.candidate.json': ['data/bund/models/bund-streets-web.json'],
    'scene-props.candidate.json': ['data/scene-props.json'],
    'street-frontage-audit.json': ['data/bund/validation/street-frontage-0709-v6.json'],
    'raw-prefix-validation.json': ['data/bund/validation/street-frontage-0709-v6-raw-prefix.json'],
    'street-frontage-check.geojson': ['source/bund/street/frontage-0709-v6/street-frontage-check.geojson'],
    'exclusions.geojson': ['source/bund/street/frontage-0709-v6/exclusions.geojson'],
    'support-probes.json': ['source/bund/street/frontage-0709-v6/support-probes.json'],
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def raw_bin(path):
    data=Path(path).read_bytes()
    magic,version,length=struct.unpack_from('<4sII',data)
    assert magic==b'glTF' and version==2 and length==len(data)
    n,kind=struct.unpack_from('<II',data,12)
    assert kind==0x4e4f534a
    count,kind=struct.unpack_from('<II',data,20+n)
    assert kind==0x004e4942
    return json.loads(data[20:20+n]), data[28+n:28+n+count]


def validate(output, project):
    source=project/'source/bund/street/frontage-0709-v6/inputs'
    for entry in read(source/'source-manifest.json')['files']:
        path=(source/entry['file']).resolve()
        assert path.is_relative_to(source.resolve()) and path.stat().st_size==entry['bytes'] and sha(path)==entry['sha256'], entry['file']
    props=read(output/'scene-props.candidate.json')
    assert len(props)==1 and props[0]['id']=='bund-streets', 'The street remains a single prop'
    record=props[0]
    for name,key in [('bund-streets.glb','raw'),('bund-streets-web.glb','web'),('street-interaction-v5.json','interaction')]:
        path=output/name
        assert sha(path)==record[key+'_sha256'] and path.stat().st_size==record[key+'_bytes'], name
    assert record['sha256']==record['web_sha256'] and record['bytes']==record['web_bytes']
    before,old_buffer=raw_bin(source/'assets/models/bund/bund-streets.glb')
    after,new_buffer=raw_bin(output/'bund-streets.glb')
    assert new_buffer[:len(old_buffer)]==old_buffer, 'Existing binary geometry changed'
    for key in ('materials','nodes','scenes'):
        assert before[key]==after[key], 'Existing '+key+' changed'
    for key in ('accessors','bufferViews'):
        assert before[key]==after[key][:len(before[key])], key
    primitives=before['meshes'][0]['primitives']
    assert after['meshes'][0]['primitives'][:len(primitives)]==primitives
    old=read(source/'data/bund/street-interaction-v5.json');new=read(output/'street-interaction-v5.json')
    assert new['features'][:len(old['features'])]==old['features'] and new['local_obstacles']==old['local_obstacles']
    assert len(new['features'])==len(old['features'])+2
    assert new['raw_model_sha256']==record['raw_sha256'] and new['web_model_sha256']==record['web_sha256']
    audit=read(output/'street-frontage-audit.json')
    assert audit['passed'] and audit['raw_after_sha256']==record['raw_sha256'] and audit['web_after_sha256']==record['web_sha256']
    prefix={'schema':'street-frontage-raw-prefix-v1','passed':True,
        'existing_binary_prefix_bytes':len(old_buffer),'existing_materials':len(before['materials']),
        'existing_primitives':len(primitives),'new_primitives':len(after['meshes'][0]['primitives'])-len(primitives),
        'all_old_accessors_and_views_equal':True,'all_old_nodes_and_scenes_equal':True,
        'all_old_buffer_bytes_equal':True,'sidecar_old_features_equal':True,
        'sidecar_old_obstacles_equal':True,'sidecar_old_feature_count':len(old['features']),
        'sidecar_old_obstacle_count':len(old['local_obstacles']),
        'added_ground_surfaces':len(new['features'])-len(old['features'])}
    (output/'raw-prefix-validation.json').write_text(json.dumps(prefix,ensure_ascii=False,indent=2)+'\n')
    for name in MAPPING:
        assert 0<(output/name).stat().st_size<100_000_000, name
    assert read(output/'bund-streets-web-metadata.candidate.json')==record
    metadata=read(output/'bund-streets-metadata.candidate.json')
    assert metadata['sha256']==record['raw_sha256'] and metadata['triangles']==record['triangles']
    return record


def install(output, project):
    """Called only with validated complete output; every file replacement is atomic."""
    record=validate(output,project)
    current=read(project/'data/scene-props.json')
    assert len(current)==1 and current[0]['id']=='bund-streets', 'Unexpected scene-prop schema; review before installation'
    for name, destinations in MAPPING.items():
        for relative in destinations:
            destination=project/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            fd,temporary=tempfile.mkstemp(prefix='.'+destination.name+'.',dir=destination.parent)
            try:
                with os.fdopen(fd,'wb') as stream, (output/name).open('rb') as original:
                    shutil.copyfileobj(original,stream)
                os.replace(temporary,destination)
            finally:
                if os.path.exists(temporary):os.unlink(temporary)
    return record


def build(project, output, gltfpack):
    source=project/'source/bund/street/frontage-0709-v6'
    subprocess.run([sys.executable,str(source/'append_frontage.py'),'--inputs',str(source/'inputs'),
        '--output',str(output),'--ids','bund07','bund09','--gltfpack',gltfpack],check=True)
    return validate(output,project)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,default=PROJECT)
    parser.add_argument('--gltfpack',required=True)
    parser.add_argument('--output',type=Path,help='Fresh output directory: rebuild and validate without replacing project assets')
    args=parser.parse_args();project=args.project.resolve()
    if args.output:
        output=args.output.resolve()
        record=build(project,output,args.gltfpack)
    else:
        with tempfile.TemporaryDirectory(prefix='shanghai-street-v6-') as temporary:
            output=Path(temporary)/'output'
            build(project,output,args.gltfpack)
            record=install(output,project)
    print(json.dumps({'passed':True,'installed':not bool(args.output),'raw_sha256':record['raw_sha256'],
        'web_sha256':record['web_sha256'],'triangles':record['triangles']},ensure_ascii=False))


if __name__=='__main__':
    main()
