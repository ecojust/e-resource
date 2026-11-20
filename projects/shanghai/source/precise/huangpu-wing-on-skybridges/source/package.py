"""Generate the raw and native model, optimize both GLBs, then verify and bind output bytes."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import struct
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
MODEL='huangpu-wing-on-skybridges'
NAME='新老永安跨浙江中路北侧封闭天桥'
SCOPE='南京东路一侧的北桥外观。北立面参照2025年5月1日照片，两列水平窗带各六跨。南向隐面、桥深、桥底及两端接头按资料估计。后方另一座桥及商场室内另行核查。'


def inspect(path):
    data=path.read_bytes()
    assert 0<len(data)<100_000_000
    record={'file':path.name,'bytes':len(data),'sha256':sha256(data).hexdigest()}
    if path.suffix=='.glb':
        magic,vers,length,jlength,kind=struct.unpack_from('<4sIIII',data)
        assert (magic,vers,length,kind)==(b'glTF',2,len(data),0x4e4f534a)
        doc=json.loads(data[20:20+jlength])
        assert not doc.get('images') and not any(x in doc.get('extensionsRequired',[]) for x in ('KHR_mesh_quantization','EXT_meshopt_compression'))
        triangles=0
        for node in doc['nodes']:
            if 'mesh' in node:
                for primitive in doc['meshes'][node['mesh']]['primitives']:
                    assert doc['accessors'][primitive['attributes']['POSITION']]['componentType']==5126
                    triangles+=doc['accessors'][primitive['indices']]['count']//3
        record['triangles']=triangles
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets',type=Path,required=True)
    parser.add_argument('--audit',type=Path,required=True)
    parser.add_argument('--gltfpack',default='gltfpack')
    parser.add_argument('--blender',default='blender')
    args=parser.parse_args()
    out=args.assets.resolve()
    audit=args.audit.resolve()
    dims=json.loads((SOURCE/'dimensions.json').read_text())
    with tempfile.TemporaryDirectory() as directory:
        tmp=Path(directory)
        for lod,dest in [(False,out),(True,tmp)]:
            command=[args.blender,'-b','-t','4','--python-exit-code','1','--python',str(SOURCE/'build_bridge.py'),'--',
                     '--assets',str(dest),'--audit',str(audit)]
            subprocess.run(command+(['--lod'] if lod else []),check=True)
        raw=out/(MODEL+'-raw.glb')
        result={'raw':inspect(raw),'native':inspect(out/(MODEL+'.blend'))}
        for key,source,suffix in [('full',raw,'-web'),('lod',tmp/(MODEL+'-lod-unpacked.glb'),'-lod')]:
            target=out/(MODEL+suffix+'.glb')
            subprocess.run([args.gltfpack,'-i',str(source),'-o',str(target),'-noq','-vnf','-km','-kn','-ke'],check=True)
            result[key]=inspect(target)
            assert result[key]['triangles']==inspect(source)['triangles']
    manifest={'id':MODEL,'model_id':MODEL,'name':NAME,'status':'original-photo-informed-overhead-connector',
              'viewer_page':'wing-on-north-skybridge.html','audit_directory':'data/audit/wing-on-skybridges-v1/',
              'model_scope_zh':SCOPE,'ground_collision_mode':'overhead-connector',
              'geometry_license':'MIT','map_reference_license':'ODbL-1.0','interiors_modeled':False,
              'photos_embedded':False,'third_party_models_embedded':False,'ground_supports_modeled':False,
              'all_dimensions_estimated':True,'selected_dimensions':dims,'source_register':'source/precise/'+MODEL+'/source-register.json',
              'assets':result}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    main()
