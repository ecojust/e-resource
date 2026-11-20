"""Package an architectural Builder model, compare decoded surfaces and render its editable blend."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
PREVIOUS = PROJECT/'source/precise/jingan-country-hospital/source'
POSTAL = PROJECT/'source/precise/hongkou-general-post-office/source'
sys.path.insert(0,str(PREVIOUS))
from build_garden import glb_stats, group_parts
from check_meshes import check_pair
from package_assets import metadata as retain_metadata
from photo_architecture import Builder


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def build(model_source, meta, palette, add_geometry):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--decoded', type=Path, help='Keep the independently decoded meshes')
    parser.add_argument('--blender', default='blender')
    parser.add_argument('--gltfpack', default='gltfpack')
    parser.add_argument('--oidn', default='oidnDenoise')
    args = parser.parse_args()
    out, audit = args.out.resolve(), args.audit.resolve()
    out.mkdir(parents=True, exist_ok=True)
    audit.mkdir(parents=True, exist_ok=True)
    ident = meta['id']
    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        raw = temp/(ident+'-raw.glb')
        web = temp/(ident+'-web.glb')
        lod = temp/(ident+'-lod.glb')
        native = temp/(ident+'.blend')
        preview = temp/(ident+'-preview.png')
        full = Builder(palette)
        add_geometry(full,False)
        full.save(raw,meta)
        reduced = Builder(palette)
        add_geometry(reduced,True)
        low = temp/'before-compression.glb'
        reduced.save(low,meta)
        checks = {}
        decoded = args.decoded.resolve() if args.decoded else temp
        decoded.mkdir(parents=True,exist_ok=True)
        for role,source,packed in [('full',raw,web),('lod',low,lod)]:
            subprocess.run([args.gltfpack,'-i',source,'-o',packed,'-cc','-noq','-vnf','-km','-kn','-ke'],check=True)
            retain_metadata(packed,source)
            checks[role] = check_pair(source,packed,decoded/(role+'.glb'))
        assert glb_stats(raw)['triangles'] == glb_stats(web)['triangles'] > glb_stats(lod)['triangles']
        data_file = temp/'parts.json'
        write_json(data_file,{'groups':group_parts(full),'palette':full.palette,'metadata':meta})
        blender = [args.blender,'-b','--threads','2','--python-exit-code','1','--python']
        unfiltered = temp/'render'/preview.name
        unfiltered.parent.mkdir()
        subprocess.run([*blender, PREVIOUS/'make_native.py','--',data_file,native,unfiltered],check=True)
        # Native positions/material assignments are decoded independently from Blender.
        verification = temp/'verify-native.json'
        verify = PROJECT/'tools/verify_editable_model.py'
        subprocess.run([*blender,verify,'--',native,raw,verification],check=True)
        subprocess.run(['magick',unfiltered,'-colorspace','sRGB','-endian','LSB',temp/'render.pfm'],check=True)
        denoise = subprocess.run([args.oidn,'-d','cpu','--threads','2','--ldr',temp/'render.pfm',
                                  '--srgb','-o',temp/'clean.pfm'],capture_output=True,text=True,check=True)
        subprocess.run(['magick',temp/'clean.pfm','-set','colorspace','sRGB','-depth','8',preview],check=True)
        assets = {}
        for role,path in [('raw',raw),('full',web),('lod',lod),('native',native)]:
            assert 0 < path.stat().st_size < 100_000_000
            assets[role] = {'file':path.name,'bytes':path.stat().st_size,'sha256':sha(path)}
            if path.suffix == '.glb':
                assets[role].update(glb_stats(path))
        manifest = {**meta,'model_id':ident,'assets':assets,'geometry_license':'MIT',
                    'all_dimensions_estimated':True,'photos_embedded':False,'third_party_models_embedded':False}
        inputs = [x for x in model_source.rglob('*') if x.is_file() and '__pycache__' not in x.parts]
        inputs.extend([Path(__file__).resolve(),verify,PREVIOUS/'make_native.py',PREVIOUS/'check_meshes.py',
                       PREVIOUS/'build_garden.py',POSTAL/'common/photo_architecture.py',POSTAL/'common/sign_lettering.py',
                       POSTAL/'package_assets.py',POSTAL/'decode_meshopt.mjs',PROJECT/'vendor/meshopt_decoder.module.js',
                       PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'])
        versions = subprocess.run([args.gltfpack,'-v'],capture_output=True,text=True)
        report = {'id':ident,'sha256':{k:v['sha256'] for k,v in assets.items()},'input_sha256':{
                      str(p.relative_to(PROJECT)):sha(p) for p in inputs},
                  'packaging':(versions.stdout+versions.stderr).strip(),
                  'meshopt_decoded_oriented_surfaces_match':True,'surface_sha256':checks,
                  'native_reopened_and_compared':json.loads(verification.read_text()),
                  'render':'Cycles, 48 samples, from reopened blend. OIDN RT sRGB postfilter.',
                  'oidn_device':next(line.strip() for line in denoise.stdout.splitlines() if 'version=' in line),
                  'render_unfiltered_sha256':sha(unfiltered),'preview':preview.name,'preview_sha256':sha(preview)}
        # Publish only after both mesh variants and the editable file have passed.
        for path in (raw,web,lod,native):
            shutil.copy2(path,out/path.name)
        shutil.copy2(preview,audit/preview.name)
        write_json(audit/'geometry-native.json',report)
        write_json(out/'manifest.json',manifest)
        print(json.dumps(assets))
