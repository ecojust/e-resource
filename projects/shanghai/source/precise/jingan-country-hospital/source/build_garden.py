"""Build the garden facade study. See README.md for command and scope."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

SOURCE = Path(__file__).resolve().parent
COMMON = SOURCE.parents[1] / 'hongkou-general-post-office/source/common'
sys.path.insert(0, str(COMMON))
sys.path.insert(0, str(COMMON.parent))
from package_assets import metadata as retain_glb_metadata
from photo_architecture import Builder
from portico import add_center, PALETTE
from check_meshes import check_pair


def assembled(with_wings, lod, scale, bearing):
    builder = Builder(PALETTE)
    add_center(builder, lod)
    if with_wings:
        from garden_wings import add_wings
        add_wings(builder, lod)
    c, s = math.cos(bearing), math.sin(bearing)
    for part in builder.parts:
        part['vertices'] = [(scale*(c*x+s*y), scale*(-s*x+c*y), scale*z)
                            for x, y, z in part['vertices']]
    return builder


def glb_stats(path):
    with path.open('rb') as stream:
        magic, version, length, json_length, kind = struct.unpack('<4sIIII',stream.read(20))
        assert (magic,version,length,kind) == (b'glTF',2,path.stat().st_size,0x4e4f534a)
        doc=json.loads(stream.read(json_length))
    primitives=[p for mesh in doc['meshes'] for p in mesh['primitives']]
    positions=[doc['accessors'][p['attributes']['POSITION']] for p in primitives]
    return {'triangles':sum(doc['accessors'][p['indices']]['count']//3 for p in primitives),
            'bounds_gltf_m': [[fn(a[key][i] for a in positions) for i in range(3)]
                              for key, fn in [('min',min),('max',max)]],
            'materials':len(doc['materials'])}


def group_parts(builder):
    """Preserve separate editable architectural components and material slots in Blender."""
    groups=defaultdict(lambda: {'v':[],'f':[],'materials':[],'face_materials':[]})
    for part in builder.parts:
        target=groups[part['label']]
        index=len(target['v'])
        target['v'].extend(part['vertices'])
        target['f'].extend([[i+index for i in tri] for tri in part['triangles']])
        mat=part['material']
        if mat not in target['materials']:
            target['materials'].append(mat)
        target['face_materials'].extend([target['materials'].index(mat)]*len(part['triangles']))
    return groups


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-wings',action='store_true',help='Include the documented lateral garden frontage')
    parser.add_argument('--out',type=Path,default=SOURCE.parent/'development')
    parser.add_argument('--parameters',type=Path,default=SOURCE/'parameters.json')
    parser.add_argument('--audit',type=Path,help='Directory for preview and verification evidence')
    parser.add_argument('--decoded',type=Path,help='Keep decoded meshes for independent checks')
    parser.add_argument('--oidn',default='oidnDenoise',help='Open Image Denoise command-line tool')
    parser.add_argument('--blender',default='blender')
    parser.add_argument('--gltfpack',default='gltfpack')
    args=parser.parse_args()
    out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    audit=(args.audit or out).resolve()
    audit.mkdir(parents=True,exist_ok=True)
    params=json.loads(args.parameters.read_text())
    scale=float(params['portico_width_m'])/25
    bearing=math.radians(params['author_axis_bearing_degrees'])
    if not math.isfinite(scale) or scale<=0 or not math.isfinite(bearing):
        parser.error('width must be positive and bearing finite')
    model_id='jingan-country-hospital'
    prefix=model_id+('-garden-front' if args.with_wings else '-central-portico')
    scope=('Garden frontage, including a 1926-informed arrangement of lateral loggias and bays; '
           if args.with_wings else 'Central five-bay portico of the garden facade; ')
    scope+='exterior relief study, excluding unseen building mass, complete roof and interiors.'
    title='宏恩医院历史主楼花园立面（三处山花与两段拱廊窗墙）' if args.with_wings else '宏恩医院历史主楼花园立面中央门廊'
    meta={'id':model_id,'name':title,'scope':scope,'portico_width_m':params['portico_width_m'],
          'copyright':'Original geometric study: MIT; no photographic pixels embedded.'}
    raw=out/(prefix+'-raw.glb')
    native=out/(prefix+'.blend')
    web=out/(prefix+'-web.glb')
    far=out/(prefix+'-lod.glb')
    with tempfile.TemporaryDirectory() as directory:
        temp=Path(directory)
        full=assembled(args.with_wings,False,scale,bearing)
        full.save(temp/'raw.glb',meta)
        shutil.copyfile(temp/'raw.glb',raw)
        (temp/'parts.json').write_text(json.dumps({'groups':group_parts(full),'palette':full.palette,'metadata':meta},separators=(',',':')))
        low=assembled(args.with_wings,True,scale,bearing)
        low.save(temp/'low.glb',meta)
        decoded=(args.decoded or temp).resolve()
        decoded.mkdir(parents=True,exist_ok=True)
        checks={}
        for role,src,dest in [('full',raw,web),('lod',temp/'low.glb',far)]:
            subprocess.run([args.gltfpack,'-i',str(src),'-o',str(dest),'-cc','-noq','-vnf','-kn','-km','-ke'],check=True)
            retain_glb_metadata(dest,src)
            checks[role]=check_pair(src,dest,decoded/(role+'.glb'))
            assert glb_stats(src)['triangles']==glb_stats(dest)['triangles']
        preview=audit/(prefix+'-preview.png')
        unfiltered=temp/preview.name
        subprocess.run([args.blender,'-b','--threads','2','--python-exit-code','1','--python',str(SOURCE/'make_native.py'),
                        '--',str(temp/'parts.json'),str(native),str(unfiltered)],check=True)
        # Preserve the native camera image. OIDN filters only Monte Carlo sampling noise.
        subprocess.run(['magick',str(unfiltered),'-colorspace','sRGB','-endian','LSB',str(temp/'render.pfm')],check=True)
        subprocess.run([args.oidn,'-d','cpu','--threads','2','--ldr',str(temp/'render.pfm'),'--srgb','-o',str(temp/'clean.pfm')],check=True)
        subprocess.run(['magick',str(temp/'clean.pfm'),'-set','colorspace','sRGB','-depth','8',str(preview)],check=True)
        native_render_sha=hashlib.sha256(unfiltered.read_bytes()).hexdigest()
    assets={}
    for key,path in [('raw',raw),('full',web),('lod',far),('native',native)]:
        content=path.read_bytes()
        assert 0<len(content)<100_000_000
        assets[key]={'file':path.name,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()}
        if path.suffix=='.glb':
            assets[key].update(glb_stats(path))
    assert assets['lod']['triangles']<assets['full']['triangles']
    scope_zh='历史主楼朝花园的三处山花门廊与两段退进窗墙、十开间底层拱廊。后部主楼、完整屋面、内部和院区独立建筑待核。' if args.with_wings else '朝向花园的中央五开间门廊。'
    report={**meta,'model_id':model_id,'status':'original-photo-informed-exterior',
            'viewer_page':'country-hospital.html','model_scope_zh':scope_zh,'estimated':scope_zh,
            'assets':assets,'includes_wings':args.with_wings,'parameters':params,
            'coordinate_convention':'Local GLB [facade-right, up, garden-outward], metres; placement supplies geographic rotation.',
            'geometry_license':'MIT','photos_embedded':False,'third_party_models_embedded':False,
            'all_dimensions_estimated':True,'interiors_modeled':False,
            'source_register':'source/precise/jingan-country-hospital/reference-review.json'}
    evidence={'id':model_id,'asset_sha256':{k:v['sha256'] for k,v in assets.items()},
              'native_editable_meshes':len(group_parts(full)),'native_reopened':True,
              'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in [Path(__file__), SOURCE/'make_native.py', SOURCE/'check_meshes.py',
                                         SOURCE/'parameters.json', SOURCE/'portico.py',
                                         *([SOURCE/'garden_wings.py'] if args.with_wings else []),
                                         COMMON/'photo_architecture.py', COMMON.parent/'package_assets.py']},
              'tool_versions':{'blender':subprocess.check_output([args.blender,'--version'],text=True).splitlines()[0],
                               'gltfpack':subprocess.run([args.gltfpack,'-v'],capture_output=True,text=True).stderr.strip() or 'See source/README.md',
                               'oidn':subprocess.check_output([args.oidn,'--ld'],text=True).splitlines()[0]},
              'render':'48 samples, Cycles CPU; rendered from reopened blend, then OIDN RT sRGB. No photo textures.',
              'preview':preview.name,'unfiltered_render_sha256':native_render_sha,
              'preview_sha256':hashlib.sha256(preview.read_bytes()).hexdigest(),
              'full_and_lod_oriented_triangles_equal_precompression':True,
              'oriented_triangle_digest_by_material':checks}
    (audit/'geometry-native.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+'\n')
    (out/'manifest.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(assets))

if __name__=='__main__':
    main()
